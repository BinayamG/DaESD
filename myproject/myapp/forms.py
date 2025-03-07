from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    student_number = forms.CharField(max_length=20, required=True)
    degree_program = forms.ChoiceField(choices=CustomUser.DEGREE_CHOICES, required=True)
    major = forms.CharField(max_length=100, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password', 'first_name', 'last_name', 'student_number', 'degree_program', 'major')

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])  # Set the password
        if commit:
            user.save()
        return user