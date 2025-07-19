from django import template
register = template.Library()

@register.filter
def get_historial(historial, key):
    return historial.get(key, [])


@register.filter
def dict_get(d, key):
    return d.get(key, [])