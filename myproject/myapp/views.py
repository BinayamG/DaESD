from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, CommunityRequestForm, EventForm, PostForm
from django.contrib import messages
from django.db import models
from .models import CommunityRequest, Community, Event
from django.http import JsonResponse


# Decorator for super_users
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

    all_communities = Community.objects.all()

    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()

    user_communities = joined_communities | owned_communities
    form = PostForm() #SUMANTH


    # Get user's community IDs for filtering events
    user_community_ids = user_communities.values_list('id', flat=True)
    
    # Filter events based on event_type and user's community membership
    # 1. Get public events
    public_events = Event.objects.filter(event_type='Public')
    
    # 2. Get community-only events for communities the user is a member of
    community_events = Event.objects.filter(
        event_type='Community', 
        community__id__in=user_community_ids
    )
    
    # Combine the two querysets
    events = public_events | community_events

    context = {
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_number': user.student_number,
        'user_communities': user_communities,
        'all_communities': all_communities,
        "is_superuser": user.is_superuser, 
        "events": events,
        'form': form, #Sumanth

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

    # Check if the logged-in user is the creator of the community
    if community.created_by != request.user:
        messages.error(request, 'Only the community leader can create events')
        return redirect('main')  # Redirect to the main page or another appropriate page
    
    if request.method == 'POST':
        form = EventForm(request.POST)
        if form.is_valid():
            event = form.save(commit=False)
            event.community = community
            event.created_by = request.user
            event.save()
            messages.success(request, 'Event created successfully!')
            return redirect('main')  # Redirect to the main page or another appropriate page
        
    else: 
        form = EventForm()

    return render(request, 'create_event.html', {'form': form, 'community': community})

@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.user in community.members.all():
        messages.info(request, "You are already a member of this community.")
    else:
        community.members.add(request.user)
        messages.success(request, f"You have successfully joined the community: {community.name}")
    # Redirect to main with communities tab active
    return redirect('/myapp/main/#communities')

@login_required
def leave_community(request):
    if request.method == "POST":
        community_id = request.POST.get("community_id")
        community = get_object_or_404(Community, id=community_id)
        # Remove the user from the community's members
        community.members.remove(request.user)
        messages.success(request, f"You have left the community: {community.name}")
        # Redirect back to the communities page
        return redirect('/myapp/main/#communities')

@login_required
def delete_community(request):
    if request.method == "POST":
        community_id = request.POST.get("community_id")
        try:
            community = Community.objects.get(id=community_id)
            
            # Check if the current user is the creator of the community
            if request.user != community.created_by:
                messages.error(request, "You don't have permission to delete this community.")
                return redirect('/myapp/main/#communities')
            
            # Delete the community (CASCADE will automatically delete related events and posts)
            community_name = community.name
            community.delete()
            
            messages.success(request, f"Community '{community_name}' has been deleted successfully.")
            return redirect('/myapp/main/#communities')
        
        except Community.DoesNotExist:
            messages.error(request, "Community not found.")
            return redirect('/myapp/main/#communities')
    
    return redirect('/myapp/main/#communities')
    
@login_required
def search_communities(request):
    user = request.user
    query = request.GET.get('query', '').strip()
    search_results = []
    search_query = ''
    
    if query:
        search_query = query
        # Search for communities that match query in name, description, or tags
        search_results = Community.objects.filter(
            models.Q(name__icontains=query) | 
            models.Q(description__icontains=query) | 
            models.Q(tags__icontains=query)
        ).distinct()
    else:
        # If no query, return all communities
        search_results = Community.objects.all()
    
    # Get user communities for the sidebar
    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()
    user_communities = (joined_communities | owned_communities).distinct()
    
    # Get events for the events tab
    events = Event.objects.all()
    
    context = {
        'search_query': search_query,
        'all_communities': search_results,
        'user_communities': user_communities,
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_number': user.student_number,
        'is_superuser': user.is_superuser,
        'events': events,
        'active_tab': 'communities',  # Set the active tab to communities
    }
    
    return render(request, 'accounts/main.html', context)

@login_required
def search_events(request):
    user = request.user
    query = request.GET.get('query', '').strip()
    search_query = ''
    
    # Get user's community IDs for filtering events
    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()
    user_communities = joined_communities | owned_communities
    user_community_ids = user_communities.values_list('id', flat=True)
    
    if query:
        search_query = query
        # Get public events matching the query
        public_events = Event.objects.filter(
            event_type='Public'
        ).filter(
            models.Q(title__icontains=query) | 
            models.Q(description__icontains=query) | 
            models.Q(community__name__icontains=query)
        )
        
        # Get community-only events for communities the user is a member of
        community_events = Event.objects.filter(
            event_type='Community',
            community__id__in=user_community_ids
        ).filter(
            models.Q(title__icontains=query) | 
            models.Q(description__icontains=query) | 
            models.Q(community__name__icontains=query)
        )
        
        # Combine the querysets
        search_results = public_events | community_events
    else:
        # If no query, return all accessible events (public or from user's communities)
        public_events = Event.objects.filter(event_type='Public')
        community_events = Event.objects.filter(
            event_type='Community',
            community__id__in=user_community_ids
        )
        search_results = public_events | community_events
    
    context = {
        'search_query': search_query,
        'events': search_results,
        'user_communities': user_communities,
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_number': user.student_number,
        'is_superuser': user.is_superuser,
        'active_tab': 'events',  # Set the active tab to events
    }
    
    return render(request, 'accounts/main.html', context)

@login_required #Sumanth
def create_post(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.community = community
            post.save()
            messages.success(request, "Post created successfully!")
        else:
            messages.error(request, "There was an error in your form.")
        html = render(request, 'post.html', {'post': post}).content.decode('utf-8')
        return redirect("main")

@login_required #SUMANTH
def load_community_posts(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    posts = community.posts.order_by('-created_at')
    return render(request, 'postList.html', {'posts': posts})

# @login_required #Sumanth
# def delete_post(request, post_id):
#     post = get_object_or_404(post_id)
#     if request.method == 'POST':
#         post.delete()
#         messages.success(request, "Post deleted succesfully)")
#         return redirect("main")