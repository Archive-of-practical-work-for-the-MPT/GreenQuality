"""
Преобразование исключений в понятные пользователю сообщения на русском.
Технические детали (str(e)) конечному пользователю не показываем.
"""
from django.db import IntegrityError
from django.core.exceptions import ValidationError, PermissionDenied
from django.http import Http404
from decimal import DecimalException


# Сообщения по контексту (действие пользователя) — можно передавать context='create' и т.д.
CONTEXT_MESSAGES = {
    'create': 'Не удалось сохранить запись. Проверьте введённые данные.',
    'update': 'Не удалось обновить запись. Проверьте введённые данные.',
    'delete': 'Не удалось удалить запись.',
    'save': 'Не удалось сохранить данные. Проверьте введённые значения.',
    'login': 'Не удалось войти. Проверьте email и пароль.',
    'register': 'Не удалось завершить регистрацию. Проверьте данные формы.',
    'export': 'Не удалось сформировать отчёт. Попробуйте позже.',
    'load': 'Не удалось загрузить данные.',
}


def get_user_friendly_message(exception, context=None):
    """
    Возвращает понятное сообщение на русском для переданного исключения.
    context — необязательно: 'create', 'update', 'delete', 'save', 'login',
    'register', 'export', 'load'.
    """
    if exception is None:
        return 'Произошла ошибка.'

    exc_type = type(exception)

    # Ошибки целостности БД (дубликаты, внешние ключи и т.д.)
    if exc_type is IntegrityError:
        return (
            'Такие данные уже есть или они противоречат правилам. '
            'Проверьте введённые значения и попробуйте снова.'
        )

    # Валидация Django — по возможности используем сообщение из исключения
    if exc_type is ValidationError:
        if hasattr(exception, 'message_dict') and exception.message_dict:
            parts = []
            for field, messages_list in exception.message_dict.items():
                if isinstance(messages_list, list):
                    parts.extend(messages_list)
                else:
                    parts.append(str(messages_list))
            if parts:
                return ' '.join(parts[:3])  # Не более 3 сообщений
        if getattr(exception, 'messages', None):
            first = list(exception.messages)[0] if exception.messages else None
            return first or CONTEXT_MESSAGES.get(context, 'Проверьте введённые данные.')
        return 'Проверьте введённые данные.'

    # Нет доступа
    if exc_type is PermissionDenied:
        return 'У вас нет прав для этого действия.'

    # Страница не найдена
    if exc_type is Http404:
        return 'Запрашиваемая страница не найдена.'

    # Ошибки типов и значений (дата, число и т.д.)
    if exc_type in (ValueError, TypeError, DecimalException):
        return 'Неверный формат данных. Проверьте введённые значения.'

    # DoesNotExist — общее для всех моделей
    bases = getattr(exc_type, '__bases__', None)
    if exc_type.__name__ == 'DoesNotExist' or (
            bases and any(b.__name__ == 'DoesNotExist' for b in bases)):
        return 'Запись не найдена.'

    # Для любых других исключений — общее сообщение или по контексту
    default = (
        'Произошла непредвиденная ошибка. '
        'Попробуйте позже или обратитесь в поддержку.'
    )
    return CONTEXT_MESSAGES.get(context, default)
