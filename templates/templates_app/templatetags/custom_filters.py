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


@register.filter
def get_field_value(dictionary, field_id):
    """Récupère la valeur d'un champ dans le dictionnaire current_values"""
    if isinstance(dictionary, dict):
        field_key = f'field_{field_id}'
        return dictionary.get(field_key, '')
    return ''


@register.filter
def multiply(value, arg):
    """Multiplie deux nombres"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def divide(value, arg):
    """Divise deux nombres"""
    try:
        return float(value) / float(arg)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def percentage(value, total):
    """Calcule un pourcentage"""
    try:
        return round((float(value) / float(total)) * 100, 1)
    except (ValueError, TypeError, ZeroDivisionError):
        return 0


@register.filter
def truncate_chars(value, length):
    """Tronque une chaîne à une longueur donnée"""
    if len(str(value)) > int(length):
        return str(value)[:int(length)] + '...'
    return str(value)


@register.filter
def format_date(value, format_string):
    """Formate une date selon un format spécifique"""
    try:
        if hasattr(value, 'strftime'):
            return value.strftime(format_string)
        return value
    except:
        return value


@register.filter
def default_if_empty(value, default):
    """Retourne une valeur par défaut si la valeur est vide"""
    if not value or (isinstance(value, str) and value.strip() == ''):
        return default
    return value


@register.simple_tag
def field_value(current_values, field_id):
    """Tag pour récupérer la valeur d'un champ plus facilement"""
    if isinstance(current_values, dict):
        field_key = f'field_{field_id}'
        return current_values.get(field_key, '')
    return ''


@register.inclusion_tag('templates_app/templatetags/field_input.html')
def render_field_input(field, current_values=None):
    """Rendu d'un champ de formulaire dynamique"""
    field_value = ''
    if current_values and isinstance(current_values, dict):
        field_key = f'field_{field.id}'
        field_value = current_values.get(field_key, '')

    return {
        'field': field,
        'field_value': field_value,
    }
