from django import forms
from .models import User, Department

class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'first_name', 'last_name', 'email', 'password',
            'position', 'department', 'employee_number', 'join_date',
        ]

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)  # views에서 넘겨줄 값
        super().__init__(*args, **kwargs)

        if company:
            self.fields['department'].queryset = Department.objects.filter(
                is_active=True,
                company=company
            )
        else:
            self.fields['department'].queryset = Department.objects.none()
