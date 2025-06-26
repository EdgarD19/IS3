from django.db import migrations

class Migration(migrations.Migration):

    dependencies = [
        ('compras', '0009_compra_observacion_alter_compra_total_creditocompra_and_more'),
    ]

    operations = [
        migrations.RunSQL(
            # SQL para crear los triggers
            """
            -- Trigger para actualizar el total de la compra cuando se inserta/actualiza/elimina un detalle
            CREATE OR REPLACE FUNCTION actualizar_total_compra()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Actualizar el total de la compra
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

            -- Trigger para INSERT en detalles de compra
            CREATE TRIGGER trigger_actualizar_total_compra_insert
                AFTER INSERT ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_total_compra();

            -- Trigger para UPDATE en detalles de compra
            CREATE TRIGGER trigger_actualizar_total_compra_update
                AFTER UPDATE ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_total_compra();

            -- Trigger para DELETE en detalles de compra
            CREATE TRIGGER trigger_actualizar_total_compra_delete
                AFTER DELETE ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_total_compra();

            -- Trigger para actualizar el stock del producto cuando se registra una compra
            CREATE OR REPLACE FUNCTION actualizar_stock_producto()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Actualizar el stock del producto
                UPDATE inventario_producto 
                SET stock = stock + NEW.cantidad
                WHERE id = NEW.producto_id;
                
                RETURN NEW;
            END;
            $$ LANGUAGE plpgsql;

            -- Trigger para INSERT en detalles de compra (actualizar stock)
            CREATE TRIGGER trigger_actualizar_stock_compra_insert
                AFTER INSERT ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_stock_producto();

            -- Trigger para actualizar el stock cuando se modifica una cantidad
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

            -- Trigger para UPDATE en detalles de compra (actualizar stock)
            CREATE TRIGGER trigger_actualizar_stock_compra_update
                AFTER UPDATE ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION actualizar_stock_producto_modificacion();

            -- Trigger para revertir el stock cuando se elimina un detalle
            CREATE OR REPLACE FUNCTION revertir_stock_producto()
            RETURNS TRIGGER AS $$
            BEGIN
                -- Revertir el stock del producto
                UPDATE inventario_producto 
                SET stock = stock - OLD.cantidad
                WHERE id = OLD.producto_id;
                
                RETURN OLD;
            END;
            $$ LANGUAGE plpgsql;

            -- Trigger para DELETE en detalles de compra (revertir stock)
            CREATE TRIGGER trigger_revertir_stock_compra_delete
                AFTER DELETE ON compras_detallecompra
                FOR EACH ROW
                EXECUTE FUNCTION revertir_stock_producto();
            """,
            # SQL para revertir los triggers (en caso de rollback)
            """
            DROP TRIGGER IF EXISTS trigger_actualizar_total_compra_insert ON compras_detallecompra;
            DROP TRIGGER IF EXISTS trigger_actualizar_total_compra_update ON compras_detallecompra;
            DROP TRIGGER IF EXISTS trigger_actualizar_total_compra_delete ON compras_detallecompra;
            DROP TRIGGER IF EXISTS trigger_actualizar_stock_compra_insert ON compras_detallecompra;
            DROP TRIGGER IF EXISTS trigger_actualizar_stock_compra_update ON compras_detallecompra;
            DROP TRIGGER IF EXISTS trigger_revertir_stock_compra_delete ON compras_detallecompra;
            DROP FUNCTION IF EXISTS actualizar_total_compra();
            DROP FUNCTION IF EXISTS actualizar_stock_producto();
            DROP FUNCTION IF EXISTS actualizar_stock_producto_modificacion();
            DROP FUNCTION IF EXISTS revertir_stock_producto();
            """
        ),
    ] 