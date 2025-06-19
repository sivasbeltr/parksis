from django import template

register = template.Library()


@register.filter
def get_item(dictionary, key):
    """
    Dictionary'den key ile değer alır.
    Kullanım: {{ dict|get_item:key }}
    """
    if dictionary is None or key is None:
        return None
    return dictionary.get(key, None)


@register.filter
def get_color(colors_dict, status_key):
    """
    Renk dictionary'sinden durum için renk alır.
    Kullanım: {{ GOREV_DURUM_COLORS|get_color:gorev.durum }}
    """
    if colors_dict is None or status_key is None:
        return None
    return colors_dict.get(status_key, {})


@register.filter
def split(value, separator):
    """
    String'i belirtilen separator ile böler.
    Kullanım: {{ "a,b,c"|split:"," }}
    """
    if value is None:
        return []
    return value.split(separator)


@register.filter
def add_suffix(value, suffix):
    """
    Değere suffix ekler.
    Kullanım: {{ color|add_suffix:"20" }}
    """
    if value is None:
        return ""
    return str(value) + str(suffix)


@register.filter
def get_gorev_durum_color(durum):
    """
    Görev durumu için renk bilgilerini alır.
    """
    from istakip.choices import GOREV_DURUM_COLORS

    return GOREV_DURUM_COLORS.get(durum, {})


@register.filter
def get_gorev_oncelik_color(oncelik):
    """
    Görev önceliği için renk bilgilerini alır.
    """
    from istakip.choices import GOREV_ONCELIK_COLORS

    return GOREV_ONCELIK_COLORS.get(oncelik, {})


@register.filter
def get_kontrol_durum_color(durum):
    """
    Kontrol durumu için renk bilgilerini alır.
    """
    from istakip.choices import KONTROL_DURUM_COLORS

    return KONTROL_DURUM_COLORS.get(durum, {})


# gorev_asama_durum_color
@register.filter
def get_gorev_asama_durum_color(durum):
    """
    Görev aşama durumu için renk bilgilerini alır.
    """
    from istakip.choices import GOREV_ASAMA_DURUM_COLORS

    return GOREV_ASAMA_DURUM_COLORS.get(durum, {})
