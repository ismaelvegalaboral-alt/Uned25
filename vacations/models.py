from django.conf import settings
from django.db import models
from django.urls import reverse


class Employee(models.Model):
    first_name = models.CharField('nombre', max_length=120)
    last_name = models.CharField('apellidos', max_length=160)
    national_id = models.CharField('DNI/NIE', max_length=20, blank=True)
    email = models.EmailField('email', blank=True)
    department = models.CharField('departamento', max_length=120, blank=True)
    position = models.CharField('puesto', max_length=120, blank=True)
    annual_days = models.PositiveSmallIntegerField('días anuales', default=22)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['last_name', 'first_name']
        verbose_name = 'trabajador'
        verbose_name_plural = 'trabajadores'

    def __str__(self) -> str:
        return self.full_name

    @property
    def full_name(self) -> str:
        return f'{self.first_name} {self.last_name}'.strip()

    def get_absolute_url(self):
        return reverse('employee_detail', args=[self.pk])


class VacationRequest(models.Model):
    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PENDING = 'pending', 'Pendiente de dirección'
        APPROVED = 'approved', 'Aprobada'
        REJECTED = 'rejected', 'Denegada'
        CANCELLED = 'cancelled', 'Cancelada'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='requests', verbose_name='trabajador')
    start_date = models.DateField('fecha de inicio')
    end_date = models.DateField('fecha de fin')
    requested_days = models.DecimalField('días solicitados', max_digits=5, decimal_places=1)
    notes = models.TextField('observaciones del trabajador', blank=True)
    status = models.CharField('estado', max_length=20, choices=Status.choices, default=Status.PENDING)
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='created_vacation_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    request_pdf = models.FileField('PDF solicitud', upload_to='vacation_documents/', blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'solicitud de vacaciones'
        verbose_name_plural = 'solicitudes de vacaciones'

    def __str__(self) -> str:
        return f'{self.employee} · {self.start_date:%d/%m/%Y} - {self.end_date:%d/%m/%Y}'

    def get_absolute_url(self):
        return reverse('request_detail', args=[self.pk])


class VacationDecision(models.Model):
    class Decision(models.TextChoices):
        APPROVED = 'approved', 'Aprobada'
        REJECTED = 'rejected', 'Denegada'

    request = models.OneToOneField(VacationRequest, on_delete=models.CASCADE, related_name='decision', verbose_name='solicitud')
    decision = models.CharField('decisión', max_length=20, choices=Decision.choices)
    decided_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='vacation_decisions')
    decided_at = models.DateTimeField(auto_now_add=True)
    company_notes = models.TextField('observaciones de dirección', blank=True)
    decision_pdf = models.FileField('PDF decisión', upload_to='vacation_documents/', blank=True)

    class Meta:
        ordering = ['-decided_at']
        verbose_name = 'decisión de vacaciones'
        verbose_name_plural = 'decisiones de vacaciones'

    def __str__(self) -> str:
        return f'{self.get_decision_display()} · {self.request}'
