from django.urls import path
from pagos.views import (
    health,
    primas,
    primas_por_poliza,
    indemnizaciones,
    indemnizaciones_por_siniestro,
)

urlpatterns = [
    path("health", health),
    path("api/v1/pagos/primas", primas),
    path("api/v1/pagos/primas/poliza/<uuid:id>", primas_por_poliza),
    path("api/v1/pagos/indemnizaciones", indemnizaciones),
    path("api/v1/pagos/indemnizaciones/siniestro/<uuid:id>", indemnizaciones_por_siniestro),
]
