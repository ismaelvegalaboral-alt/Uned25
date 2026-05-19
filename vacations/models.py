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

class DailyWorkReport(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='daily_work_reports',
        verbose_name='trabajador',
    )
    report_date = models.DateField('fecha')
    machine_number = models.CharField('máquina nº', max_length=80, blank=True)
    truck_number = models.CharField('camión nº', max_length=80, blank=True)
    other_equipment = models.CharField('otros', max_length=255, blank=True)

    client_1 = models.CharField('cliente 1', max_length=255, blank=True)
    client_2 = models.CharField('cliente 2', max_length=255, blank=True)
    client_3 = models.CharField('cliente 3', max_length=255, blank=True)
    client_4 = models.CharField('cliente 4', max_length=255, blank=True)

    worksite_1 = models.CharField('obra 1', max_length=255, blank=True)
    worksite_2 = models.CharField('obra 2', max_length=255, blank=True)
    worksite_3 = models.CharField('obra 3', max_length=255, blank=True)
    worksite_4 = models.CharField('obra 4', max_length=255, blank=True)

    hours = models.CharField('horas', max_length=80, blank=True)
    trips = models.CharField('viajes', max_length=80, blank=True)
    other_notes = models.CharField('otros', max_length=255, blank=True)

    supplied_material = models.TextField('material suministrado', blank=True)
    work_performed = models.TextField('trabajos realizados', blank=True)

    worker_name = models.CharField('nombre del trabajador', max_length=255)
    signature_name = models.CharField('firma', max_length=255, blank=True)

    pdf = models.FileField('PDF generado', upload_to='daily_work_reports/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_daily_work_reports',
        verbose_name='creado por',
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ['-report_date', '-created_at']
        verbose_name = 'parte personal diario'
        verbose_name_plural = 'partes personales diarios'

    def __str__(self):
        return f'{self.worker_name} · {self.report_date:%d/%m/%Y}'

class CustomerDeliveryNote(models.Model):
    employee = models.ForeignKey(
        Employee,
        on_delete=models.CASCADE,
        related_name='customer_delivery_notes',
        verbose_name='trabajador',
    )
    note_date = models.DateField('fecha')

    customer_name = models.CharField('cliente', max_length=255)
    phone = models.CharField('teléfono', max_length=80, blank=True)
    tax_id = models.CharField('CIF/NIF', max_length=80, blank=True)
    worksite = models.CharField('obra', max_length=255, blank=True)
    address = models.CharField('dirección', max_length=255, blank=True)

    machine_1 = models.CharField('máquina 1', max_length=255, blank=True)
    machine_1_hours = models.CharField('horas máquina 1', max_length=80, blank=True)
    machine_2 = models.CharField('máquina 2', max_length=255, blank=True)
    machine_2_hours = models.CharField('horas máquina 2', max_length=80, blank=True)

    truck_1 = models.CharField('camión 1', max_length=255, blank=True)
    truck_1_hours = models.CharField('horas camión 1', max_length=80, blank=True)
    truck_1_trips = models.CharField('viajes camión 1', max_length=80, blank=True)
    truck_2 = models.CharField('camión 2', max_length=255, blank=True)
    truck_2_hours = models.CharField('horas camión 2', max_length=80, blank=True)
    truck_2_trips = models.CharField('viajes camión 2', max_length=80, blank=True)
    truck_3 = models.CharField('camión 3', max_length=255, blank=True)
    truck_3_hours = models.CharField('horas camión 3', max_length=80, blank=True)
    truck_3_trips = models.CharField('viajes camión 3', max_length=80, blank=True)
    truck_4 = models.CharField('camión 4', max_length=255, blank=True)
    truck_4_hours = models.CharField('horas camión 4', max_length=80, blank=True)
    truck_4_trips = models.CharField('viajes camión 4', max_length=80, blank=True)
    truck_5 = models.CharField('camión 5', max_length=255, blank=True)
    truck_5_hours = models.CharField('horas camión 5', max_length=80, blank=True)
    truck_5_trips = models.CharField('viajes camión 5', max_length=80, blank=True)

    work_description = models.TextField('descripción de trabajos realizados', blank=True)
    materials = models.TextField('otros conceptos o materiales', blank=True)
    observations = models.TextField('observaciones', blank=True)

    received_by = models.CharField('recibí conforme', max_length=255, blank=True)
    signature_image = models.FileField('firma cliente', upload_to='customer_delivery_notes/signatures/', blank=True, null=True)
    pdf = models.FileField('PDF generado', upload_to='customer_delivery_notes/', blank=True, null=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_customer_delivery_notes',
        verbose_name='creado por',
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ['-note_date', '-created_at']
        verbose_name = 'albarán de cliente'
        verbose_name_plural = 'albaranes de cliente'

    def __str__(self):
        return f'{self.customer_name} · {self.note_date:%d/%m/%Y}'

class DailyJobPlan(models.Model):
    plan_date = models.DateField('fecha de faena', unique=True)
    title = models.CharField('título', max_length=255, blank=True)
    notes = models.TextField('notas generales', blank=True)
    is_published = models.BooleanField('publicada para trabajadores', default=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_daily_job_plans',
        verbose_name='creada por',
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ['-plan_date']
        verbose_name = 'faena diaria'
        verbose_name_plural = 'faenas diarias'

    def __str__(self):
        return self.title or f'Faena {self.plan_date:%d/%m/%Y}'


class DailyJobAssignment(models.Model):
    CATEGORY_WORK = 'work'
    CATEGORY_MAINTENANCE = 'maintenance'
    CATEGORY_WORKSHOP = 'workshop'
    CATEGORY_TRAINING = 'training'
    CATEGORY_STOPPED = 'stopped'
    CATEGORY_SUBCONTRACTED = 'subcontracted'
    CATEGORY_OTHER = 'other'

    CATEGORY_CHOICES = [
        (CATEGORY_WORK, 'Trabajo/obra'),
        (CATEGORY_MAINTENANCE, 'Mantenimiento'),
        (CATEGORY_WORKSHOP, 'Taller/ITV'),
        (CATEGORY_TRAINING, 'Formación'),
        (CATEGORY_STOPPED, 'Parado'),
        (CATEGORY_SUBCONTRACTED, 'Subcontratado/alquilado'),
        (CATEGORY_OTHER, 'Varios'),
    ]

    plan = models.ForeignKey(DailyJobPlan, on_delete=models.CASCADE, related_name='assignments', verbose_name='faena')
    category = models.CharField('tipo', max_length=30, choices=CATEGORY_CHOICES, default=CATEGORY_WORK)
    client = models.CharField('cliente', max_length=255, blank=True)
    worksite = models.CharField('obra/zona', max_length=255, blank=True)
    machine = models.CharField('máquina', max_length=255, blank=True)
    truck = models.CharField('camión', max_length=255, blank=True)

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='daily_job_assignments',
        verbose_name='trabajador',
    )
    worker_name = models.CharField('nombre del trabajador', max_length=255, blank=True)
    hours = models.CharField('horas previstas', max_length=80, blank=True)
    trips = models.CharField('viajes previstos', max_length=80, blank=True)
    notes = models.TextField('observaciones', blank=True)
    sort_order = models.PositiveIntegerField('orden', default=0)

    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ['sort_order', 'client', 'worksite', 'machine', 'truck', 'worker_name']
        verbose_name = 'línea de faena'
        verbose_name_plural = 'líneas de faena'

    def __str__(self):
        worker = self.worker_name or (self.employee.full_name if self.employee else 'Sin trabajador')
        target = self.worksite or self.client or self.machine or self.truck or self.get_category_display()
        return f'{worker} · {target}'

    def save(self, *args, **kwargs):
        if self.employee and not self.worker_name:
            self.worker_name = self.employee.full_name
        super().save(*args, **kwargs)


class DailyJobStatusEntry(models.Model):
    STATUS_CHOICES = [
        ('vacation', 'Vacaciones'),
        ('personal_leave', 'Asuntos propios'),
        ('sick_leave', 'Baja médica/enfermo'),
        ('medical_check', 'Reconocimiento'),
        ('maintenance', 'Mantenimiento'),
        ('workshop', 'Taller/ITV'),
        ('training', 'Formación'),
        ('stopped', 'Parado'),
        ('subcontracted', 'Subcontratado/alquilado'),
        ('various', 'Varios'),
    ]

    plan = models.ForeignKey(DailyJobPlan, on_delete=models.CASCADE, related_name='status_entries', verbose_name='faena')
    status_type = models.CharField('estado', max_length=40, choices=STATUS_CHOICES)
    text = models.TextField('detalle')
    sort_order = models.PositiveIntegerField('orden', default=0)
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        ordering = ['status_type', 'sort_order', 'text']
        verbose_name = 'estado de faena'
        verbose_name_plural = 'estados de faena'

    def __str__(self):
        return f'{self.get_status_type_display()}: {self.text[:60]}'

class PlatformFeaturePermission(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feature_permissions',
        verbose_name='usuario',
    )
    can_use_vacations = models.BooleanField('vacaciones/ausencias', default=True)
    can_use_daily_reports = models.BooleanField('partes personales', default=True)
    can_use_customer_delivery_notes = models.BooleanField('albaranes de cliente', default=True)
    can_use_daily_jobs = models.BooleanField('faena diaria', default=True)
    can_use_work_orders = models.BooleanField('órdenes de trabajo', default=True)
    notes = models.TextField('observaciones internas', blank=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)

    class Meta:
        verbose_name = 'permiso de funciones de plataforma'
        verbose_name_plural = 'permisos de funciones de plataforma'

    def __str__(self):
        return f'Permisos de {self.user}'


class WorkOrder(models.Model):
    ORDER_MAINTENANCE = 'maintenance'
    ORDER_REPAIR = 'repair'

    ORDER_TYPE_CHOICES = [
        (ORDER_MAINTENANCE, 'Mantenimiento'),
        (ORDER_REPAIR, 'Reparación'),
    ]

    STATUS_OPEN = 'open'
    STATUS_CLOSED = 'closed'

    STATUS_CHOICES = [
        (STATUS_OPEN, 'Abierta'),
        (STATUS_CLOSED, 'Cerrada'),
    ]

    employee = models.ForeignKey(
        Employee,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='work_orders',
        verbose_name='trabajador',
    )
    worker_name = models.CharField('nombre del trabajador', max_length=255)
    vehicle_machine = models.CharField('vehículo o máquina', max_length=255)
    order_type = models.CharField('tipo', max_length=30, choices=ORDER_TYPE_CHOICES)
    task_description = models.TextField('descripción de tarea')
    status = models.CharField('estado', max_length=30, choices=STATUS_CHOICES, default=STATUS_OPEN)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_work_orders',
        verbose_name='creada por',
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)
    updated_at = models.DateTimeField('última actualización', auto_now=True)
    closed_at = models.DateTimeField('fecha de cierre', null=True, blank=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'orden de trabajo'
        verbose_name_plural = 'órdenes de trabajo'

    def __str__(self):
        return f'{self.worker_name} · {self.vehicle_machine} · {self.get_order_type_display()}'

    @property
    def total_hours(self):
        total = 0
        for entry in self.hour_entries.all():
            total += float(entry.hours or 0)
        return total


class WorkOrderReceipt(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='receipts',
        verbose_name='orden de trabajo',
    )
    receipt_file = models.FileField(
        'foto/PDF de albarán o ticket',
        upload_to='work_order_receipts/%Y/%m/',
    )
    receipt_date = models.DateField('fecha del albarán/ticket', null=True, blank=True)
    supplier = models.CharField('proveedor/taller', max_length=255, blank=True)
    receipt_number = models.CharField('número de albarán/ticket', max_length=120, blank=True)
    amount = models.DecimalField('importe', max_digits=10, decimal_places=2, null=True, blank=True)
    description = models.TextField('descripción', blank=True)
    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='uploaded_work_order_receipts',
        verbose_name='subido por',
    )
    uploaded_at = models.DateTimeField('fecha de subida', auto_now_add=True)

    class Meta:
        ordering = ['-uploaded_at']
        verbose_name = 'albarán/ticket de orden de trabajo'
        verbose_name_plural = 'albaranes/tickets de órdenes de trabajo'

    def __str__(self):
        return self.receipt_number or self.supplier or f'Albarán orden {self.work_order_id}'


class WorkOrderHourEntry(models.Model):
    work_order = models.ForeignKey(
        WorkOrder,
        on_delete=models.CASCADE,
        related_name='hour_entries',
        verbose_name='orden de trabajo',
    )
    work_date = models.DateField('fecha')
    hours = models.DecimalField('horas', max_digits=5, decimal_places=2)
    notes = models.TextField('observaciones', blank=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_work_order_hours',
        verbose_name='creado por',
    )
    created_at = models.DateTimeField('fecha de creación', auto_now_add=True)

    class Meta:
        ordering = ['-work_date', '-created_at']
        verbose_name = 'hora de orden de trabajo'
        verbose_name_plural = 'horas de órdenes de trabajo'

    def __str__(self):
        return f'{self.work_order} · {self.work_date:%d/%m/%Y} · {self.hours}h'
