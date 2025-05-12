from django import forms
from .models import Credito
from ventas.models import Venta

class CreditoForm(forms.ModelForm):
    venta = forms.ModelChoiceField(
        queryset=Venta.objects.filter(modalidad=Venta.CREDITO),
        label='Venta a Crédito'
    )
    dias_vencimiento = forms.CharField(
        required=False,
        label='Días de vencimiento para cada cuota (separados por coma)',
        help_text='Ejemplo: 30,45,60'
    )

    class Meta:
        model = Credito
        fields = ['venta', 'cliente', 'monto', 'cantidad_cuotas', 'modalidad', 'fecha_inicio'] 