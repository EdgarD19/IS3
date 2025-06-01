from django import forms
from .models import Factura, Credito

class FacturaForm(forms.ModelForm):
    # Campos adicionales para crédito
    cantidad_cuotas = forms.IntegerField(required=False, min_value=1)
    dias_vencimiento = forms.CharField(required=False)
    fecha_inicio = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    class Meta:
        model = Factura
        fields = ['cliente', 'numero', 'fecha', 'moneda', 'total', 'modalidad', 'observacion']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'modalidad': forms.RadioSelect()
        }

    def clean(self):
        cleaned_data = super().clean()
        if cleaned_data.get('modalidad') == 'CR':
            if not cleaned_data.get('cantidad_cuotas'):
                self.add_error('cantidad_cuotas', 'Este campo es requerido para crédito')
            if not cleaned_data.get('dias_vencimiento'):
                self.add_error('dias_vencimiento', 'Este campo es requerido para crédito')
            if not cleaned_data.get('fecha_inicio'):
                self.add_error('fecha_inicio', 'Este campo es requerido para crédito')
        return cleaned_data