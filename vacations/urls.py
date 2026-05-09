from django.urls import path

from . import views

urlpatterns = [
    path('', views.dashboard, name='dashboard'),
    path('trabajadores/', views.employee_list, name='employee_list'),
    path('trabajadores/nuevo/', views.employee_create, name='employee_create'),
    path('trabajadores/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('calendario/', views.vacation_calendar, name='vacation_calendar'),
    path('solicitudes/', views.request_list, name='request_list'),
    path('solicitudes/nueva/', views.request_create, name='request_create'),
    path('solicitudes/<int:pk>/', views.request_detail, name='request_detail'),
    path('solicitudes/<int:pk>/resolver/', views.request_decide, name='request_decide'),
]
