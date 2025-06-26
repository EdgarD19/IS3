#!/usr/bin/env python
"""
Script de prueba para verificar que los triggers de PostgreSQL funcionan correctamente
"""
import os
import sys
import django

# Configurar Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'gqc_system.settings')
django.setup()

from django.db import connection
from compras.models import Compra, DetalleCompra
from inventario.models import Producto
from proveedores.models import Proveedor
from decimal import Decimal

def test_triggers():
    """Prueba los triggers de PostgreSQL"""
    print("🧪 Probando triggers de PostgreSQL...")
    
    try:
        # 1. Crear datos de prueba
        print("\n1. Creando datos de prueba...")
        
        # Crear proveedor
        proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            ruc="12345678",
            telefono="098123456",
            email="test@proveedor.com"
        )
        
        # Crear producto
        producto = Producto.objects.create(
            nombre="Producto Test",
            descripcion="Producto para pruebas",
            stock=0,
            unidad_medida="unidad"
        )
        
        print(f"   ✅ Proveedor creado: {proveedor.nombre}")
        print(f"   ✅ Producto creado: {producto.nombre} (stock inicial: {producto.stock})")
        
        # 2. Crear compra
        print("\n2. Creando compra...")
        compra = Compra.objects.create(
            proveedor=proveedor,
            fecha="2025-01-16",
            moneda="Guaraní",
            total=0,  # Los triggers actualizarán esto
            modalidad="CO"
        )
        print(f"   ✅ Compra creada: #{compra.numero}")
        print(f"   📊 Total inicial: {compra.total}")
        
        # 3. Agregar detalle (debería activar triggers)
        print("\n3. Agregando detalle de compra...")
        detalle = DetalleCompra.objects.create(
            compra=compra,
            producto=producto,
            cantidad=10,
            precio_unitario=Decimal('50000.00')
        )
        print(f"   ✅ Detalle creado: {detalle.cantidad} x {detalle.precio_unitario}")
        print(f"   📊 Subtotal esperado: {detalle.subtotal}")
        
        # 4. Verificar que los triggers funcionaron
        print("\n4. Verificando triggers...")
        
        # Recargar objetos desde la base de datos
        compra.refresh_from_db()
        producto.refresh_from_db()
        
        print(f"   📊 Total de compra actualizado: {compra.total}")
        print(f"   📦 Stock del producto actualizado: {producto.stock}")
        
        # Verificar cálculos
        total_esperado = Decimal('500000.00')  # 10 * 50000
        stock_esperado = 10
        
        if compra.total == total_esperado:
            print("   ✅ Trigger de total funcionando correctamente")
        else:
            print(f"   ❌ Error en trigger de total: esperado {total_esperado}, obtenido {compra.total}")
        
        if producto.stock == stock_esperado:
            print("   ✅ Trigger de stock funcionando correctamente")
        else:
            print(f"   ❌ Error en trigger de stock: esperado {stock_esperado}, obtenido {producto.stock}")
        
        # 5. Probar actualización de detalle
        print("\n5. Probando actualización de detalle...")
        detalle.cantidad = 15
        detalle.save()
        
        compra.refresh_from_db()
        producto.refresh_from_db()
        
        print(f"   📊 Total después de actualización: {compra.total}")
        print(f"   📦 Stock después de actualización: {producto.stock}")
        
        # 6. Probar eliminación de detalle
        print("\n6. Probando eliminación de detalle...")
        detalle.delete()
        
        compra.refresh_from_db()
        producto.refresh_from_db()
        
        print(f"   📊 Total después de eliminación: {compra.total}")
        print(f"   📦 Stock después de eliminación: {producto.stock}")
        
        # Limpiar datos de prueba
        print("\n7. Limpiando datos de prueba...")
        compra.delete()
        producto.delete()
        proveedor.delete()
        print("   ✅ Datos de prueba eliminados")
        
        print("\n🎉 ¡Prueba de triggers completada exitosamente!")
        
    except Exception as e:
        print(f"\n❌ Error durante la prueba: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_triggers() 