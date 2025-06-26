from django.db import models

class Producto(models.Model):
    codigo = models.CharField(max_length=20, unique=True, blank=True, null=True)
    nombre = models.CharField(max_length=100)
    precio_compra = models.DecimalField(max_digits=10, decimal_places=2)
    stock = models.IntegerField(default=0)
   

    def save(self, *args, **kwargs):
        if not self.codigo:
            ultimo = Producto.objects.order_by('-id').first()
            if ultimo and ultimo.codigo and ultimo.codigo.startswith('PROD-'):
                try:
                    # Extraer el número y aumentarlo
                    num = int(ultimo.codigo.split('-')[1]) + 1
                    self.codigo = f"PROD-{str(num).zfill(6)}"
                except (IndexError, ValueError):
                    # Si hay error en el formato, empezar desde 1
                    self.codigo = 'PROD-000001'
            else:
                # Si no hay productos o el último no tiene código válido
                self.codigo = 'PROD-000001'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.codigo} - {self.nombre}"