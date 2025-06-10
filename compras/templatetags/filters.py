from django import template
register = template.Library()

@register.filter
def formato_py(value):
    try:
        num = float(value)
        # Formatea y reemplaza comas/points según convención PY
        formatted = "{:,.2f}".format(num).replace(",", "X").replace(".", ",").replace("X", ".")
        # Elimina ,00 si es entero
        return formatted[:-3] if formatted.endswith(",00") else formatted
    except (ValueError, TypeError):
        return str(value)