from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, CommunityRequest, Event, Post, Comments
from django.core.exceptions import ValidationError

class CustomUserCreationForm(UserCreationForm):
    email = forms.EmailField(required=True)
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)
    student_number = forms.CharField(max_length=20, required=True)
    date_of_birth = forms.DateField(required=True, widget=forms.DateInput(attrs={'type': 'date'}))
    degree_program = forms.ChoiceField(choices=CustomUser.DEGREE_CHOICES, required=True)
    major = forms.CharField(max_length=100, required=True)

    class Meta:
        model = CustomUser
        fields = ('username', 'email', 'password1', 'password2', 'first_name', 'last_name', 'student_number', 'date_of_birth', 'degree_program', 'major')

    def clean_date_of_birth(self):
        dob = self.cleaned_data.get('date_of_birth')
        if dob:
            import datetime
            today = datetime.date.today()
            age = today.year - dob.year - ((today.month, today.day) < (dob.month, dob.day))
            if age < 16:
                raise forms.ValidationError("You must be at least 16 years old to register.")
        return dob

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()
        return user

# User Address Form
class UserAddressForm(forms.ModelForm):
    street_address = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Street Address'}))
    city = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'City'}))
    postcode = forms.CharField(required=True, widget=forms.TextInput(attrs={'placeholder': 'Postcode'}))
    
    class Meta:
        model = CustomUser
        fields = ['street_address', 'city', 'postcode']

# Community Request form replaced from original 
class CommunityRequestForm(forms.ModelForm):
    class Meta:
        model = CommunityRequest
        fields = ['name', 'description', 'tags']

# Event Creation form
class EventForm(forms.ModelForm):
    class Meta:
        model = Event
        fields = ['title', 'description', 'date', 'end_date', 'location', 'event_type', 'maximum_capacity', 'required_materials']
        widgets = {
            'date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'location': forms.TextInput(attrs={'placeholder': 'Physical location or virtual meeting link'}),
            'maximum_capacity': forms.NumberInput(attrs={'min': '1', 'placeholder': 'Leave blank for unlimited'}),
            'required_materials': forms.Textarea(attrs={'rows': 3, 'placeholder': 'List any materials participants should bring'})
        }

# Post creation form      \  
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category', 'tags', 'attachment']
        widgets = {
            'title': forms.TextInput(attrs={'placeholder': 'Post title'}),
            'content': forms.Textarea(attrs={'rows': 3, 'placeholder': 'What’s on your mind?'}),
            'category': forms.Select(),
        }
    def clean_attachment(self):
        attachment = self.cleaned_data.get('attachment')
        if attachment:
            if not attachment.name.lower().endswith(('.png', '.jpg', '.jpeg')):
                raise ValidationError("Only PNG and JPEG images are allowed.")
        return attachment

# Comment creation form for posts
class CommentForm(forms.ModelForm):
    class Meta:
        model = Comments
        fields = ['content']
