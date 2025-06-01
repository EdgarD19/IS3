from django.contrib import admin
from .models import Factura, Credito, Cuota

@admin.register(Factura)
class FacturaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'moneda', 'total', 'modalidad')
    search_fields = ('numero', 'cliente__nombre')
    list_filter = ('moneda', 'fecha', 'modalidad')

@admin.register(Credito)
class CreditoAdmin(admin.ModelAdmin):
    list_display = ('factura', 'cantidad_cuotas', 'modalidad', 'fecha_inicio')
    search_fields = ('factura__numero', 'factura__cliente__nombre')
    list_filter = ('modalidad',)

@admin.register(Cuota)
class CuotaAdmin(admin.ModelAdmin):
    list_display = ('credito', 'numero', 'importe', 'vence', 'cobrado')
    search_fields = ('credito__factura__numero',)
    list_filter = ('cobrado', 'vence')