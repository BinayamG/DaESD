from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, CommunityRequestForm, EventForm
from .models import CommunityRequest, Community, Event
from django.contrib import messages


#Function for super_users
superuser_required = user_passes_test(lambda u: u.is_authenticated and u.is_superuser)

def home_view(request):
    return render(request, "home.html")

def login_view(request): 
    if request.method == "POST":
        form = AuthenticationForm(data=request.POST)
        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("main")
            else:
                print("Invalid username or password")
        else:
            print("Form errors:", form.errors.as_json())
    else:
        form = AuthenticationForm() 
    return render(request, "accounts/login.html", {"form": form})
    

def signup_view(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            form.save()
            print("User successfully created!")  # Debug message
            return redirect('login')
        else:
            print("Form errors:", form.errors.as_json())  # Debugging errors

    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {'form': form})

@login_required
def main_view(request):
    user = request.user
    if request.method == 'POST':
            if 'update-profile-form' in request.POST:
                first_name = request.POST.get('first_name')
                last_name = request.POST.get('last_name')
                email = request.POST.get('email')
                student_number = request.POST.get('student_number')

                if first_name:
                    user.first_name = first_name
                if last_name:
                    user.last_name = last_name
                if email:
                    user.email = email
                if student_number:
                    user.student_number = student_number
                user.save()
                messages.success(request, 'Profile updated successfully')

            elif 'change-password-form' in request.POST:
                current_password = request.POST.get('current_password')
                new_password = request.POST.get('new_password')
                confirm_password = request.POST.get('confirm_password')

                if not user.check_password(current_password):
                    messages.error(request, 'Current password is incorrect')
                elif new_password != confirm_password:
                    messages.error(request, 'New password and confirm password do not match')
                elif len(new_password) < 8:
                    messages.error(request, "password must be at least 8 characters")
                elif new_password.isdigit():
                    messages.error(request, "password must contain at least one letter")
                else:
                    user.set_password(new_password)
                    user.save()
                    update_session_auth_hash(request, user)
                    messages.success(request, 'Password updated successfully')

    context = {
        "username": user.username,
        "full_name": f"{user.first_name} {user.last_name}",
        "email": user.email,
        "student_number": user.student_number,
        "first_name": user.first_name,
        "last_name": user.last_name,
        "is_superuser": user.is_superuser, 
    }
    return render(request, "accounts/main.html", context)

@login_required
def delete_account_view(request):
    user = request.user
    if request.method == 'POST':
        user.delete()
        messages.success(request, "Your account has been deleted successfully")
        return redirect('signup')
    return render('main')


@login_required
def request_community_creation_view(request):
    if request.method == "POST":
        form = CommunityRequestForm(request.POST)

        if form.is_valid():
            request_obj = form.save(commit=False)
            request_obj.requested_by = request.user
            request_obj.save()
            messages.success(request, "Your community creation request was sent to an admin for review")

            return redirect("main")
    else:
        form = CommunityRequestForm()

    return render(request, "communityForm.html", {"form": form})

@superuser_required
def community_request_review_view(request):
    pending_requests = CommunityRequest.objects.filter(is_approved=False, is_rejected=False)
    
    if request.method == "POST":
        action = request.POST.get("action")
        req_id = request.POST.get("request_id")
        request_obj = CommunityRequest.objects.get(id=req_id)

        if action == "approve":
            request_obj.approve(request.user)
            messages.success(request, f"Approved community: {request_obj.name}")
        elif action == "reject":
            reason = request.POST.get("rejection_reason", "")
            request_obj.reject(request.user, reason)
            messages.error(request, f"Rejected community: {request_obj.name}")

    return render(request, "review_admin_dashboard.html", {"pending_requests": pending_requests})

@login_required
def create_event_view(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if community.created_by != request.user:
        return messages.error(request, 'Only the community leader can create events')
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.community = community
            event.created_by = request.user
            event.save()
            return redirect('main')
        
    else: 
        form = EventForm()

    return render(request, 'create_event.html', {'form': form, 'community': community})
     
