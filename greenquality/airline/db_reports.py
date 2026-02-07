"""
Вызов процедур (функций) и представлений БД GreenQuality.
Используются: calc_flight_revenue, calc_flight_occupancy,
calc_user_payments_in_period, v_flights_report, v_airports_revenue_report,
v_audit_operations_report.
"""
from decimal import Decimal
from django.db import connection


def _run_scalar(sql, params=None):
    """Выполнить запрос и вернуть одно значение или None при ошибке."""
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params or [])
            row = cur.fetchone()
            return row[0] if row else None
    except Exception:
        return None


def _run_query(sql, params=None):
    """Выполнить запрос, вернуть список словарей (имена столбцов) или []."""
    try:
        with connection.cursor() as cur:
            cur.execute(sql, params or [])
            columns = [col[0] for col in cur.description]
            return [dict(zip(columns, row)) for row in cur.fetchall()]
    except Exception:
        return []


# --- Процедуры (расчёты) ---

def get_flight_revenue(flight_id):
    """Выручка по рейсу (руб.)."""
    result = _run_scalar("SELECT calc_flight_revenue(%s)", [flight_id])
    if result is not None:
        return Decimal(str(result))
    return Decimal('0')


def get_flight_occupancy(flight_id):
    """Загрузка рейса (%)."""
    result = _run_scalar("SELECT calc_flight_occupancy(%s)", [flight_id])
    if result is not None:
        return Decimal(str(result))
    return Decimal('0')


def get_user_payments_in_period(user_id, date_from, date_to):
    """Сумма завершённых платежей пользователя за период (руб.)."""
    sql = "SELECT calc_user_payments_in_period(%s, %s::timestamptz, %s::timestamptz)"
    result = _run_scalar(sql, [user_id, date_from, date_to])
    if result is not None:
        return Decimal(str(result))
    return Decimal('0')


# --- Представления (отчётность) ---

def get_flights_report(limit=None, flight_ids=None):
    """
    Отчёт по рейсам: id, аэропорты, время, статус, места, выручка.
    flight_ids — фильтр по id_flight; limit — макс. строк.
    """
    if flight_ids:
        placeholders = ','.join(['%s'] * len(flight_ids))
        sql = "SELECT * FROM v_flights_report WHERE id_flight IN (" + placeholders + ")"
        return _run_query(sql, list(flight_ids))
    sql = "SELECT * FROM v_flights_report"
    if limit:
        sql += f" LIMIT {int(limit)}"
    return _run_query(sql)


def get_airports_revenue_report():
    """Отчёт по выручке по аэропортам (вылеты/прилёты)."""
    return _run_query("SELECT * FROM v_airports_revenue_report")


def get_audit_operations_report():
    """Отчёт по операциям в журнале аудита (таблица, операция, кол-во)."""
    return _run_query("SELECT * FROM v_audit_operations_report")


def get_revenue_occupancy_for_flights(flight_ids):
    """
    Для списка id рейсов вернуть словарь {id_flight: (revenue, occupancy)}.
    """
    if not flight_ids:
        return {}
    try:
        with connection.cursor() as cur:
            ph = ','.join(['%s'] * len(flight_ids))
            cur.execute(
                "SELECT id_flight, calc_flight_revenue(id_flight) AS revenue, "
                "calc_flight_occupancy(id_flight) AS occupancy FROM flights "
                "WHERE id_flight IN (" + ph + ")",
                list(flight_ids)
            )
            return {
                row[0]: (Decimal(str(row[1] or 0)), Decimal(str(row[2] or 0)))
                for row in cur.fetchall()
            }
    except Exception:
        return {}
