from django.urls import path
from . import views

urlpatterns = [
    # ------------------------
    # Appointment booking flow
    # ------------------------
    path('', views.step1, name='step1'),
    path('step2/', views.step2, name='step2'),
    path('success/', views.success, name='success'),

    # ------------------------
    # Reschedule functionality
    # ------------------------
    path('reschedule/<str:token>/', views.reschedule_appointment, name='reschedule_appointment'),

    # ------------------------
    # Receptionist authentication
    # ------------------------
    path('receptionist/register/', views.receptionist_register, name='receptionist_register'),
    path('receptionist/login/', views.receptionist_login, name='receptionist_login'),
    path('receptionist/logout/', views.receptionist_logout, name='receptionist_logout'),

    # ------------------------
    # Receptionist dashboard
    # ------------------------
    path('dashboard/', views.dashboard, name='dashboard'),

    # ------------------------
    # Admin functionality
    # ------------------------

    # Admin auth & approval
    path('admin-login/', views.admin_login, name='admin_login'),
    path('admin-logout/', views.admin_logout, name='admin_logout'),
    path('approval/', views.approval_page, name='approval_page'),
    path('approve/<int:pk>/', views.approve_receptionist, name='approve_receptionist'),
    path('reject/<int:pk>/', views.reject_receptionist, name='reject_receptionist'),

    # ------------------------
    # API endpoints
    # ------------------------
    path('get_appointments/', views.get_appointments, name='get_appointments'),
    path('update_appointment_status/', views.update_appointment_status, name='update_appointment_status'),
]
