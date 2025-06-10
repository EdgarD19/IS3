# creditos/models.py
from django.db import models

class TipoPlazo(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre

class Plazo(models.Model):
    nombre = models.CharField(max_length=100)
    tipo = models.ForeignKey(TipoPlazo, on_delete=models.PROTECT)
    cantidad_cuotas = models.PositiveIntegerField()
    es_irregular = models.BooleanField(default=False)
    activo = models.BooleanField(default=True)
    
    class Meta:
        verbose_name_plural = "Plazos"
    
    def __str__(self):
        return f"{self.nombre} ({self.cantidad_cuotas} cuotas)"

class DetallePlazo(models.Model):
    plazo = models.ForeignKey(Plazo, related_name='detalles', on_delete=models.CASCADE)
    numero_cuota = models.PositiveIntegerField()
    dias_vencimiento = models.PositiveIntegerField()
    
    class Meta:
        ordering = ['plazo', 'numero_cuota']
    
    def __str__(self):
        return f"Cuota {self.numero_cuota} a {self.dias_vencimiento} días"