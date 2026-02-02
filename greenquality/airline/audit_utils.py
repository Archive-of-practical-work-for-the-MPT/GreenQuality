"""
Утилиты для записи в журнал аудита: кто/когда/что изменил, данные до и после.
"""
from django.db import models

from .models import AuditLog, Account


def model_instance_to_audit_dict(instance):
    """
    Преобразует экземпляр модели в словарь для old_data/new_data.
    Исключает пароль, ForeignKey представляются как pk.
    """
    if instance is None:
        return None
    result = {}
    for field in instance._meta.get_fields():
        if not hasattr(instance, field.name):
            continue
        if field.name == 'password':
            continue
        value = getattr(instance, field.name)
        if value is None:
            result[field.name] = None
        elif hasattr(value, 'pk'):
            result[field.name] = value.pk
        elif hasattr(value, 'isoformat'):
            result[field.name] = value.isoformat()
        elif isinstance(value, (models.Model,)):
            result[field.name] = value.pk
        else:
            result[field.name] = str(value)
    return result


def get_record_id_for_audit(instance):
    """
    Возвращает record_id для AuditLog. Для целочисленных PK — значение pk,
    для строковых (напр. Airport) — 0 (реальный id в old_data/new_data).
    """
    pk = getattr(instance, instance._meta.pk.name)
    if isinstance(pk, int):
        return pk
    return 0


def log_audit(table_name, record_id, operation, changed_by_account_id, old_data=None, new_data=None):
    """
    Записывает запись в журнал аудита.

    :param table_name: имя таблицы/модели (напр. 'User', 'Flight')
    :param record_id: id записи (int; для строковых PK — 0)
    :param operation: 'INSERT', 'UPDATE' или 'DELETE'
    :param changed_by_account_id: id_account пользователя (или None)
    :param old_data: данные до изменения (dict; для INSERT — None)
    :param new_data: данные после изменения (dict; для DELETE — None)
    """
    try:
        changed_by = None
        if changed_by_account_id:
            try:
                changed_by = Account.objects.get(id_account=changed_by_account_id)
            except Account.DoesNotExist:
                pass
        AuditLog.objects.create(
            table_name=table_name,
            record_id=record_id,
            operation=operation,
            old_data=old_data,
            new_data=new_data,
            changed_by=changed_by,
        )
    except Exception:
        pass  # не ломаем основную операцию при ошибке аудита
