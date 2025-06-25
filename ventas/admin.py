from django.contrib import admin
from .models import Venta, CreditoVenta, CuotaVenta

@admin.register(Venta)
class VentaAdmin(admin.ModelAdmin):
    list_display = ('numero', 'cliente', 'fecha', 'total', 'modalidad')
    list_filter = ('modalidad', 'fecha')
    search_fields = ('numero', 'cliente__nombre')

@admin.register(CreditoVenta)
class CreditoVentaAdmin(admin.ModelAdmin):
    list_display = ('venta', 'fecha_inicio')
    search_fields = ('venta__numero',)

@admin.register(CuotaVenta)
class CuotaVentaAdmin(admin.ModelAdmin):
    list_display = ('credito', 'numero', 'vence')
    # list_filter = ('cobrado', 'vence')
    search_fields = ('credito__venta__numero',)
