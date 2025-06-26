# compras/views.py
from django.shortcuts import render, redirect, get_object_or_404
from .models import Compra, DetalleCompra,CuotaCompra,CreditoCompra
from django.forms import inlineformset_factory
from django.urls import reverse
from .forms import CompraForm, DetalleCompraForm
from proveedores.models import Proveedor
from inventario.models import Producto  # ← Importar Producto
from django.db.utils import IntegrityError
from django.core.exceptions import ValidationError
from django.contrib import messages  # Import para los mensajes
from django.db import transaction  
from django.utils import timezone

DetalleCompraFormSet = inlineformset_factory(
    Compra, DetalleCompra,
    form=DetalleCompraForm,
    extra=1, can_delete=True
)
def lista_compras(request):
    compras = Compra.objects.select_related('proveedor').all()

    # Filtro por proveedor
    proveedor = request.GET.get("proveedor")
    if proveedor:
        compras = compras.filter(proveedor__nombre__icontains=proveedor)

    # Filtro por fechas
    fecha_inicio = request.GET.get("fecha_inicio")
    if fecha_inicio:
        compras = compras.filter(fecha__gte=fecha_inicio)

    fecha_fin = request.GET.get("fecha_fin")
    if fecha_fin:
        compras = compras.filter(fecha__lte=fecha_fin)

    compras = list(compras)

    # Filtro por estado (pagado, moroso, curso)
    estado = request.GET.get("estado")
    if estado:
        if estado == "pagado":
            compras = [c for c in compras if (c.modalidad == 'CO') or (hasattr(c, 'credito') and c.credito.esta_pagado)]
        elif estado == "moroso":
            compras = [c for c in compras if hasattr(c, 'credito') and c.credito.tiene_morosidad]
        elif estado == "curso":
            compras = [c for c in compras if hasattr(c, 'credito') and not c.credito.esta_pagado and not c.credito.tiene_morosidad]

    return render(request, 'compras/lista_compras.html', {
        'compras': compras,
        'seccion': 'compras'
    })


# views.py
def nueva_compra(request):
    if request.method == 'POST':
        form = CompraForm(request.POST)
        formset = DetalleCompraFormSet(request.POST)
        
        if form.is_valid() and formset.is_valid():
            try:
                with transaction.atomic():
                    # 1. Guardar compra básica
                    compra = form.save(commit=False)
                    compra.total = 0  # Inicializar en 0
                    compra.save()
                    
                    # 2. Procesar detalles
                    for form_detalle in formset:
                        if form_detalle.cleaned_data and not form_detalle.cleaned_data.get('DELETE', False):
                            detalle = form_detalle.save(commit=False)
                            detalle.compra = compra
                            detalle.save()
                            compra.total += detalle.subtotal
                            
                            # Actualizar stock
                            producto = detalle.producto
                            producto.stock += detalle.cantidad
                            producto.save()
                    
                    # 3. Actualizar total de compra
                    compra.save()
                    
                    # 4. Si es crédito, crear y generar cuotas 
                    if compra.modalidad == 'CR':
                        credito = CreditoCompra.objects.create(
                            compra=compra,
                            cantidad_cuotas=3,  # Puedes hacerlo configurable
                            modalidad=CreditoCompra.MODALIDAD_MENSUAL,
                            fecha_inicio=compra.fecha
                        )
                        credito.generar_cuotas()  # Llamada explícita
                    
                    return redirect('lista_compras')
            
            except Exception as e:
                messages.error(request, f'Error al guardar la compra: {str(e)}')
        else:
            messages.error(request, 'Por favor corrige los errores en el formulario')
    else:
        form = CompraForm()
        formset = DetalleCompraFormSet()
    
    return render(request, 'compras/nueva_compra.html', {
        'form': form,
        'formset': formset
    })

def detalle_compra(request, compra_id):
    compra = get_object_or_404(
        Compra.objects.select_related('proveedor', 'credito')
                     .prefetch_related('detalles__producto', 'credito__cuotas'),
        id=compra_id
    )
    
    # Calcular el total sumando los subtotales de los detalles
    detalles = compra.detalles.all()
    total_calculado = sum(detalle.subtotal for detalle in detalles) if detalles else 0
    
    hoy = timezone.now().date()
    cuotas_con_estado = []
    
    if hasattr(compra, 'credito'):
        for cuota in compra.credito.cuotas.all():
            if cuota.pagado:
                estado = 'pagado'
                dias_info = None
            else:
                dias_restantes = (cuota.vence - hoy).days
                if dias_restantes > 0:
                    estado = 'pendiente'
                    dias_info = {'texto': f"{dias_restantes} días", 'clase': 'text-success'}
                elif dias_restantes == 0:
                    estado = 'hoy'
                    dias_info = {'texto': "Hoy", 'clase': 'text-warning'}
                else:
                    estado = 'vencido'
                    dias_info = {'texto': f"{abs(dias_restantes)} días de atraso", 'clase': 'text-danger'}
            
            cuotas_con_estado.append({
                'cuota': cuota,
                'estado': estado,
                'dias_info': dias_info,
                'esta_proxima': estado == 'pendiente' and dias_restantes <= 7
            })
    
    context = {
        'compra': compra,
        'detalles': detalles,
        'total_calculado': total_calculado,  # Añadir este campo
        'cuotas_con_estado': cuotas_con_estado,
        'hoy': hoy,
    }
    return render(request, 'compras/detalle_compra.html', context)

def registrar_pago_compra(request, cuota_id):
    cuota = get_object_or_404(CuotaCompra, id=cuota_id)
    
    if request.method == 'POST':
        try:
            cuota.pagado = True
            cuota.fecha_pago = request.POST.get('fecha_pago')
            cuota.metodo_pago = request.POST.get('metodo_pago')
            cuota.save()
            
            messages.success(request, f'Pago de la cuota {cuota.numero} registrado correctamente')
        except Exception as e:
            messages.error(request, f'Error al registrar el pago: {str(e)}')
    
    return redirect('detalle_compra', compra_id=cuota.credito.compra.id)