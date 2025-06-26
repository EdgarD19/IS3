from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Venta, CreditoVenta, CuotaVenta, DetalleVenta
from clientes.models import Cliente
from .forms import VentaForm, DetalleVentaForm
from inventario.models import Producto

from django.forms import inlineformset_factory

DetalleVentaFormSet = inlineformset_factory(
    Venta, DetalleVenta,
    form=DetalleVentaForm,
    extra=1, can_delete=True
)

def lista_ventas(request):
    ventas = Venta.objects.select_related('cliente').all()

    cliente = request.GET.get("cliente")
    if cliente:
        ventas = ventas.filter(cliente__nombre__icontains=cliente)

    modalidad = request.GET.get("modalidad")
    if modalidad:
        ventas = ventas.filter(modalidad=modalidad)

    ventas = list(ventas)
    estado = request.GET.get("estado")
    if estado:
        if estado == "pagado":
            ventas = [v for v in ventas if (v.modalidad == 'CO') or (hasattr(v, 'credito') and v.credito.esta_pagado)]
        elif estado == "moroso":
            ventas = [v for v in ventas if hasattr(v, 'credito') and v.credito.tiene_morosidad]
        elif estado == "curso":
            ventas = [v for v in ventas if hasattr(v, 'credito') and not v.credito.esta_pagado and not v.credito.tiene_morosidad]


    return render(request, 'ventas/lista.html', {
        'ventas': ventas,
        'seccion': 'ventas'
    })

def nueva_venta(request):
    if request.method == 'POST':
        form = VentaForm(request.POST)
        formset = DetalleVentaFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    venta = form.save(commit=False)
                    venta.total = 0
                    venta.save()

                    for form_detalle in formset:
                        if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE', False):
                            detalle = form_detalle.save(commit=False)
                            detalle.venta = venta
                            detalle.save()
                            venta.total += detalle.subtotal

                            producto = detalle.producto
                            producto.stock -= detalle.cantidad
                            producto.save()

                    venta.save()

                    if form.cleaned_data['modalidad'] == 'CR':
                        cantidad_cuotas = int(request.POST.get('cantidad_cuotas', 3))
                        tipo_vencimiento = request.POST.get('tipo_vencimiento', 'regular')
                        dias_vencimiento = request.POST.get('dias_vencimiento', '')
                        fecha_inicio = form.cleaned_data.get('fecha_inicio') or timezone.now().date()

                        if tipo_vencimiento == 'regular':
                            modalidad = CreditoVenta.MODALIDAD_MENSUAL
                            dias_vencimiento = ''
                        else:
                            modalidad = CreditoVenta.MODALIDAD_PERSONALIZADA

                        credito = CreditoVenta.objects.create(
                            venta=venta,
                            cantidad_cuotas=cantidad_cuotas,
                            modalidad=modalidad,
                            fecha_inicio=fecha_inicio,
                            dias_vencimiento=dias_vencimiento
                        )
                        credito.generar_cuotas()

                    return redirect('lista_ventas')

            except Exception as e:
                messages.error(request, f'Error al guardar la venta: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')

    else:
        ultima = Venta.objects.order_by('-id').first()
        if ultima and ultima.numero.isdigit():
            nuevo_numero = str(int(ultima.numero) + 1).zfill(6)
        else:
            nuevo_numero = '000001'

        form = VentaForm(initial={
            'fecha': timezone.now().date(),
            'modalidad': 'CO',
            'numero': nuevo_numero
        })
        formset = DetalleVentaFormSet()

    
    productos = Producto.objects.all()

    return render(request, 'ventas/crear_venta.html', {
        'form': form,
        'clientes': Cliente.objects.all(),
        'formset': formset,
        
    })

def detalle_venta(request, venta_id):
    venta = get_object_or_404(
        Venta.objects.select_related('cliente', 'credito')
                     .prefetch_related('credito__cuotas', 'detalles__producto'),
        id=venta_id
    )

    detalles = venta.detalles.all()
    total_calculado = sum(detalle.subtotal for detalle in detalles)

    total_pagado = 0
    saldo = 0
    if hasattr(venta, 'credito'):
        total_pagado = sum(cuota.importe for cuota in venta.credito.cuotas.filter(pagado=True))
        saldo = venta.total - total_pagado

    return render(request, 'ventas/detalle_cuenta.html', {
        'venta': venta,
        'detalles': detalles,
        'total_calculado': total_calculado,
        'total_pagado': total_pagado,
        'saldo': saldo,
    })

def registrar_pago(request, cuota_id):
    cuota = get_object_or_404(CuotaVenta, id=cuota_id)
    if not cuota.pagado:
        cuota.pagado = True
        cuota.fecha_pago = timezone.now()
        cuota.save()
    return redirect('detalle_venta', venta_id=cuota.credito.venta.id)

