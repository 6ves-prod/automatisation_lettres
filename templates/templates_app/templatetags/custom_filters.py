from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Récupère un élément d'un dictionnaire avec une clé dynamique"""
    if isinstance(dictionary, dict):
        return dictionary.get(key)
    return None

@register.filter
def add_str(value, arg):
    """Concatène deux chaînes de caractères"""
    return str(value) + str(arg)