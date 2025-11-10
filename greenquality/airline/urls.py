from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('auth/', include('airline.auth_urls', namespace='auth')),
]
