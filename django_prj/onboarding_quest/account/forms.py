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
            'employee_number',  # 사번이 제일 위
            'first_name',
            'last_name',
            'email',
            'position',
            'department',
        ]
        labels = {
            'employee_number': '사번',
            'first_name': '이름',
            'last_name': '성',
            'email': '이메일',
            'position': '직급',
            'department': '부서명',
        }
        widgets = {
            'employee_number': forms.NumberInput(attrs={'placeholder': '사번', 'class': 'form-control'}),
            'first_name': forms.TextInput(attrs={'placeholder': '이름', 'class': 'form-control'}),
            'last_name': forms.TextInput(attrs={'placeholder': '성', 'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'placeholder': '이메일', 'class': 'form-control'}),
            'position': forms.TextInput(attrs={'placeholder': '직급', 'class': 'form-control'}),
            'department': forms.Select(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        company = kwargs.pop('company', None)  # views에서 넘겨줄 값
        super().__init__(*args, **kwargs)

        # 비밀번호 필드는 폼에서 제거
        if 'password' in self.fields:
            self.fields.pop('password')

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
