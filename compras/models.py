# compras/models.py

from django.db import models
from django.utils import timezone
from inventario.models import Producto
from proveedores.models import Proveedor 


class Compra(models.Model):
    MODALIDAD_CHOICES = [
        ('CO', 'Contado'),
        ('CR', 'Crédito'),
    ]
    proveedor = models.ForeignKey(Proveedor, on_delete=models.CASCADE)
    numero = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha = models.DateField(default=timezone.now)
    moneda = models.CharField(max_length=20, default='Guaraní')
    modalidad = models.CharField(max_length=2, choices=MODALIDAD_CHOICES, default='CO')
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
   

    def save(self, *args, **kwargs):
        if not self.numero:
            ultima = Compra.objects.order_by('-id').first()
            if ultima and ultima.numero.isdigit():
                self.numero = str(int(ultima.numero) + 1).zfill(6)
            else:
                self.numero = '000001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f'Compra #{self.numero}'
   
    @property
    def total_calculado(self):
        return sum(detalle.subtotal for detalle in self.detallecompra_set.all())


    @property
    def total_pagado(self):
        return sum(pago.monto for pago in self.pagos.all())
    
    @property
    def saldo_pendiente(self):
        return self.total - self.total_pagado
    
    def get_cuotas(self):
        if self.modalidad == 'CR':
            return self.pagos.all().order_by('fecha_vencimiento')
        return []


class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto} x {self.cantidad}"


# compras/models.py
class PagoCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='pagos')
    fecha_pago = models.DateField(auto_now_add=True)
    fecha_vencimiento = models.DateField(null=True, blank=True) # <-- Añade este campo
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    
    @property
    def esta_vencido(self):
        from django.utils import timezone
        return self.fecha_vencimiento and self.fecha_vencimiento < timezone.now().date()
    
    def __str__(self):
        return f"Pago de {self.monto} para compra #{self.compra.id}"