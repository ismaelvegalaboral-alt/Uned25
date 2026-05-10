from django.contrib import admin

from .models import Employee, VacationDecision, VacationRequest

try:
    from .models import PushSubscription
except ImportError:
    PushSubscription = None


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    pass


@admin.register(VacationRequest)
class VacationRequestAdmin(admin.ModelAdmin):
    list_display = ("id", "employee", "absence_type", "start_date", "end_date", "requested_days", "status")
    list_filter = ("absence_type", "status", "start_date")
    search_fields = ("employee__first_name", "employee__last_name", "employee__department")


@admin.register(VacationDecision)
class VacationDecisionAdmin(admin.ModelAdmin):
    pass


if PushSubscription is not None:
    @admin.register(PushSubscription)
    class PushSubscriptionAdmin(admin.ModelAdmin):
        list_display = ("user", "is_active", "created_at", "updated_at")
        list_filter = ("is_active", "created_at")
        search_fields = ("user__username", "endpoint")
