from django import template

register = template.Library()

@register.simple_tag(takes_context=True)
def qs(context, **kwargs):
    request = context.get("request")
    if request is None:
        return ""

    q = request.GET.copy()
    for k, v in kwargs.items():
        if v is None or v == "":
            q.pop(k, None)
        else:
            q[k] = str(v)

    encoded = q.urlencode()
    return ("?" + encoded) if encoded else ""
