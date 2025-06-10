# facturacion/forms.py
from django import forms
from .models import Factura, Credito
from creditos.models import Plazo

class FacturaForm(forms.ModelForm):
    class Meta:
        model = Factura
        fields = '__all__'
    
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