from django.db import models
from clientes.models import Cliente
from django.utils import timezone

class Factura(models.Model):
    MODALIDAD_CHOICES = [
        ('CO', 'Contado'),
        ('CR', 'Crédito'),
    ]
    
    cliente = models.ForeignKey(Cliente, on_delete=models.CASCADE)
    numero = models.CharField(max_length=20, unique=True)
    fecha = models.DateField(default=timezone.now)
    moneda = models.CharField(max_length=20, default='Guaraní')
    total = models.DecimalField(max_digits=12, decimal_places=2)
    modalidad = models.CharField(max_length=2, choices=MODALIDAD_CHOICES, default='CO')
    observacion = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.numero} - {self.cliente.nombre}"

class Credito(models.Model):
    MODALIDAD_MENSUAL = 'mensual'
    MODALIDAD_PERSONALIZADA = 'personalizada'
    MODALIDAD_CHOICES = [
        (MODALIDAD_MENSUAL, 'Mensual'),
        (MODALIDAD_PERSONALIZADA, 'Personalizada'),
    ]
    
    factura = models.OneToOneField(Factura, on_delete=models.CASCADE, related_name='credito')
    cantidad_cuotas = models.PositiveIntegerField()
    modalidad = models.CharField(max_length=20, choices=MODALIDAD_CHOICES)
    fecha_inicio = models.DateField(default=timezone.now)
    dias_vencimiento = models.CharField(max_length=255, blank=True, null=True)

    def __str__(self):
        return f"Crédito de {self.factura.cliente.nombre} - {self.factura.total} Gs. ({self.cantidad_cuotas} cuotas)"

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
       

    def generar_cuotas(self):
        from datetime import timedelta
        
        # Eliminar cuotas existentes si las hay
        self.cuotas.all().delete()
        
        # Calcular fechas de vencimiento
        if self.modalidad == self.MODALIDAD_PERSONALIZADA and self.dias_vencimiento:
            dias = list(map(int, filter(None, self.dias_vencimiento.split(','))))
        else:
            # Modalidad mensual por defecto
            dias = [30 * (i+1) for i in range(self.cantidad_cuotas)]
        
        # Calcular monto por cuota
        monto_cuota = self.factura.total / self.cantidad_cuotas
        
        # Crear cuotas
        for i, dias_vencimiento in enumerate(dias):
            Cuota.objects.create(
                credito=self,
                numero=i+1,
                importe=monto_cuota,
                vence=self.fecha_inicio + timedelta(days=dias_vencimiento)
            )


    @property
    def esta_pagado(self):
        return not self.cuotas.filter(cobrado=False).exists()

    @property
    def tiene_morosidad(self):
        hoy = timezone.now().date()
        return self.cuotas.filter(cobrado=False, vence__lt=hoy).exists()


class Cuota(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='cuotas')
    numero = models.PositiveIntegerField()
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    vence = models.DateField()
    cobrado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Cuota {self.numero} de {self.credito}"

    @property
    def esta_vencida(self):
        from django.utils import timezone
        return not self.cobrado and self.vence < timezone.now().date()
