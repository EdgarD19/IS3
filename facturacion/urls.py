from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_facturas, name='lista_facturas'),
    path('nueva/', views.crear_factura, name='crear_factura'),
    path('<int:factura_id>/', views.detalle_cuenta, name='detalle_cuenta'),
    #path('<int:factura_id>/credito/', views.registrar_credito, name='registrar_credito'),
    path('cuotas/<int:cuota_id>/pago/', views.registrar_pago, name='registrar_pago'),
]