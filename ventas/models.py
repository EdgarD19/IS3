# ventas/models.py
from django.db import models
from django.utils import timezone
from datetime import timedelta
from clientes.models import Cliente
from inventario.models import Producto

class Venta(models.Model):
    MODALIDAD_CHOICES = [
        ('CO', 'Contado'),
        ('CR', 'Crédito'),
    ]

    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero = models.CharField(max_length=100, unique=True, blank=True, null=True)
    fecha = models.DateField(default=timezone.now)
    moneda = models.CharField(max_length=20, default='Guaraní')
    total = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    modalidad = models.CharField(max_length=2, choices=MODALIDAD_CHOICES, default='CO')
    observacion = models.TextField(blank=True, null=True)

    def save(self, *args, **kwargs):
        if not self.numero:
            ultima = Venta.objects.order_by('-id').first()
            if ultima and ultima.numero.isdigit():
                self.numero = str(int(ultima.numero) + 1).zfill(6)
            else:
                self.numero = '000001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Venta #{self.numero} - {self.cliente}"


class CreditoVenta(models.Model):
    MODALIDAD_MENSUAL = 'mensual'
    MODALIDAD_PERSONALIZADA = 'personalizada'
    MODALIDAD_CHOICES = [
        (MODALIDAD_MENSUAL, 'Mensual'),
        (MODALIDAD_PERSONALIZADA, 'Personalizada'),
    ]

    venta = models.OneToOneField('Venta', on_delete=models.CASCADE, related_name='credito')
    cantidad_cuotas = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    fecha_inicio = models.DateField(default=timezone.now)
    dias_vencimiento = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Crédito de venta #{self.venta.numero} - {self.venta.total} {self.venta.moneda}"

    def generar_cuotas(self):
        self.cuotas.all().delete()  # Eliminar cuotas existentes antes de generar nuevas

        if self.modalidad == self.MODALIDAD_PERSONALIZADA and self.dias_vencimiento:
            dias = list(map(int, filter(None, self.dias_vencimiento.split(','))))
        else:
            dias = [30 * (i + 1) for i in range(self.cantidad_cuotas)]

        importe_cuota = self.venta.total / self.cantidad_cuotas

        for i, dias_venc in enumerate(dias):
            from ventas.models import CuotaVenta  # Evitar posible import circular
            CuotaVenta.objects.create(
                credito=self,
                numero=i + 1,
                importe=importe_cuota,
                vence=self.fecha_inicio + timedelta(days=dias_venc)
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
        return sum(cuota.importe for cuota in self.cuotas.filter(pagado=True))

    @property
    def saldo_pendiente(self):
        return self.venta.total - self.total_pagado
    

class CuotaVenta(models.Model):
    credito = models.ForeignKey(CreditoVenta, on_delete=models.CASCADE, related_name='cuotas')
    numero = models.PositiveIntegerField()
    importe = models.DecimalField(max_digits=12, decimal_places=2) 
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

class DetalleVenta(models.Model):
    venta = models.ForeignKey(Venta, on_delete=models.CASCADE, related_name='detalles')
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    precio_unitario = models.DecimalField(max_digits=12, decimal_places=2)

    @property
    def subtotal(self):
        return self.cantidad * self.precio_unitario

    def __str__(self):
        return f"{self.producto.nombre} x {self.cantidad} - {self.subtotal}"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        self.venta.total = sum(detalle.subtotal for detalle in self.venta.detalles.all())
        self.venta.save()
