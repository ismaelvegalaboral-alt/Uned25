from decimal import Decimal

from django import forms

from .models import Employee, VacationDecision, VacationRequest, DailyWorkReport
from .permissions import can_create_requests_for_others, get_employee_for_user
from .services import business_days_between, committed_days_for_employee


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['user', 'first_name', 'last_name', 'national_id', 'email', 'department', 'position', 'annual_days']


class VacationRequestForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if 'absence_type' in self.fields:
            self.fields['absence_type'].label = 'Tipo de ausencia'
        if 'supporting_document' in self.fields:
            self.fields['supporting_document'].label = 'Justificante opcional'
            self.fields['supporting_document'].help_text = 'Puedes adjuntar justificante si aplica.'
        self.user = user
        if user and not can_create_requests_for_others(user):
            employee = get_employee_for_user(user)
            if employee:
                self.fields['employee'].queryset = Employee.objects.filter(pk=employee.pk)
                self.fields['employee'].initial = employee
                self.fields['employee'].disabled = True
                self.fields['employee'].help_text = 'Solicitud vinculada a tu ficha de trabajador.'
            else:
                self.fields['employee'].queryset = Employee.objects.none()

    class Meta:
        model = VacationRequest
        fields = ['employee', 'absence_type', 'start_date', 'end_date', 'requested_days', 'supporting_document', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def clean_requested_days(self):
        requested_days = self.cleaned_data.get('requested_days')
        if requested_days is not None and requested_days <= 0:
            raise forms.ValidationError('Los días solicitados deben ser superiores a cero.')
        return requested_days

    def clean(self):
        cleaned = super().clean()
        employee = cleaned.get('employee')
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        requested_days = cleaned.get('requested_days')

        if start and end and end < start:
            raise forms.ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')

        if start and end and requested_days is not None:
            business_days = business_days_between(start, end)
            if business_days == 0:
                raise forms.ValidationError('El periodo indicado no contiene días laborables de lunes a viernes.')
            if requested_days > Decimal(business_days):
                raise forms.ValidationError(
                    f'Has indicado {requested_days:g} días, pero entre esas fechas solo hay {business_days} días laborables.'
                )

        if employee and start and end and requested_days is not None:
            temporary_request = VacationRequest(
                employee=employee,
                start_date=start,
                end_date=end,
                requested_days=requested_days,
            )
            already_committed = committed_days_for_employee(temporary_request)
            if already_committed + requested_days > employee.annual_days:
                raise forms.ValidationError(
                    f'El trabajador tiene {employee.annual_days} días anuales y ya constan '
                    f'{already_committed:g} día(s) comprometido(s) este año.'
                )

        return cleaned


class VacationDecisionForm(forms.ModelForm):
    confirm_policy_review = forms.BooleanField(
        label='Confirmo que he revisado las alertas de RRHH y el calendario de solapes',
        required=True,
    )

    def __init__(self, *args, hr_review=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.hr_review = hr_review

    class Meta:
        model = VacationDecision
        fields = ['decision', 'company_notes']
        widgets = {'company_notes': forms.Textarea(attrs={'rows': 5})}

    def clean(self):
        cleaned = super().clean()
        decision = cleaned.get('decision')
        company_notes = cleaned.get('company_notes', '').strip()

        if decision == VacationDecision.Decision.REJECTED and not company_notes:
            raise forms.ValidationError('Si la solicitud se deniega, indica el motivo en observaciones de dirección.')

        if (
            decision == VacationDecision.Decision.APPROVED
            and self.hr_review
            and self.hr_review.has_blocking_flags
            and not company_notes
        ):
            raise forms.ValidationError(
                'Esta solicitud tiene alertas críticas. Para aprobarla, deja una justificación en observaciones.'
            )

        return cleaned

class DailyWorkReportForm(forms.ModelForm):
    class Meta:
        model = DailyWorkReport
        fields = [
            'report_date',
            'machine_number',
            'truck_number',
            'other_equipment',
            'client_1',
            'client_2',
            'client_3',
            'client_4',
            'worksite_1',
            'worksite_2',
            'worksite_3',
            'worksite_4',
            'hours',
            'trips',
            'other_notes',
            'supplied_material',
            'work_performed',
            'signature_name',
        ]
        widgets = {
            'report_date': forms.DateInput(attrs={'type': 'date'}),
            'supplied_material': forms.Textarea(attrs={'rows': 2}),
            'work_performed': forms.Textarea(attrs={'rows': 7}),
        }

    def __init__(self, *args, employee=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.employee = employee
        for field in self.fields.values():
            css = field.widget.attrs.get('class', '')
            field.widget.attrs['class'] = (css + ' form-control').strip()

    def save(self, commit=True):
        instance = super().save(commit=False)
        if self.employee is not None:
            instance.employee = self.employee
            instance.worker_name = self.employee.full_name
        if not instance.signature_name:
            instance.signature_name = instance.worker_name
        if commit:
            instance.save()
        return instance
