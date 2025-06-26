# ventas/forms.py
from django import forms
from .models import Venta, DetalleVenta
from clientes.models import Cliente
from inventario.models import Producto
from django.core.exceptions import ValidationError

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['cliente', 'fecha', 'moneda', 'modalidad', 'numero','metodo_pago']
        widgets = {
            'cliente': forms.Select(attrs={'class': 'form-select'}),
            'fecha': forms.DateInput(attrs={'class': 'form-control', 'type': 'date'}),
            'moneda': forms.Select(attrs={'class': 'form-select'}),
            'modalidad': forms.Select(attrs={'class': 'form-select', 'onchange': 'toggleCreditFields()'}),
            'numero': forms.TextInput(attrs={'class': 'form-control'}),
            'metodo_pago': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ordenar clientes alfabéticamente, si querés
        self.fields['cliente'].queryset = Cliente.objects.all().order_by('nombre')




class DetalleVentaForm(forms.ModelForm):
    producto_nombre = forms.CharField(label='Producto')  # Campo adicional para búsqueda

    class Meta:
        model = DetalleVenta
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
