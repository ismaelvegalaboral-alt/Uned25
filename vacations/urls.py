from django.urls import path

from . import views
from . import daily_job_plan_views
from . import customer_delivery_note_views
from . import daily_report_views
from . import file_views
from . import push_views

urlpatterns = [
    path('faena/', daily_job_plan_views.daily_job_plan_list, name='daily_job_plan_list'),
    path('faena/nueva/', daily_job_plan_views.daily_job_plan_create, name='daily_job_plan_create'),
    path('faena/<int:pk>/', daily_job_plan_views.daily_job_plan_detail, name='daily_job_plan_detail'),
    path('faena/<int:pk>/publicar/', daily_job_plan_views.daily_job_plan_publish, name='daily_job_plan_publish'),
    path('faena/<int:plan_pk>/linea/nueva/', daily_job_plan_views.daily_job_assignment_create, name='daily_job_assignment_create'),
    path('faena/<int:plan_pk>/estado/nuevo/', daily_job_plan_views.daily_job_status_create, name='daily_job_status_create'),
    path('faena/panel/', daily_job_plan_views.daily_job_panel, name='daily_job_panel'),
    path('faena/<int:pk>/copiar/', daily_job_plan_views.daily_job_plan_copy, name='daily_job_plan_copy'),
    path('faena/<int:pk>/ocultar/', daily_job_plan_views.daily_job_plan_unpublish, name='daily_job_plan_unpublish'),
    path('faena/<int:pk>/csv/', daily_job_plan_views.daily_job_plan_csv, name='daily_job_plan_csv'),
    path('faena/<int:pk>/excel/', daily_job_plan_views.daily_job_plan_excel, name='daily_job_plan_excel'),
    path('faena/linea/<int:pk>/editar/', daily_job_plan_views.daily_job_assignment_edit, name='daily_job_assignment_edit'),
    path('faena/linea/<int:pk>/eliminar/', daily_job_plan_views.daily_job_assignment_delete, name='daily_job_assignment_delete'),
    path('faena/estado/<int:pk>/editar/', daily_job_plan_views.daily_job_status_edit, name='daily_job_status_edit'),
    path('faena/estado/<int:pk>/eliminar/', daily_job_plan_views.daily_job_status_delete, name='daily_job_status_delete'),
    path('mi-faena/', daily_job_plan_views.daily_job_my_assignments, name='daily_job_my_assignments'),
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
