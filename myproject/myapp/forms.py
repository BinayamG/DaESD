from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, CommunityRequest, Event

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    student_number = forms.CharField(max_length=20, required=True)
    degree_program = forms.ChoiceField(choices=CustomUser.DEGREE_CHOICES, required=True)
    major = forms.CharField(max_length=100, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'student_number', 'degree_program', 'major')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user
    
# Community form (templates/communityForm.html)
# class CommunityForm(forms.ModelForm):
#     class Meta:
#         model = Community
#         fields = ['name', 'description', 'tags']

# Community Request form replaced from original 
class CommunityRequestForm(forms.ModelForm):
    class Meta:
        model = CommunityRequest
        fields = ['name', 'description', 'tags']

# Event Creation form
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'location', 'event_type']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'})
        }
        
