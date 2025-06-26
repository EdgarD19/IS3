from django.db import models
from django.utils import timezone
from datetime import timedelta
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
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    modalidad = models.CharField(max_length=2, choices=MODALIDAD_CHOICES, default='CO')
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            ultima = Compra.objects.order_by('-id').first()
            if ultima and ultima.numero.isdigit():
                self.numero = str(int(ultima.numero) + 1).zfill(6)
            else:
                self.numero = '000001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Compra #{self.numero} - {self.proveedor.nombre}"

# models.py
class CreditoCompra(models.Model):
    MODALIDAD_MENSUAL = 'mensual'
    MODALIDAD_PERSONALIZADA = 'personalizada'
    MODALIDAD_CHOICES = [
        (MODALIDAD_MENSUAL, 'Mensual'),
        (MODALIDAD_PERSONALIZADA, 'Personalizada'),
    ]
    
    compra = models.OneToOneField(Compra, on_delete=models.CASCADE, related_name='credito')
    cantidad_cuotas = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    fecha_inicio = models.DateField(default=timezone.now)
    dias_vencimiento = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Crédito de compra #{self.compra.numero} - {self.compra.total} {self.compra.moneda}"

    def save(self, *args, **kwargs):
        # Eliminamos la generación automática de cuotas aquí
        super().save(*args, **kwargs)

    def generar_cuotas(self):
        """Método separado para generar cuotas, idéntico al de ventas"""
        self.cuotas.all().delete()  # Eliminar cuotas existentes
        
        if self.modalidad == self.MODALIDAD_PERSONALIZADA and self.dias_vencimiento:
            dias = list(map(int, filter(None, self.dias_vencimiento.split(','))))
        else:
            dias = [30 * (i+1) for i in range(self.cantidad_cuotas)]
        
        monto_cuota = self.compra.total / self.cantidad_cuotas
        
        for i, dias_vencimiento in enumerate(dias):
            CuotaCompra.objects.create(
                credito=self,
                numero=i+1,
                monto=monto_cuota,  # Cambiado a 'monto' para mantener consistencia
                vence=self.fecha_inicio + timedelta(days=dias_vencimiento)
            )

    @property
    def esta_pagado(self):
        return not self.cuotas.filter(pagado=False).exists()

    @property
    def tiene_morosidad(self):
        hoy = timezone.now().date()
        return self.cuotas.filter(pagado=False, vence__lt=hoy).exists()

    @property
    def total_pagado(self):
        return sum(cuota.monto for cuota in self.cuotas.filter(pagado=True))

    @property
    def saldo_pendiente(self):
        return self.compra.total - self.total_pagado

class CuotaCompra(models.Model):
    credito = models.ForeignKey(CreditoCompra, on_delete=models.CASCADE, related_name='cuotas')
    numero = models.PositiveIntegerField()
    monto = models.DecimalField(max_digits=12, decimal_places=2)
    vence = models.DateField()
    pagado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)
    metodo_pago = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        ordering = ['numero']

    def __str__(self):
        return f"Cuota {self.numero} de {self.credito}"

    @property
    def esta_vencida(self):
        return not self.pagado and self.vence < timezone.now().date()

class DetalleCompra(models.Model):
    compra = models.ForeignKey(Compra, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} - {self.subtotal}"

    