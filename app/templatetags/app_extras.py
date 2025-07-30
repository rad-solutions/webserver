from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.simple_tag(takes_context=True)
def url_replace(context, **kwargs):
    """Este template tag reemplaza o añade parámetros GET en la URL actual.

    Esencial para que la paginación funcione correctamente con los filtros.
    """
    query = context["request"].GET.copy()
    for key, value in kwargs.items():
        query[key] = value
    return query.urlencode()
