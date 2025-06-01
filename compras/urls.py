# compras/urls.py

from django.urls import path
from . import views

urlpatterns = [
    path('', views.lista_compras, name='lista_compras'),
    path('nueva/', views.nueva_compra, name='nueva_compra'),
    path('<int:compra_id>/', views.detalle_compra, name='detalle_compra'),
]
