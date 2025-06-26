from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.db import transaction
from .models import DetalleCompra, Compra
from inventario.models import Producto

@receiver(post_save, sender=DetalleCompra)
def actualizar_total_compra(sender, instance, created, **kwargs):
    """
    Trigger para actualizar el total de la compra cuando se guarda un detalle
    """
    with transaction.atomic():
        # Recalcular el total de la compra
        total = sum(detalle.subtotal for detalle in instance.compra.detalles.all())
        instance.compra.total = total
        instance.compra.save(update_fields=['total'])

@receiver(post_delete, sender=DetalleCompra)
def actualizar_total_compra_delete(sender, instance, **kwargs):
    """
    Trigger para actualizar el total de la compra cuando se elimina un detalle
    """
    with transaction.atomic():
        # Recalcular el total de la compra
        total = sum(detalle.subtotal for detalle in instance.compra.detalles.all())
        instance.compra.total = total
        instance.compra.save(update_fields=['total'])

@receiver(post_save, sender=DetalleCompra)
def actualizar_stock_producto(sender, instance, created, **kwargs):
    """
    Trigger para actualizar el stock del producto cuando se registra una compra
    """
    with transaction.atomic():
        producto = instance.producto
        
        if created:
            # Nueva compra - aumentar stock
            producto.stock += instance.cantidad
        else:
            # Actualización - calcular diferencia
            # Obtener el detalle anterior (si existe)
            try:
                detalle_anterior = DetalleCompra.objects.get(id=instance.id)
                diferencia = instance.cantidad - detalle_anterior.cantidad
                producto.stock += diferencia
            except DetalleCompra.DoesNotExist:
                # Si no existe el anterior, es una nueva inserción
                producto.stock += instance.cantidad
        
        producto.save(update_fields=['stock'])

@receiver(post_delete, sender=DetalleCompra)
def revertir_stock_producto(sender, instance, **kwargs):
    """
    Trigger para revertir el stock del producto cuando se elimina un detalle
    """
    with transaction.atomic():
        producto = instance.producto
        producto.stock -= instance.cantidad
        producto.save(update_fields=['stock']) 