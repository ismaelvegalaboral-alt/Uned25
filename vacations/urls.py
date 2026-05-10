from django.urls import path

from . import views
from . import push_views

urlpatterns = [
    path('notificaciones/', push_views.notification_settings, name='notification_settings'),
    path('push/public-key/', push_views.public_key, name='push_public_key'),
    path('push/subscribe/', push_views.subscribe, name='push_subscribe'),
    path('push/test/', push_views.test_notification, name='push_test'),
    path('', views.dashboard, name='dashboard'),
    path('trabajadores/', views.employee_list, name='employee_list'),
    path('trabajadores/nuevo/', views.employee_create, name='employee_create'),
    path('trabajadores/<int:pk>/', views.employee_detail, name='employee_detail'),
    path('calendario/', views.vacation_calendar, name='vacation_calendar'),
    path('solicitudes/', views.request_list, name='request_list'),
    path('solicitudes/nueva/', views.request_create, name='request_create'),
    path('solicitudes/<int:pk>/', views.request_detail, name='request_detail'),
    path('solicitudes/<int:pk>/pdf/solicitud/', views.request_pdf_download, name='request_pdf_download'),
    path('solicitudes/<int:pk>/pdf/decision/', views.decision_pdf_download, name='decision_pdf_download'),
    path('solicitudes/<int:pk>/resolver/', views.request_decide, name='request_decide'),
]
