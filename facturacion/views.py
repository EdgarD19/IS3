from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db import transaction
from django.utils import timezone
from .models import Factura, Credito, Cuota, Cliente, DetalleFactura
from .forms import FacturaForm,DetalleFacturaForm

from django.forms import inlineformset_factory

DetalleFacturaFormSet = inlineformset_factory(
    Factura, DetalleFactura,
    form=DetalleFacturaForm,
    extra=1, can_delete=True
)

def lista_facturas(request):
    facturas = Factura.objects.select_related('cliente').all()

    # Filtro por cliente (nombre)
    cliente = request.GET.get("cliente")
    if cliente:
        facturas = facturas.filter(cliente__nombre__icontains=cliente)

    # Filtro por modalidad
    modalidad = request.GET.get("modalidad")
    if modalidad:
        facturas = facturas.filter(modalidad=modalidad)

    # Convertimos a lista para aplicar filtros con lógica Python
    facturas = list(facturas)

    estado = request.GET.get("estado")
    if estado:
        if estado == "pagado":
            facturas = [f for f in facturas if (f.modalidad == 'CO') or (hasattr(f, 'credito') and f.credito.esta_pagado)]
        elif estado == "moroso":
            facturas = [f for f in facturas if hasattr(f, 'credito') and f.credito.tiene_morosidad]
        elif estado == "curso":
            facturas = [f for f in facturas if hasattr(f, 'credito') and not f.credito.esta_pagado and not f.credito.tiene_morosidad]

    return render(request, 'facturacion/lista.html', {
        'facturas': facturas,
        'seccion': 'facturas'
    })




def crear_factura(request):
    if request.method == 'POST':
        form = FacturaForm(request.POST)
        formset = DetalleFacturaFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            with transaction.atomic():
                factura = form.save(commit=False)
                factura.total = 0
                # Guardar la factura primero
                factura.save()

                # 2. Procesar detalles
                for form_detalle in formset:
                    if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE', False):
                        detalle = form_detalle.save(commit=False)
                        detalle.factura = factura
                        detalle.save()
                        factura.total += detalle.subtotal
                        
                        # Actualizar stock
                        producto = detalle.producto
                        producto.stock += detalle.cantidad
                        producto.save()

                factura.save()

                # Si es crédito, crear el crédito y las cuotas
                if form.cleaned_data['modalidad'] == 'CR':
                    credito = Credito.objects.create(
                        factura=factura,
                        cantidad_cuotas=form.cleaned_data['cantidad_cuotas'],
                        dias_vencimiento=form.cleaned_data['dias_vencimiento'],
                        fecha_inicio=form.cleaned_data['fecha_inicio'],
                        modalidad='mensual'  # O la modalidad que uses
                    )
                    credito.generar_cuotas()

                    messages.success(request, 'Factura a crédito creada exitosamente!')
                else:
                    messages.success(request, 'Factura de contado creada exitosamente!')

                return redirect('lista_facturas')
    else:
        # Obtener el último número de factura para asignar el siguiente
        ultima_factura = Factura.objects.order_by('-id').first()
        if ultima_factura and ultima_factura.numero.isdigit():
            nuevo_numero = str(int(ultima_factura.numero) + 1).zfill(6)  # Ejemplo: '000001'
        else:
            nuevo_numero = '000001'

        form = FacturaForm(initial={
            'fecha': timezone.now().date(),
            'modalidad': 'CO',  # Contado por defecto
            'numero': nuevo_numero
        })
        formset = DetalleFacturaFormSet();

    return render(request, 'facturacion/crear_factura.html', {
        'form': form,
        'clientes': Cliente.objects.all(),
        'formset': formset
    })


def crear_cuotas(credito):
    """Crea las cuotas automáticamente para un crédito"""
    dias_array = [int(d.strip()) for d in credito.dias_vencimiento.split(',')]
    importe_cuota = credito.factura.total / credito.cantidad_cuotas
    
    for i in range(1, credito.cantidad_cuotas + 1):
        dias = dias_array[i-1] if i <= len(dias_array) else dias_array[-1]
        fecha_vencimiento = credito.fecha_inicio + timezone.timedelta(days=dias)
        
        Cuota.objects.create(
            credito=credito,
            numero=i,
            importe=importe_cuota,
            vence=fecha_vencimiento,
            cobrado=False
        )

def detalle_cuenta(request, factura_id):
    factura = get_object_or_404(
        Factura.objects.select_related('cliente', 'credito').prefetch_related('credito__cuotas'),
        id=factura_id
    )
    return render(request, 'facturacion/detalle_cuenta.html', {
        'factura': factura,
        'detalles':factura.detalles.all()
    })



def registrar_pago(request, cuota_id):
    cuota = get_object_or_404(Cuota, id=cuota_id)

    if not cuota.cobrado:
        cuota.cobrado = True
        cuota.fecha_pago = timezone.now()
        cuota.save()

    return redirect('detalle_cuenta', factura_id=cuota.credito.factura.id) 



