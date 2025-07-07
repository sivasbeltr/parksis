from django import template
from django.contrib.auth.models import Group

register = template.Library()


class HasRoleNode(template.Node):
    def __init__(self, roles, nodelist):
        self.roles = roles
        self.nodelist = nodelist

    def render(self, context):
        request = context.get("request")

        # Eğer kullanıcı giriş yapmamışsa içeriği gösterme
        if not request or not request.user.is_authenticated:
            return ""

        # Kullanıcının rollerini al
        user_roles = set(request.user.groups.values_list("name", flat=True))
        required_roles = set(role.strip("'\"") for role in self.roles)

        # Eğer kullanıcı belirtilen rollerden en az birine sahipse içeriği göster
        if user_roles.intersection(required_roles):
            return self.nodelist.render(context)
        return ""


@register.tag(name="has_role")
def do_has_role(parser, token):
    """
    Kullanıcının belirtilen rollerden herhangi birine sahip olup olmadığını kontrol eder
    ve içeriği ona göre gösterir.

    Kullanım:
    {% has_role 'admin' 'user' %}
        Bu içerik sadece admin veya user rolüne sahip kullanıcılara gösterilir
    {% end %}
    """
    try:
        tag_name, *roles = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(
            "%r etiketi en az bir rol almalıdır" % token.contents.split()[0]
        )

    # Etiketin sonunu {% end %} olarak kabul et
    nodelist = parser.parse(("end",))
    parser.delete_first_token()

    return HasRoleNode(roles, nodelist)


# Eski simple_tag'i de tutuyoruz, geriye dönük uyumluluk için
@register.simple_tag(takes_context=True)
def has_role_check(context, *roles):
    """
    Kullanıcının belirtilen rollerden herhangi birine sahip olup olmadığını kontrol eder.

    Kullanım:
    {% load role_tags %}
    {% has_role_check "admin" as is_admin %}
    {% if is_admin %}
        Bu içerik sadece admin rolüne sahip kullanıcılara gösterilir.
    {% endif %}
    """
    request = context["request"]
    if not request.user.is_authenticated:
        return False

    user_roles = set(request.user.groups.values_list("name", flat=True))
    required_roles = set(roles)

    # Kullanıcı belirtilen rollerden herhangi birine sahipse True döndür
    return bool(user_roles.intersection(required_roles))
