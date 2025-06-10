# compras/forms.py
from django import forms
from .models import Compra, DetalleCompra
from proveedores.models import Proveedor
from inventario.models import Producto
from django.forms.models import BaseInlineFormSet
from django.core.exceptions import ValidationError

class CompraForm(forms.ModelForm):
    class Meta:
        model = Compra
        fields = ['proveedor', 'fecha', 'moneda', 'modalidad']
        widgets = {
            'proveedor': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'modalidad': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar proveedores alfabéticamente, si querés
        self.fields['proveedor'].queryset = Proveedor.objects.all().order_by('nombre')

# compras/forms.py
class DetalleCompraForm(forms.ModelForm):
    producto_nombre = forms.CharField(label='Producto')  # Campo adicional para búsqueda
    
    class Meta:
        model = DetalleCompra
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