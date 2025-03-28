from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import CustomUser, Community, Post

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

class CommunityForm(forms.ModelForm):

    class Meta:
        model = Community
        fields = ['name', 'description', 'tags']

# Post form (templates/accounts/main.html)
class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['title', 'content', 'category']
        widgets = {
            'title': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Post title'
            }),
            'content': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Write your post...'
            }),
            'category': forms.Select(attrs={
                'class': 'form-control'
            })
        }