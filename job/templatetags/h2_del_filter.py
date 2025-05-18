from django import template
import re

register = template.Library()

@register.filter
def remove_first_h2(value):
    """Удаляет первый тег <h2>...</h2> из строки"""
    return re.sub(r'<h2[^>]*>.*?</h2>', '', value, count=1, flags=re.DOTALL)