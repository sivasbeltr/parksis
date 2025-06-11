# filepath: c:\Users\cgundogdu\Desktop\Proje\parksis\istakip\templatetags\dict_extras.py
from django import template

register = template.Library()


@register.filter
def dict_get(dictionary, key):
    """Dictionary'den key ile değer alma filtresi"""
    if isinstance(dictionary, dict):
        return dictionary.get(str(key), [])
    return []


@register.filter
def length(value):
    """Değerin uzunluğunu döndürür"""
    try:
        return len(value)
    except (ValueError, TypeError):
        return 0


@register.filter
def sorun_sayisi(kontroller):
    """Kontroller listesindeki sorun sayısını hesaplar"""
    try:
        if not kontroller:
            return 0
        return sum(1 for kontrol in kontroller if kontrol.get("sorun_sayisi", 0) > 0)
    except (AttributeError, TypeError):
        return 0


@register.filter
def div(value, arg):
    """Bölme işlemi"""
    try:
        return float(value) / float(arg)
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def mul(value, arg):
    """Çarpma işlemi"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0
