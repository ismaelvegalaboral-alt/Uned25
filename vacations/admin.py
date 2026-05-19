from django.contrib import admin

from .models import DailyWorkReport, AuditLog, DailyWorkReport, Employee, LoginAttempt, VacationDecision, VacationRequest, CustomerDeliveryNote, DailyJobPlan, DailyJobAssignment, DailyJobStatusEntry, PlatformFeaturePermission, WorkOrder, WorkOrderReceipt, WorkOrderHourEntry

try:
    from .models import PushSubscription
except ImportError:
    PushSubscription = None


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    search_fields = ('first_name', 'last_name', 'department', 'national_id')
    list_display = ('first_name', 'last_name', 'department', 'position')


@admin.register(VacationRequest)
class VacationRequestAdmin(admin.ModelAdmin):
    list_display = ('id', 'employee', 'absence_type', 'start_date', 'end_date', 'requested_days', 'status')
    list_filter = ('absence_type', 'status', 'start_date')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__department')


@admin.register(VacationDecision)
class VacationDecisionAdmin(admin.ModelAdmin):
    list_display = ('request', 'decision', 'decided_by', 'decided_at')
    list_filter = ('decision', 'decided_at')
    search_fields = ('request__employee__first_name', 'request__employee__last_name', 'decided_by__username')


class DailyJobAssignmentInline(admin.TabularInline):
    model = DailyJobAssignment
    extra = 0


class DailyJobStatusEntryInline(admin.TabularInline):
    model = DailyJobStatusEntry
    extra = 0


@admin.register(DailyJobPlan)
class DailyJobPlanAdmin(admin.ModelAdmin):
    list_display = ('plan_date', 'title', 'is_published', 'created_by', 'created_at')
    list_filter = ('is_published', 'plan_date')
    search_fields = ('title', 'notes')
    readonly_fields = ('created_at', 'updated_at')
    inlines = [DailyJobAssignmentInline, DailyJobStatusEntryInline]


@admin.register(DailyJobAssignment)
class DailyJobAssignmentAdmin(admin.ModelAdmin):
    list_display = ('plan', 'category', 'client', 'worksite', 'machine', 'truck', 'worker_name', 'hours', 'trips')
    list_filter = ('category', 'plan__plan_date')
    search_fields = ('client', 'worksite', 'machine', 'truck', 'worker_name', 'notes')


@admin.register(DailyJobStatusEntry)
class DailyJobStatusEntryAdmin(admin.ModelAdmin):
    list_display = ('plan', 'status_type', 'text', 'sort_order')
    list_filter = ('status_type', 'plan__plan_date')
    search_fields = ('text',)


@admin.register(CustomerDeliveryNote)
class CustomerDeliveryNoteAdmin(admin.ModelAdmin):
    list_display = ('note_date', 'customer_name', 'worksite', 'received_by', 'employee', 'created_at')
    list_filter = ('note_date', 'created_at')
    search_fields = ('customer_name', 'worksite', 'address', 'received_by', 'work_description', 'materials')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(DailyWorkReport)
class DailyWorkReportAdmin(admin.ModelAdmin):
    list_display = ('report_date', 'worker_name', 'employee', 'hours', 'trips', 'created_at')
    list_filter = ('report_date', 'created_at')
    search_fields = ('worker_name', 'employee__first_name', 'employee__last_name', 'client_1', 'client_2', 'work_performed')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('actor__username', 'action', 'model_name', 'object_repr', 'ip_address')
    readonly_fields = ('actor', 'action', 'model_name', 'object_id', 'object_repr', 'metadata', 'ip_address', 'user_agent', 'created_at')

    def has_add_permission(self, request):
        return False


@admin.register(LoginAttempt)
class LoginAttemptAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'ip_address', 'username', 'success', 'blocked', 'path')
    list_filter = ('success', 'blocked', 'created_at')
    search_fields = ('ip_address', 'username', 'user_agent')
    readonly_fields = ('ip_address', 'username', 'path', 'success', 'blocked', 'user_agent', 'created_at')

    def has_add_permission(self, request):
        return False


if PushSubscription is not None:
    @admin.register(PushSubscription)
    class PushSubscriptionAdmin(admin.ModelAdmin):
        list_display = ('user', 'is_active', 'created_at', 'updated_at')
        list_filter = ('is_active', 'created_at')
        search_fields = ('user__username', 'endpoint')

@admin.register(PlatformFeaturePermission)
class PlatformFeaturePermissionAdmin(admin.ModelAdmin):
    list_display = ('user', 'can_use_vacations', 'can_use_daily_reports', 'can_use_customer_delivery_notes', 'can_use_daily_jobs', 'can_use_work_orders', 'updated_at')
    search_fields = ('user__username', 'user__first_name', 'user__last_name', 'user__email')
    list_filter = ('can_use_vacations', 'can_use_daily_reports', 'can_use_customer_delivery_notes', 'can_use_daily_jobs', 'can_use_work_orders')


class WorkOrderHourEntryInline(admin.TabularInline):
    model = WorkOrderHourEntry
    extra = 0


class WorkOrderReceiptInline(admin.TabularInline):
    model = WorkOrderReceipt
    extra = 0


@admin.register(WorkOrder)
class WorkOrderAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'worker_name', 'vehicle_machine', 'order_type', 'status', 'employee')
    list_filter = ('order_type', 'status', 'created_at')
    search_fields = ('worker_name', 'vehicle_machine', 'task_description')
    readonly_fields = ('created_at', 'updated_at', 'closed_at')
    inlines = [WorkOrderHourEntryInline, WorkOrderReceiptInline]


@admin.register(WorkOrderReceipt)
class WorkOrderReceiptAdmin(admin.ModelAdmin):
    list_display = ('uploaded_at', 'work_order', 'supplier', 'receipt_number', 'amount')
    list_filter = ('uploaded_at', 'receipt_date')
    search_fields = ('supplier', 'receipt_number', 'description')


@admin.register(WorkOrderHourEntry)
class WorkOrderHourEntryAdmin(admin.ModelAdmin):
    list_display = ('work_date', 'work_order', 'hours', 'created_by')
    list_filter = ('work_date',)
    search_fields = ('work_order__worker_name', 'work_order__vehicle_machine', 'notes')

