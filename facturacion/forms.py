# facturacion/forms.py
from django import forms
from .models import Factura, Credito, DetalleFactura
from creditos.models import Plazo
from inventario.models import Producto

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = ['cliente', 'fecha', 'moneda', 'modalidad', 'numero']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['modalidad'].widget.attrs.update({
            'onchange': 'toggleCreditFields()'
        })

class CreditoForm(forms.ModelForm):
    plazo = forms.ModelChoiceField(
        queryset=Plazo.objects.filter(activo=True),
        label="Plan de pagos",
        help_text="Seleccione un plan de pagos existente o cree uno nuevo"
    )
    
    class Meta:
        model = Credito
        fields = ['plazo', 'fecha_inicio']


class DetalleFacturaForm(forms.ModelForm):
    producto_nombre = forms.CharField(label='Producto')  # Campo adicional para búsqueda
    
    class Meta:
        model = DetalleFactura
        fields = ['producto_nombre', 'cantidad', 'precio_unitario']
    
    def clean(self):
        cleaned_data = super().clean()
        precio_unitario = cleaned_data.get('precio_unitario')
        
        if precio_unitario is None or precio_unitario <= 0:
            raise ValidationError("El precio unitario debe ser mayor que 0")
        
        return cleaned_data
    
    def save(self, commit=True):
        detalle = super().save(commit=False)
        
        # Si es un producto nuevo
        if not detalle.producto_id:
            nombre_producto = self.cleaned_data.get('producto_nombre')
            detalle.producto, created = Producto.objects.get_or_create(
                nombre=nombre_producto,
                defaults={
                    'precio_compra': detalle.precio_unitario,
                    'stock': 0
                }
            )
        
        if commit:
            detalle.save()
        
        return detalle