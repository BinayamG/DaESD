from django.shortcuts import render, redirect
from .forms import CustomUserCreationForm

def login_view(request):
    return render(request, "accounts/login.html")

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            print("User successfully created!")  # Debug message
            return redirect('login')
        else:
            print("Form errors:", form.errors)  # Debugging errors

    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {'form': form})

def home_view(request):
    return render(request, "home.html")

