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


class CustomPasswordChangeForm(forms.Form):
    current_password = forms.CharField(
        label='현재 비밀번호',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    new_password = forms.CharField(
        label='새 비밀번호',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )
    confirm_password = forms.CharField(
        label='새 비밀번호 확인',
        widget=forms.PasswordInput(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)

    def clean_current_password(self):
        current_password = self.cleaned_data.get('current_password')
        if not self.user.check_password(current_password):
            raise forms.ValidationError("현재 비밀번호가 올바르지 않습니다.")
        return current_password

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_password = cleaned_data.get("confirm_password")

        if new_password and confirm_password and new_password != confirm_password:
            self.add_error('confirm_password', "새 비밀번호가 일치하지 않습니다.")


class UserEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['first_name', 'last_name', 'email']
        widgets = {
            'first_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'disabled': True}),
            'last_name': forms.TextInput(attrs={'class': 'form-control', 'readonly': True, 'disabled': True}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'readonly': True, 'disabled': True}),
        }
