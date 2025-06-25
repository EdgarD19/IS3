
from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_ventas, name='lista_ventas'), 
    path('nueva/', views.nueva_venta, name='nueva_venta'), 
    path('<int:venta_id>/', views.detalle_venta, name='detalle_venta'),
    path('cuotas/<int:cuota_id>/pago/', views.registrar_pago, name='registrar_pago_venta'),
]
