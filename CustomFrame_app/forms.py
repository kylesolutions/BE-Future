from django.contrib.auth.forms import UserCreationForm

from CustomFrame_app.models import Login


class UserRegister(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Login
        fields = ('username', 'password1', 'password2', 'email', 'name', 'phone')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.is_user = True  # Set is_user to True for new users
        user.is_employee = False  # Ensure other roles are False
        user.is_blocked = False  # Ensure user is not blocked
        if commit:
            user.save()
        return user


class EmployeeRegister(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Login
        fields = ('username','password1','password2','email','company_name','company_address','phone','role')