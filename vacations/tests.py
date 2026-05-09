from datetime import date

from django.contrib.auth import get_user_model
from django.test import TestCase

from .models import Employee, VacationDecision, VacationRequest
from .pdf import build_decision_pdf, build_request_pdf


class VacationPdfTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='direccion', password='test-pass')
        self.employee = Employee.objects.create(first_name='Ana', last_name='López', department='Operaciones')

    def test_request_pdf_is_generated(self):
        request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 14),
            requested_days=10,
            created_by=self.user,
        )

        pdf = build_request_pdf(request)

        self.assertTrue(pdf.name.endswith('.pdf'))
        self.assertGreater(len(pdf.read()), 1000)

    def test_request_pdf_download_regenerates_document(self):
        vacation_request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 14),
            requested_days=10,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(f'/solicitudes/{vacation_request.pk}/pdf/solicitud/')

        vacation_request.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(vacation_request.request_pdf.name.endswith('.pdf'))

    def test_decision_pdf_is_generated(self):
        vacation_request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 14),
            requested_days=10,
            created_by=self.user,
        )
        decision = VacationDecision.objects.create(
            request=vacation_request,
            decision=VacationDecision.Decision.APPROVED,
            decided_by=self.user,
        )

        pdf = build_decision_pdf(decision)

        self.assertTrue(pdf.name.endswith('.pdf'))
        self.assertGreater(len(pdf.read()), 1000)

    def test_decision_pdf_download_regenerates_document(self):
        vacation_request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 14),
            requested_days=10,
            created_by=self.user,
        )
        VacationDecision.objects.create(
            request=vacation_request,
            decision=VacationDecision.Decision.APPROVED,
            decided_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get(f'/solicitudes/{vacation_request.pk}/pdf/decision/')

        vacation_request.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response['Content-Type'], 'application/pdf')
        self.assertIn('attachment;', response['Content-Disposition'])
        self.assertTrue(vacation_request.decision.decision_pdf.name.endswith('.pdf'))


class VacationCalendarTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='rrhh', password='test-pass')
        self.employee_a = Employee.objects.create(first_name='Ana', last_name='López')
        self.employee_b = Employee.objects.create(first_name='Luis', last_name='Pérez')

    def test_calendar_marks_overlap_days(self):
        VacationRequest.objects.create(
            employee=self.employee_a,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 7),
            requested_days=5,
            created_by=self.user,
        )
        VacationRequest.objects.create(
            employee=self.employee_b,
            start_date=date(2026, 8, 5),
            end_date=date(2026, 8, 10),
            requested_days=4,
            created_by=self.user,
        )
        self.client.force_login(self.user)

        response = self.client.get('/calendario/?year=2026&month=8')

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Agosto 2026')
        self.assertContains(response, 'Solape')
        self.assertEqual(response.context['overlap_days'], 3)
