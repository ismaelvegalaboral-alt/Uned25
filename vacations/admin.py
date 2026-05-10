from django.contrib import admin

from .models import AuditLog, Employee, VacationDecision, VacationRequest

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


@admin.register(AuditLog)
class AuditLogAdmin(admin.ModelAdmin):
    list_display = ('created_at', 'actor', 'action', 'model_name', 'object_id', 'ip_address')
    list_filter = ('action', 'model_name', 'created_at')
    search_fields = ('actor__username', 'action', 'model_name', 'object_repr', 'ip_address')
    readonly_fields = ('actor', 'action', 'model_name', 'object_id', 'object_repr', 'metadata', 'ip_address', 'user_agent', 'created_at')

    def has_add_permission(self, request):
        return False


if PushSubscription is not None:
    @admin.register(PushSubscription)
    class PushSubscriptionAdmin(admin.ModelAdmin):
        list_display = ('user', 'is_active', 'created_at', 'updated_at')
        list_filter = ('is_active', 'created_at')
        search_fields = ('user__username', 'endpoint')
