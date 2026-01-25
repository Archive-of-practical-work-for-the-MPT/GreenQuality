from django.urls import path
from . import views

urlpatterns = [
    path('', views.index, name='index'),
    path('about/', views.about, name='about'),
    path('contacts/', views.contacts, name='contacts'),
    path('flights/', views.flights, name='flights'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    path('profile/', views.profile_view, name='profile'),
    path('buy-ticket/<int:flight_id>/', views.buy_ticket, name='buy_ticket'),
    path('buy-ticket/<int:flight_id>/seat/', views.buy_ticket_seat, name='buy_ticket_seat'),
    path('buy-ticket/<int:flight_id>/confirm/', views.buy_ticket_confirm, name='buy_ticket_confirm'),
    path('admin-panel/', views.admin_panel, name='admin_panel'),
    path('admin-panel/crud/', views.admin_crud, name='admin_crud'),
    path('admin-panel/get-record/', views.admin_get_record, name='admin_get_record'),
    path('admin-panel/get-options/', views.admin_get_options, name='admin_get_options'),
    path('profile/export/<str:format_type>/', views.export_statistics, name='export_statistics'),
]
