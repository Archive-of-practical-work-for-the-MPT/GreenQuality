from prometheus_client.core import GaugeMetricFamily


class FlightsByStatusCollector:
    """
    Метрика для отслеживания количества рейсов по их статусам.
    Позволяет отслеживать распределение рейсов по различным состояниям:
    - Запланированные
    - В пути
    - Прибыли
    - Отменены
    - Задержаны
    """

    def collect(self):
        from django.db.models import Count
        from .models import Flight

        metric = GaugeMetricFamily(
            'airline_flights_by_status',
            'Количество рейсов по статусам',
            labels=['status']
        )

        # Получаем количество рейсов для каждого статуса
        flight_objects = Flight.objects  # type: ignore
        for row in flight_objects.values('status').annotate(count=Count('id_flight')):
            status = row['status'] if row['status'] else 'Не определен'
            metric.add_metric([status], float(row['count']))

        # Добавляем нулевые значения для статусов, которых нет в базе
        existing_statuses = {row['status']
                             for row in flight_objects.values('status')}
        all_possible_statuses = ['Запланирован',
                                 'В пути', 'Прибыл', 'Отменен', 'Задержан']

        for status in all_possible_statuses:
            if status not in existing_statuses:
                metric.add_metric([status], 0.0)

        yield metric


class TicketsByClassCollector:
    """
    Метрика для отслеживания количества проданных билетов по классам обслуживания.
    Позволяет анализировать популярность различных классов:
    - Эконом
    - Бизнес
    - Первый
    """

    def collect(self):
        from django.db.models import Count
        from .models import Ticket, Class

        metric = GaugeMetricFamily(
            'airline_tickets_by_class',
            'Количество проданных билетов по классам обслуживания',
            labels=['class_name']
        )

        # Получаем количество билетов для каждого класса обслуживания
        ticket_objects = Ticket.objects  # type: ignore
        ticket_counts = (ticket_objects
                         .select_related('class_id')
                         .values('class_id__class_name')
                         .annotate(count=Count('id_ticket')))

        for row in ticket_counts:
            class_name = row['class_id__class_name'] if row['class_id__class_name'] else 'Не определен'
            metric.add_metric([class_name], float(row['count']))

        # Добавляем нулевые значения для классов, по которым нет билетов
        existing_classes = {row['class_id__class_name']
                            for row in ticket_counts}
        class_objects = Class.objects  # type: ignore

        for cls in class_objects.all():
            if cls.class_name not in existing_classes:
                metric.add_metric([cls.class_name], 0.0)

        yield metric


class ProfitByFlightCollector:
    """
    Метрика для отслеживания дохода по каждому рейсу.
    Позволяет определить самые прибыльные направления и рейсы.
    """

    def collect(self):
        from django.db.models import Sum
        from .models import Ticket

        metric = GaugeMetricFamily(
            'airline_profit_by_flight',
            'Доход по каждому рейсу',
            labels=['flight_id', 'departure_airport', 'arrival_airport']
        )

        # Вычисляем общий доход для каждого рейса
        ticket_objects = Ticket.objects  # type: ignore
        profit_by_flight = (ticket_objects
                            .select_related('flight_id', 'flight_id__departure_airport_id', 'flight_id__arrival_airport_id')
                            .values(
                                'flight_id__id_flight',
                                'flight_id__departure_airport_id__id_airport',
                                'flight_id__arrival_airport_id__id_airport'
                            )
                            .annotate(total_revenue=Sum('price')))

        for row in profit_by_flight:
            flight_id = str(row['flight_id__id_flight'])
            departure = row['flight_id__departure_airport_id__id_airport'] if row[
                'flight_id__departure_airport_id__id_airport'] else 'Не определен'
            arrival = row['flight_id__arrival_airport_id__id_airport'] if row[
                'flight_id__arrival_airport_id__id_airport'] else 'Не определен'
            revenue = float(row['total_revenue']
                            ) if row['total_revenue'] else 0.0

            metric.add_metric([flight_id, departure, arrival], revenue)

        yield metric
