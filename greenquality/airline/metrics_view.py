from django.http import HttpResponse


def prometheus_metrics_view(_request):
    from os import getenv
    from prometheus_client import multiprocess
    from prometheus_client import CollectorRegistry, CONTENT_TYPE_LATEST, generate_latest, REGISTRY

    if getenv('PROMETHEUS_MULTIPROC_DIR'):
        registry = CollectorRegistry()
        multiprocess.MultiProcessCollector(registry)
    else:
        registry = REGISTRY

    from .metrics import (
        FlightsByStatusCollector,
        TicketsByClassCollector,
        ProfitByFlightCollector
    )

    try:
        registry.register(FlightsByStatusCollector())
        registry.register(TicketsByClassCollector())
        registry.register(ProfitByFlightCollector())
    except ValueError as e:
        if 'Duplicated timeseries' not in str(e):
            raise

    output = generate_latest(registry)
    return HttpResponse(output, content_type=CONTENT_TYPE_LATEST)
