from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def break_every(value, length=10):
    if not value:
        return ''
    return '<br>'.join([value[i:i+length] for i in range(0, len(value), length)])