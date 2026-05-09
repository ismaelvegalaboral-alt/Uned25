from datetime import date, timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.test import TestCase
from django.utils import timezone

from .models import Employee, VacationDecision, VacationRequest
from .pdf import build_decision_pdf, build_request_pdf
from .permissions import GROUP_DIRECTION, GROUP_HR, GROUP_WORKER
from .services import business_days_between, evaluate_request


class VacationPdfTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='direccion', password='test-pass')
        self.employee = Employee.objects.create(
            first_name='Ana',
            last_name='López',
            department='Operaciones',
            national_id='12345678Z',
        )

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
        self.user.groups.add(Group.objects.create(name=GROUP_HR))
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
        self.user.groups.add(Group.objects.create(name=GROUP_DIRECTION))
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
        self.user.groups.add(Group.objects.create(name=GROUP_HR))
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


class VacationPolicyReviewTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(username='rrhh', password='test-pass')
        self.employee = Employee.objects.create(
            first_name='Ismael',
            last_name='Vega',
            department='Administración',
            annual_days=22,
            national_id='00000000T',
        )

    def test_business_days_between_counts_weekdays_only(self):
        self.assertEqual(business_days_between(date(2026, 8, 3), date(2026, 8, 9)), 5)

    def test_review_flags_low_notice_and_department_overlap(self):
        start = timezone.localdate() + timedelta(days=3)
        end = start + timedelta(days=4)
        colleague = Employee.objects.create(
            first_name='Marta',
            last_name='García',
            department='Administración',
            annual_days=22,
            national_id='11111111H',
        )
        VacationRequest.objects.create(
            employee=colleague,
            start_date=start,
            end_date=end,
            requested_days=3,
            status=VacationRequest.Status.APPROVED,
            created_by=self.user,
        )
        vacation_request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=start,
            end_date=end,
            requested_days=3,
            created_by=self.user,
        )

        review = evaluate_request(vacation_request)

        self.assertTrue(review.has_flags)
        self.assertEqual(review.approved_overlap_count, 1)
        self.assertIn(review.severity, ['warning', 'critical'])


class RolePermissionTests(TestCase):
    def setUp(self):
        User = get_user_model()
        self.hr = User.objects.create_user(username='rrhh', password='test-pass')
        self.direction = User.objects.create_user(username='direccion', password='test-pass')
        self.worker_user = User.objects.create_user(username='trabajador', password='test-pass')
        self.other_worker_user = User.objects.create_user(username='otro', password='test-pass')

        self.hr.groups.add(Group.objects.create(name=GROUP_HR))
        self.direction.groups.add(Group.objects.create(name=GROUP_DIRECTION))
        self.worker_user.groups.add(Group.objects.create(name=GROUP_WORKER))
        self.other_worker_user.groups.add(Group.objects.get(name=GROUP_WORKER))

        self.employee = Employee.objects.create(
            user=self.worker_user,
            first_name='Ismael',
            last_name='Vega',
            department='Administración',
            annual_days=22,
        )
        self.other_employee = Employee.objects.create(
            user=self.other_worker_user,
            first_name='Otra',
            last_name='Persona',
            department='Administración',
            annual_days=22,
        )
        self.request = VacationRequest.objects.create(
            employee=self.employee,
            start_date=date(2026, 8, 3),
            end_date=date(2026, 8, 7),
            requested_days=5,
            created_by=self.hr,
        )

    def test_worker_can_view_own_request(self):
        self.client.force_login(self.worker_user)
        response = self.client.get(f'/solicitudes/{self.request.pk}/')
        self.assertEqual(response.status_code, 200)

    def test_worker_cannot_view_calendar(self):
        self.client.force_login(self.worker_user)
        response = self.client.get('/calendario/')
        self.assertEqual(response.status_code, 403)

    def test_worker_cannot_view_other_worker_request(self):
        other_request = VacationRequest.objects.create(
            employee=self.other_employee,
            start_date=date(2026, 9, 1),
            end_date=date(2026, 9, 4),
            requested_days=4,
            created_by=self.hr,
        )
        self.client.force_login(self.worker_user)
        response = self.client.get(f'/solicitudes/{other_request.pk}/')
        self.assertEqual(response.status_code, 403)

    def test_direction_can_resolve_request(self):
        self.client.force_login(self.direction)
        response = self.client.get(f'/solicitudes/{self.request.pk}/resolver/')
        self.assertEqual(response.status_code, 200)

    def test_hr_cannot_resolve_request_by_default(self):
        self.client.force_login(self.hr)
        response = self.client.get(f'/solicitudes/{self.request.pk}/resolver/')
        self.assertEqual(response.status_code, 403)
