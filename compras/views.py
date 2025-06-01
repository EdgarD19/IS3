# compras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Compra, DetalleCompra
from django.forms import inlineformset_factory
from django.urls import reverse
from .forms import CompraForm, DetalleCompraForm
from proveedores.models import Proveedor
from inventario.models import Producto  # ← Importar Producto

DetalleCompraFormSet = inlineformset_factory(
    Compra, DetalleCompra,
    form=DetalleCompraForm,
    extra=1, can_delete=True
)
def lista_compras(request):
    compras = Compra.objects.all().order_by('-fecha')
    return render(request, 'compras/lista_compras.html', {'compras': compras})

def nueva_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        formset = DetalleCompraFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            compra = form.save(commit=False)
            compra.total = 0
            compra.save()

            total = 0
            detalles = formset.save(commit=False)
            for detalle in detalles:
                detalle.compra = compra
                detalle.save()
                producto = detalle.producto
                producto.stock += detalle.cantidad
                producto.save()
                total += detalle.subtotal

            compra.total = total
            compra.save()
            return redirect('lista_compra', compra_id=compra.id)
    else:
        form = CompraForm()
        formset = DetalleCompraFormSet()

    # Este render debe ir fuera del if
    return render(request, 'compras/nueva_compra.html', {'form': form, 'formset': formset})



# compras/views.py
def detalle_compra(request, compra_id):
    compra = get_object_or_404(Compra, id=compra_id)
    detalles = compra.detalles.all()
    pagos = compra.pagos.all().order_by('fecha_vencimiento')  # Ordenar por fecha de vencimiento
    
    return render(request, 'compras/detalle_compra.html', {
        'compra': compra,
        'detalles': detalles,
        'pagos': pagos,
    })