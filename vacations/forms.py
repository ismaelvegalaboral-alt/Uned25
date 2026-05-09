from django import forms

from .models import Employee, VacationDecision, VacationRequest


class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        fields = ['first_name', 'last_name', 'national_id', 'email', 'department', 'position', 'annual_days']


class VacationRequestForm(forms.ModelForm):
    class Meta:
        model = VacationRequest
        fields = ['employee', 'start_date', 'end_date', 'requested_days', 'notes']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': forms.Textarea(attrs={'rows': 4}),
        }

    def clean(self):
        cleaned = super().clean()
        start = cleaned.get('start_date')
        end = cleaned.get('end_date')
        if start and end and end < start:
            raise forms.ValidationError('La fecha de fin no puede ser anterior a la fecha de inicio.')
        return cleaned


class VacationDecisionForm(forms.ModelForm):
    class Meta:
        model = VacationDecision
        fields = ['decision', 'company_notes']
        widgets = {'company_notes': forms.Textarea(attrs={'rows': 5})}
