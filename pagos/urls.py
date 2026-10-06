from django.urls import path

from . import views

urlpatterns = [
    path("api/v1/pagos/primas", views.primas),
    path("api/v1/pagos/primas/poliza/<uuid:id>", views.primas_por_poliza),
    path("api/v1/pagos/indemnizaciones", views.indemnizaciones),
    path("api/v1/pagos/indemnizaciones/siniestro/<uuid:id>", views.indemnizaciones_por_siniestro),
]
