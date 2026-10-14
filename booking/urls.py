from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='home'),
    path('register/', views.register, name='register'),
    
    # Замените views.user_login на то название, которое у вас в views.py
    # Например, views.login_view или views.login
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    
    path('profile/', views.profile, name='profile'),
    path('main/', views.main, name='main'),
    path('booking/confirm/<int:slot_id>/<int:service_id>/', views.booking_confirm_view, name='booking_confirm'),
    path('booking/success/<int:appointment_id>/', views.booking_success, name='booking_success'),
    path('search-slots/', views.search_slots, name='search_slots'),
    path('contacts/', views.contacts, name='contacts'),
    path('appointments/', views.appointments, name='appointments'),
    path('appointments/<int:appointment_id>/cancel/', views.cancel_appointment, name='cancel_appointment'),
    path('appointments/cancel/<int:appointment_id>/', views.cancel_appointment, name='cancel_appointment'),
    path('profile/update-phone/', views.update_phone, name='update_phone'),
]