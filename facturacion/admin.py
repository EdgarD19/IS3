# facturacion/admin.py
from django.contrib import admin
from .models import Factura, Credito, Cuota

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'total', 'modalidad', 'descripcion_plazo')
    list_filter = ('modalidad', 'fecha')
    search_fields = ('numero', 'cliente__nombre')

@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = ('factura', 'plazo', 'fecha_inicio')
    search_fields = ('factura__numero',)

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ('credito', 'numero', 'importe', 'vence', 'estado')
    list_filter = ('cobrado', 'vence')
    search_fields = ('credito__factura__numero',)