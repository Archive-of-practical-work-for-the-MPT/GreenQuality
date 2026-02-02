"""Шаблонные фильтры для отображения данных журнала аудита."""
import json
from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter
def json_pretty(value):
    """Форматирует dict/list в читаемый JSON для отображения в шаблоне."""
    if value is None:
        return mark_safe('<span class="audit-empty">—</span>')
    try:
        s = json.dumps(value, ensure_ascii=False, indent=2)
        escaped = s.replace('<', '&lt;').replace('>', '&gt;')
        return mark_safe('<pre class="audit-json">' + escaped + '</pre>')
    except (TypeError, ValueError):
        return str(value)
