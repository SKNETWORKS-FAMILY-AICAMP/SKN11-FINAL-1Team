from django import forms
from core.models import User, Department

class DepartmentForm(forms.ModelForm):
    class Meta:
        model = Department
        fields = ['department_name', 'description']
        labels = {
            'department_name': '부서명',
            'description': '설명',
        }
        widgets = {
            'department_name': forms.TextInput(attrs={'placeholder': '부서명', 'class': 'form-control', 'required': True}),
            'description': forms.TextInput(attrs={'placeholder': '설명', 'class': 'form-control'}),
        }


class UserForm(forms.ModelForm):
    class Meta:
        model = User
        fields = [
            'employee_number',
            'first_name',
            'last_name',
            'email',
            'department',
            'position',
            'job_part',
            'role',
            'tag',
            'mentorship_id',
            'is_admin',
            'is_active',
        ]
        labels = {
            'employee_number': '사번',
            'first_name': '이름',
            'last_name': '성',
            'email': '이메일',
            'department': '부서',
            'position': '직급',
            'job_part': '직무',
            'role': '역할',
            'tag': '태그',
            'mentorship_id': '멘토십ID',
            'is_admin': '관리자여부',
            'is_active': '활성화',
        }
        widgets = {
            'employee_number': forms.NumberInput(attrs={'placeholder': '사번', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': '이름', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': '성', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': '이메일', 'class': 'form-control'}),
            'company': forms.Select(attrs={'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
            'position': forms.TextInput(attrs={'placeholder': '직급', 'class': 'form-control'}),
            'job_part': forms.TextInput(attrs={'placeholder': '직무', 'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'}),
            'tag': forms.TextInput(attrs={'placeholder': '태그', 'class': 'form-control'}),
            'mentorship_id': forms.NumberInput(attrs={'placeholder': '멘토십ID', 'class': 'form-control'}),
            'is_admin': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)
        super().__init__(*args, **kwargs)
        if company:
            self.fields['department'].queryset = Department.objects.filter(is_active=True, company=company)
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

    def clean_new_password(self):
        """새 비밀번호가 현재 비밀번호와 같은지 확인"""
        new_password = self.cleaned_data.get('new_password')
        current_password = self.cleaned_data.get('current_password')
        
        if new_password and current_password and self.user.check_password(new_password):
            raise forms.ValidationError("현재 비밀번호와 동일합니다.")
        
        return new_password

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