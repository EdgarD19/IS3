# IS3 — Sistema GQC (Django)

Aplicación web para gestionar clientes, facturas, ventas, (contado o crédito), cuentas por cobrar (créditos y cuotas) y pagos asociados a cuotas. 

## Requisitos

- Python 3.10 o superior (recomendado 3.11+)
- `pip`

## Instalación y ejecución

Desde la raíz del proyecto (`IS3`):

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
python manage.py migrate
python manage.py runserver
```

Abre [http://127.0.0.1:8000/](http://127.0.0.1:8000/) para la página de inicio.

### Panel de administración

```powershell
python manage.py createsuperuser
```

Luego entra en [http://127.0.0.1:8000/admin/](http://127.0.0.1:8000/admin/).

## Estructura del proyecto

| Ruta | Descripción |
|------|-------------|
| `gqc_system/` | Configuración del proyecto Django (`settings`, `urls`, `wsgi`) |
| `clientes/` | Modelo `Cliente` y CRUD básico |
| `facturacion/` | Facturas vinculadas a clientes |
| `ventas/` | Ventas ligadas a facturas (modalidad contado/crédito) |
| `cuentas_cobrar/` | Créditos, cuotas y vistas de registro/seguimiento |
| `pagos/` | Modelo `Pago` por cuota (registrable vía admin) |
| `templates/` | Plantillas HTML compartidas |

## Rutas principales

| URL | Descripción |
|-----|-------------|
| `/` | Inicio |
| `/admin/` | Administración Django |
| `/clientes/` | Listado de clientes |
| `/clientes/nuevo/` | Alta de cliente |
| `/facturas/` | Listado de facturas |
| `/facturas/nuevo/` | Nueva factura |
| `/facturas/factura/<id>/` | Detalle de cuenta asociado a la factura |
| `/ventas/` | Listado de ventas |
| `/ventas/nuevo/` | Nueva venta |
| `/cuentas_cobrar/registrar/` | Registrar crédito |
| `/cuentas_cobrar/lista/` | Lista de créditos |
| `/cuentas_cobrar/cuotas/<id>/` | Detalle de cuotas de un crédito |

## Dependencias

Definidas en `requirements.txt`: Django 5.2.1 y paquetes de soporte (asgiref, sqlparse, tzdata).
