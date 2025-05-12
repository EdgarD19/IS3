from django.shortcuts import render, redirect
from .models import Venta
from facturacion.models import Factura
from django import forms

class VentaForm(forms.ModelForm):
    class Meta:
        model = Venta
        fields = ['factura', 'modalidad', 'observacion']

def lista_ventas(request):
    ventas = Venta.objects.select_related('factura').all()
    return render(request, 'ventas/lista.html', {'ventas': ventas})

def crear_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('lista_ventas')
    else:
        form = VentaForm()
    return render(request, 'ventas/form.html', {'form': form})