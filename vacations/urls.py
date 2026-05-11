from django.urls import path

from . import views
from . import customer_delivery_note_views
from . import daily_report_views
from . import file_views
from . import push_views

urlpatterns = [
    path('albaranes/', customer_delivery_note_views.customer_delivery_note_list, name='customer_delivery_note_list'),
    path('albaranes/nuevo/', customer_delivery_note_views.customer_delivery_note_create, name='customer_delivery_note_create'),
    path('albaranes/<int:pk>/', customer_delivery_note_views.customer_delivery_note_detail, name='customer_delivery_note_detail'),
    path('albaranes/<int:pk>/pdf/', customer_delivery_note_views.customer_delivery_note_pdf, name='customer_delivery_note_pdf'),
    path('partes/', daily_report_views.daily_report_list, name='daily_report_list'),
    path('partes/nuevo/', daily_report_views.daily_report_create, name='daily_report_create'),
    path('partes/<int:pk>/', daily_report_views.daily_report_detail, name='daily_report_detail'),
    path('partes/<int:pk>/pdf/', daily_report_views.daily_report_pdf, name='daily_report_pdf'),
    path('solicitudes/<int:pk>/justificante/', file_views.supporting_document_download, name='supporting_document_download'),
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
