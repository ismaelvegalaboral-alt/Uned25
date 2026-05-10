from django.conf import settings
from django.db import models
from django.urls import reverse


class Employee(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        related_name='employee_profile',
        null=True,
        blank=True,
        verbose_name='usuario vinculado',
        help_text='Opcional. Permite que el trabajador acceda solo a sus propias solicitudes.',
    )
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


    @property
    def absence_type_label(self):
        return self.get_absence_type_display()

    @property
    def has_supporting_document(self):
        return bool(self.supporting_document)

    def get_absolute_url(self):
        return reverse('employee_detail', args=[self.pk])


class VacationRequest(models.Model):
    class AbsenceType(models.TextChoices):
        VACATION = 'vacaciones', 'Vacaciones'
        MEDICAL_APPOINTMENT = 'cita_medica', 'Cita médica'
        SICK_LEAVE = 'baja_medica', 'Baja médica'
        JUSTIFIED_ABSENCE = 'ausencia_justificada', 'Ausencia justificada'
        PERSONAL_DAYS = 'asuntos_propios', 'Asuntos propios'
        PAID_LEAVE = 'permiso_retribuido', 'Permiso retribuido'
        TELEWORK = 'teletrabajo_puntual', 'Teletrabajo puntual'
        TRAINING = 'formacion', 'Formación'
        OTHER = 'otros', 'Otros'

    class Status(models.TextChoices):
        DRAFT = 'draft', 'Borrador'
        PENDING = 'pending', 'Pendiente de dirección'
        APPROVED = 'approved', 'Aprobada'
        REJECTED = 'rejected', 'Denegada'
        CANCELLED = 'cancelled', 'Cancelada'

    employee = models.ForeignKey(Employee, on_delete=models.CASCADE, related_name='requests', verbose_name='trabajador')
    absence_type = models.CharField(
        'tipo de ausencia',
        max_length=40,
        choices=AbsenceType.choices,
        default=AbsenceType.VACATION,
    )
    supporting_document = models.FileField(
        'justificante',
        upload_to='absence_documents/',
        blank=True,
        null=True,
    )
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

class PushSubscription(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='push_subscriptions',
    )
    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.TextField()
    auth = models.TextField()
    user_agent = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-updated_at']
        verbose_name = 'suscripción push'
        verbose_name_plural = 'suscripciones push'

    def __str__(self):
        return f'{self.user} · {self.endpoint[:60]}'

# Compatibilidad: etiqueta legible del tipo de ausencia
if not hasattr(VacationRequest, "absence_type_label"):
    VacationRequest.absence_type_label = property(
        lambda self: self.get_absence_type_display()
    )

if not hasattr(VacationRequest, "has_supporting_document"):
    VacationRequest.has_supporting_document = property(
        lambda self: bool(self.supporting_document)
    )

class AuditLog(models.Model):
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='audit_logs',
        verbose_name='usuario',
    )
    action = models.CharField('acción', max_length=80)
    model_name = models.CharField('modelo', max_length=120, blank=True)
    object_id = models.CharField('ID objeto', max_length=120, blank=True)
    object_repr = models.CharField('objeto', max_length=255, blank=True)
    metadata = models.JSONField('metadatos', default=dict, blank=True)
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    user_agent = models.TextField('user agent', blank=True)
    created_at = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'registro de auditoría'
        verbose_name_plural = 'registros de auditoría'

    def __str__(self):
        actor = self.actor or 'sistema'
        return f'{self.created_at:%Y-%m-%d %H:%M} · {actor} · {self.action}'

class LoginAttempt(models.Model):
    ip_address = models.GenericIPAddressField('IP', null=True, blank=True)
    username = models.CharField('usuario/email', max_length=255, blank=True)
    path = models.CharField('ruta', max_length=255, blank=True)
    success = models.BooleanField('correcto', default=False)
    blocked = models.BooleanField('bloqueado', default=False)
    user_agent = models.TextField('user agent', blank=True)
    created_at = models.DateTimeField('fecha', auto_now_add=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'intento de login'
        verbose_name_plural = 'intentos de login'
        indexes = [
            models.Index(fields=['ip_address', 'created_at']),
            models.Index(fields=['username', 'created_at']),
            models.Index(fields=['success', 'created_at']),
        ]

    def __str__(self):
        result = 'OK' if self.success else 'KO'
        if self.blocked:
            result = 'BLOQUEADO'
        return f'{self.created_at:%Y-%m-%d %H:%M} · {self.ip_address} · {self.username} · {result}'
