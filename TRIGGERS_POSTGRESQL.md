# Triggers de PostgreSQL en el Sistema GQC

## 📋 Resumen

Este documento describe los triggers de PostgreSQL implementados en el módulo de compras para automatizar la actualización de totales y stock de productos.

## 🔧 Triggers Implementados

### 1. **Trigger de Actualización de Total de Compra**

**Función:** `actualizar_total_compra()`

**Eventos que activan:**
- `INSERT` en `compras_detallecompra`
- `UPDATE` en `compras_detallecompra`
- `DELETE` en `compras_detallecompra`

**Funcionalidad:**
- Recalcula automáticamente el total de la compra sumando todos los subtotales de los detalles
- Se ejecuta después de cualquier cambio en los detalles de compra

**Código SQL:**
```sql
CREATE OR REPLACE FUNCTION actualizar_total_compra()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE compras_compra 
    SET total = (
        SELECT COALESCE(SUM(cantidad * precio_unitario), 0)
        FROM compras_detallecompra 
        WHERE compra_id = COALESCE(NEW.compra_id, OLD.compra_id)
    )
    WHERE id = COALESCE(NEW.compra_id, OLD.compra_id);
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;
```

### 2. **Trigger de Actualización de Stock (INSERT)**

**Función:** `actualizar_stock_producto()`

**Evento que activa:**
- `INSERT` en `compras_detallecompra`

**Funcionalidad:**
- Aumenta automáticamente el stock del producto cuando se registra una compra
- Se ejecuta después de insertar un nuevo detalle de compra

**Código SQL:**
```sql
CREATE OR REPLACE FUNCTION actualizar_stock_producto()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventario_producto 
    SET stock = stock + NEW.cantidad
    WHERE id = NEW.producto_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 3. **Trigger de Actualización de Stock (UPDATE)**

**Función:** `actualizar_stock_producto_modificacion()`

**Evento que activa:**
- `UPDATE` en `compras_detallecompra`

**Funcionalidad:**
- Recalcula el stock cuando se modifica la cantidad de un detalle de compra
- Resta la cantidad anterior y suma la nueva cantidad

**Código SQL:**
```sql
CREATE OR REPLACE FUNCTION actualizar_stock_producto_modificacion()
RETURNS TRIGGER AS $$
BEGIN
    -- Revertir el stock anterior
    UPDATE inventario_producto 
    SET stock = stock - OLD.cantidad
    WHERE id = OLD.producto_id;
    
    -- Aplicar la nueva cantidad
    UPDATE inventario_producto 
    SET stock = stock + NEW.cantidad
    WHERE id = NEW.producto_id;
    
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;
```

### 4. **Trigger de Reversión de Stock (DELETE)**

**Función:** `revertir_stock_producto()`

**Evento que activa:**
- `DELETE` en `compras_detallecompra`

**Funcionalidad:**
- Reduce automáticamente el stock del producto cuando se elimina un detalle de compra
- Se ejecuta después de eliminar un detalle

**Código SQL:**
```sql
CREATE OR REPLACE FUNCTION revertir_stock_producto()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE inventario_producto 
    SET stock = stock - OLD.cantidad
    WHERE id = OLD.producto_id;
    
    RETURN OLD;
END;
$$ LANGUAGE plpgsql;
```

## 🚀 Ventajas de los Triggers

1. **Consistencia de Datos:** Los totales y stock se mantienen siempre actualizados
2. **Automatización:** No es necesario manejar manualmente las actualizaciones
3. **Integridad:** Previene errores de cálculo en el código de aplicación
4. **Rendimiento:** Los cálculos se realizan a nivel de base de datos
5. **Mantenibilidad:** La lógica está centralizada en la base de datos

## 🧪 Pruebas

Para probar que los triggers funcionan correctamente, ejecuta:

```bash
python test_triggers.py
```

Este script creará datos de prueba y verificará que:
- Los totales se calculen correctamente
- El stock se actualice automáticamente
- Las modificaciones y eliminaciones funcionen correctamente

## 📁 Archivos Relacionados

- `compras/migrations/0010_create_triggers.py` - Migración que crea los triggers
- `compras/views.py` - Vistas simplificadas (sin lógica manual de actualización)
- `test_triggers.py` - Script de pruebas
- `compras/models.py` - Modelos (sin lógica de actualización en save())

## 🔄 Migración desde SQLite

Si migras desde SQLite a PostgreSQL:

1. Instalar `psycopg2-binary`
2. Configurar la base de datos PostgreSQL en `settings.py`
3. Ejecutar `python manage.py migrate`
4. Los triggers se crearán automáticamente

## ⚠️ Consideraciones

- Los triggers solo funcionan en PostgreSQL
- Para SQLite, se pueden usar Django Signals como alternativa
- Los triggers se ejecutan en transacciones, por lo que son seguros
- Si necesitas deshabilitar temporalmente los triggers, puedes usar `SET session_replication_role = replica;`

## 🛠️ Mantenimiento

Para ver los triggers existentes:
```sql
SELECT trigger_name, event_manipulation, event_object_table 
FROM information_schema.triggers 
WHERE trigger_schema = 'public';
```

Para eliminar un trigger específico:
```sql
DROP TRIGGER IF EXISTS nombre_del_trigger ON tabla;
``` 