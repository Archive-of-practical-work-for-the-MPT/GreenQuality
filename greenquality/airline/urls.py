from django.urls import path, include
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('control-panel/', views.control_panel, name='control_panel'),
    path('crud/<str:model_name>/', views.crud_interface, name='crud_interface'),
    path('auth/', include('airline.auth_urls', namespace='auth')),
]
