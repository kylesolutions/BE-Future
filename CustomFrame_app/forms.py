from django.contrib.auth.forms import UserCreationForm

from CustomFrame_app.models import Login


class UserRegister(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Login
        fields = ('username','password1','password2','email','name','phone')


class EmployeeRegister(UserCreationForm):
    class Meta(UserCreationForm.Meta):
        model = Login
        fields = ('username','password1','password2','email','company_name','company_address','phone','role')