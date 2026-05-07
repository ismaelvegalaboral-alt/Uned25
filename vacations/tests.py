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
