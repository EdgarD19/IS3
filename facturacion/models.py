# facturacion/models.py
from django.db import models
from clientes.models import Cliente
from django.utils import timezone
from creditos.models import Plazo

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
    
    @property
    def descripcion_plazo(self):
        if self.modalidad == 'CO':
            return "Contado"
        if hasattr(self, 'credito'):
            return self.credito.get_descripcion_plazo()
        return ""

class Credito(models.Model):
    factura = models.OneToOneField(Factura, on_delete=models.CASCADE, related_name='credito')
    plazo = models.ForeignKey(Plazo, on_delete=models.PROTECT)
    fecha_inicio = models.DateField(default=timezone.now)

    def __str__(self):
        return f"Crédito {self.factura.numero} - {self.plazo.nombre}"
    
    def get_descripcion_plazo(self):
        detalles = self.plazo.detalles.all().order_by('numero_cuota')
        dias = "-".join(str(detalle.dias_vencimiento) for detalle in detalles)
        return f"CR-{dias} días"
    
    def generar_cuotas(self):
        from datetime import timedelta
        
        self.cuotas.all().delete()  # Eliminar cuotas existentes
        
        monto_cuota = self.factura.total / self.plazo.cantidad_cuotas
        
        for detalle in self.plazo.detalles.all().order_by('numero_cuota'):
            Cuota.objects.create(
                credito=self,
                numero=detalle.numero_cuota,
                importe=monto_cuota,
                vence=self.fecha_inicio + timedelta(days=detalle.dias_vencimiento)
            )

class Cuota(models.Model):
    credito = models.ForeignKey(Credito, on_delete=models.CASCADE, related_name='cuotas')
    numero = models.PositiveIntegerField()
    importe = models.DecimalField(max_digits=12, decimal_places=2)
    vence = models.DateField()
    cobrado = models.BooleanField(default=False)
    fecha_pago = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Cuota {self.numero} de {self.credito.factura.numero}"
    
    @property
    def estado(self):
        if self.cobrado:
            return "Pagado"
        if self.esta_vencida:
            return "Vencido"
        return "Pendiente"
    
    @property
    def esta_vencida(self):
        return not self.cobrado and self.vence < timezone.now().date()