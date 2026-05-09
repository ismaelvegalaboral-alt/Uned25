from django.contrib import admin

from .models import Employee, VacationDecision, VacationRequest


@admin.register(Employee)
class EmployeeAdmin(admin.ModelAdmin):
    list_display = ('full_name', 'user', 'department', 'position', 'annual_days', 'email')
    search_fields = ('first_name', 'last_name', 'national_id', 'department', 'email', 'user__username')
    list_filter = ('department',)
    autocomplete_fields = ('user',)


class VacationDecisionInline(admin.StackedInline):
    model = VacationDecision
    extra = 0
    readonly_fields = ('decided_at', 'decision_pdf')


@admin.register(VacationRequest)
class VacationRequestAdmin(admin.ModelAdmin):
    list_display = ('employee', 'start_date', 'end_date', 'requested_days', 'status', 'created_at')
    list_filter = ('status', 'start_date', 'employee__department')
    search_fields = ('employee__first_name', 'employee__last_name', 'employee__user__username', 'notes')
    readonly_fields = ('created_at', 'updated_at', 'request_pdf')
    inlines = [VacationDecisionInline]


@admin.register(VacationDecision)
class VacationDecisionAdmin(admin.ModelAdmin):
    list_display = ('request', 'decision', 'decided_by', 'decided_at')
    list_filter = ('decision', 'decided_at')
    readonly_fields = ('decided_at', 'decision_pdf')
