from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required, user_passes_test
from .forms import CustomUserCreationForm, CommunityRequestForm, EventForm, PostForm, CommentForm
from django.contrib import messages
from django.db import models, IntegrityError
from django.db.models import Q
from .models import CommunityRequest, Community, Event, CustomUser, FriendRequest, RemovedMember, Post, Notification, Comments
from django.http import JsonResponse
import json
from django.utils import timezone
import os
from django.conf import settings

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
            try:
                form.save()
                messages.success(request, "User successfully created! Please login.")
                return redirect('login')
            except IntegrityError as e:
                if 'email' in str(e):
                    messages.error(request, "An account with this email already exists.")
                elif 'student_number' in str(e):
                    messages.error(request, "An account with this student number already exists.")
                else:
                    messages.error(request, "An error occurred while creating your account.")
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{error}")
    else:
        form = CustomUserCreationForm()
    return render(request, "accounts/signup.html", {'form': form})

@login_required
def main_view(request):
    user = request.user
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')[:10]

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
                
            elif 'update-address-form' in request.POST:
                street_address = request.POST.get('street_address')
                city = request.POST.get('city')
                postcode = request.POST.get('postcode')
                
                if street_address and city and postcode:
                    user.street_address = street_address
                    user.city = city
                    user.postcode = postcode
                    user.save()
                    messages.success(request, 'Address updated successfully')
                else:
                    messages.error(request, 'All address fields are required')

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

    user_communities = (joined_communities | owned_communities).distinct()
    form = PostForm()

    # Get user's community IDs for filtering events
    user_community_ids = user_communities.values_list('id', flat=True)
    
    # Get pending friend requests
    pending_requests = FriendRequest.objects.filter(
        to_user=user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    if user.is_superuser:
        # For admins, show all events regardless of type or community
        events = Event.objects.all()
    else:
        # Regular users see only public events and events from their communities

        # Get public events
        public_events = Event.objects.filter(event_type='Public')
        
        # Get community-only events for communities the user is a member of
        community_events = Event.objects.filter(
            event_type='Community', 
            community__id__in=user_community_ids
        )
        
        # Combine the two querysets
        events = public_events | community_events
    
    # Filter out past events
    current_time = timezone.now()
    events = events.filter(
        Q(end_date__isnull=True) | Q(end_date__gt=current_time)
    )

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
        'form': form,
        'friend_requests': pending_requests,
        'notifications': notifications, 
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
            Notification.objects.create(
                user=request.user,
                message=f"Your community creation request was sent successfully!"
            )
            messages.success(request, "Your community creation request was sent to an admin for review")
            return redirect("main")
    else:
        form = CommunityRequestForm()
        # Check for rejected requests for this user
        rejected_request = CommunityRequest.objects.filter(
            requested_by=request.user,
            is_rejected=True
        ).order_by('-reviewed_at').first()
        
        if rejected_request and rejected_request.rejection_reason:
            messages.error(request, f"Your previous community creation request was rejected. Reason: {rejected_request.rejection_reason}")

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

            Notification.objects.create(
                user=request_obj.requested_by,
                message=f"Your community creation request for '{request_obj.name}' has been approved!"
            )
        elif action == "reject":
            reason = request.POST.get("rejection_reason", "")
            request_obj.reject(request.user, reason)

            Notification.objects.create(
                user=request_obj.requested_by,
                message=f"Your community creation request for '{request_obj.name}' was denied because: {reason}"
            )
            messages.error(request, f"Rejected community: {request_obj.name}. Reason: {reason}")

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
            Notification.objects.create(
                user=request.user,
                message=f"Your event '{event.title}' was created successfully!"
            )
            messages.success(request, 'Event created successfully!')
            return redirect('main')  # Redirect to the main page or another appropriate page
        
    else: 
        form = EventForm()

    return render(request, 'create_event.html', {'form': form, 'community': community})

@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    
    try:
        # Check if user was previously removed from this community
        if RemovedMember.objects.filter(user=request.user, community=community).exists():
            messages.error(request, f"You cannot join {community.name} as you were previously removed by the community leader.")
            # Redirect to main with communities tab active and ensure messages are displayed
            response = redirect('main')
            response['Location'] += '#communities'
            return response
    except Exception as e:
        # If RemovedMember table doesn't exist, we can safely ignore this check

        # This will handle the case until the proper migration is created
        pass
        
    if request.user in community.members.all():
        messages.info(request, "You are already a member of this community.")
    else:
        community.members.add(request.user)
        Notification.objects.create(
                user=request.user,
                message=f"You have joined the community '{community.name}' successfully!"
            )
        messages.success(request, f"You have successfully joined the community: {community.name}")
    
    # Redirect to main with communities tab active
    response = redirect('main')
    response['Location'] += '#communities'
    return response

@login_required
def leave_community(request):
    if request.method == "POST":
        community_id = request.POST.get("community_id")
        community = get_object_or_404(Community, id=community_id)
        # Remove the user from the community's members
        community.members.remove(request.user)
        Notification.objects.create(
                user=request.user,
                message=f"You have left the community '{community.name}' successfully!"
            )
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
            
            # Store community name before deletion for the success message
            community_name = community.name
            
            # Use raw SQL to delete the community and related data to bypass RemovedMember validation
            from django.db import connection
            with connection.cursor() as cursor:
                # First gets all event IDs for this community
                cursor.execute("SELECT id FROM myapp_event WHERE community_id = %s", [community_id])
                event_ids = [row[0] for row in cursor.fetchall()]
                
                # Second delete the event-user relationship records (interested users)
                if event_ids:
                    # Create placeholders for the SQL IN clause
                    placeholders = ','.join(['%s'] * len(event_ids))
                    cursor.execute(f"DELETE FROM myapp_event_interested_users WHERE event_id IN ({placeholders})", event_ids)
                
                # Third deletes any existing comments on posts in this community
                cursor.execute("""
                    DELETE FROM myapp_comments 
                    WHERE post_id IN (
                        SELECT id FROM myapp_post WHERE community_id = %s
                    )
                """, [community_id])
                
                # Fourth deletes all associated posts
                cursor.execute("DELETE FROM myapp_post WHERE community_id = %s", [community_id])
                
                # Fifth deletes all events related to this community
                cursor.execute("DELETE FROM myapp_event WHERE community_id = %s", [community_id])
                
                # Sixth removes all members from the community
                cursor.execute("DELETE FROM myapp_community_members WHERE community_id = %s", [community_id])
                
                # Seventh deletes the community itself
                cursor.execute("DELETE FROM myapp_community WHERE id = %s", [community_id])
            
            # Create notification for the user
            Notification.objects.create(
                user=request.user,
                message=f"You have deleted the community '{community_name}' successfully!"
            )
            
            messages.success(request, f"Community '{community_name}' has been deleted successfully.")
            return redirect('/myapp/main/#communities')
        
        except Community.DoesNotExist:
            messages.error(request, "Community not found.")
            return redirect('/myapp/main/#communities')
        except Exception as e:
            messages.error(request, f"An error occurred while deleting the community: {str(e)}")
            return redirect('/myapp/main/#communities')
    
    return redirect('/myapp/main/#communities')
    
@login_required
def search_communities(request):
    user = request.user
    query = request.GET.get('community_query', '').strip()
    search_results = []
    search_query = ''
    
    if query:
        search_query = query
        search_results = Community.objects.filter(
            Q(name__icontains=query) | 
            Q(description__icontains=query) | 
            Q(tags__icontains=query)
        ).distinct()
    else:
        search_results = Community.objects.all()

    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()
    user_communities = (joined_communities | owned_communities).distinct()
    
    # Get pending friend requests
    pending_requests = FriendRequest.objects.filter(
        to_user=user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    # Get events and filter out past events
    if user.is_superuser:
        events = Event.objects.all()
    else:
        # Regular users see only public events and events from their communities
        # Get user's community IDs for filtering events
        user_community_ids = user_communities.values_list('id', flat=True)
        
        # Gets public events
        public_events = Event.objects.filter(event_type='Public')
        
        # Gets community-only events for communities the user is a member of
        community_events = Event.objects.filter(
            event_type='Community', 
            community__id__in=user_community_ids
        )
        
        # Combine the two querysets
        events = public_events | community_events
    
    # Filter out past events
    current_time = timezone.now()
    events = events.filter(
        Q(end_date__isnull=True) | Q(end_date__gt=current_time)
    ).order_by('date')
    
    context = {
        'community_search_query': query,  # Used in template for community search
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
        'active_tab': 'communities',
        'friend_requests': pending_requests
    }
    
    return render(request, 'accounts/main.html', context)

@login_required
def search_events(request):
    user = request.user
    query = request.GET.get('event_query', '').strip()
    search_query = ''
    
    # Get users community IDs for filtering events
    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()
    user_communities = (joined_communities | owned_communities).distinct()
    user_community_ids = user_communities.values_list('id', flat=True)
    
    # Get pending friend requests
    pending_requests = FriendRequest.objects.filter(
        to_user=user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    if user.is_superuser:
        # For admins, allow searching across all events
        if query:
            search_query = query
            search_results = Event.objects.filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(community__name__icontains=query)
            )
        else:
            search_results = Event.objects.all()
    else:
        if query:
            search_query = query
            # Get public events matching the query
            public_events = Event.objects.filter(event_type='Public').filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(community__name__icontains=query)
            )
            
            # Get community-only events for communities the user is a member of
            community_events = Event.objects.filter(
                event_type='Community',
                community__id__in=user_community_ids
            ).filter(
                Q(title__icontains=query) | 
                Q(description__icontains=query) | 
                Q(community__name__icontains=query)
            )
            
            search_results = public_events | community_events
        else:
            # No query then show all accessible events
            public_events = Event.objects.filter(event_type='Public')
            community_events = Event.objects.filter(
                event_type='Community',
                community__id__in=user_community_ids
            )
            search_results = public_events | community_events
    
    # Filter out past events
    current_time = timezone.now()
    search_results = search_results.filter(
        Q(end_date__isnull=True) | Q(end_date__gt=current_time)
    ).order_by('date')

    all_communities = Community.objects.all()
    
    context = {
        'event_search_query': query,  # Used in template for event search
        'events': search_results,
        'user_communities': user_communities,
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_number': user.student_number,
        'is_superuser': user.is_superuser,
        'active_tab': 'events',
        'friend_requests': pending_requests,
        'all_communities': all_communities
    }
    
    return render(request, 'accounts/main.html', context)

@login_required
def toggle_event_interest(request, event_id):
    """Toggle the current user's interest in an event"""
    event = get_object_or_404(Event, id=event_id)
    user = request.user
    is_interested = False
    is_at_capacity = False
    
    if user in event.interested_users.all():
        # User is already interested, so remove interest
        event.interested_users.remove(user)
        messages.info(request, f"You are no longer registered for the event: {event.title}")
    else:
        # Check if maximum capacity is set and would be exceeded if user is added
        if event.maximum_capacity is not None and (event.interested_users.count() + 1) > event.maximum_capacity:
            messages.error(request, f"Sorry, maximum capacity of this event is reached ({event.maximum_capacity} attendees)")
            is_at_capacity = True
        else:
            # User is not interested and capacity is not reached, so add interest
            event.interested_users.add(user)
            is_interested = True
            Notification.objects.create(
                user=request.user,
                message=f"You have registered interest in the event: {event.title}!"
            )
            messages.success(request, f"You are now registered for the event: {event.title}")
    
    # If request is AJAX, return JSON response
    if request.headers.get('x-requested-with') == 'XMLHttpRequest':
        return JsonResponse({
            'is_interested': is_interested,
            'interest_count': event.interested_users.count(),
            'at_capacity': is_at_capacity  # This is now a separate flag set only when registration fails
        })
    
    # For non-AJAX requests, redirect back to the events tab

    # Uses the same URL format for both register and unregister to maintain consistency
    return redirect('/myapp/main/#events')

@login_required
def update_event_view(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    community = event.community
    
    # Checks if the logged-in user is the creator of the community
    if community.created_by != request.user:
        messages.error(request, 'Only the community leader can update events')
        return redirect('/myapp/main/#events')
    
    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            updated_event = form.save(commit=False)
            updated_event.community = community  # Ensure community stays the same
            updated_event.created_by = request.user  # Keep original creator
            updated_event.save()
            Notification.objects.create(
                user=request.user,
                message=f"Event '{updated_event.title}' updated successfully!"
            )
            messages.success(request, 'Event updated successfully!')
            return redirect('/myapp/main/#events')
    else:
        form = EventForm(instance=event)
    
    return render(request, 'update_event.html', {'form': form, 'event': event, 'community': community})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(Event, id=event_id)
    community = event.community
    
    # Check if the logged-in user is the creator of the community
    if community.created_by != request.user:
        messages.error(request, 'Only the community leader can delete events')
        return redirect('/myapp/main/#events')
    
    if request.method == 'POST':
        event_title = event.title
        event.delete()
        messages.success(request, f'Event "{event_title}" deleted successfully!')
    
    return redirect('/myapp/main/#events')


@login_required 
def create_post(request, community_id):
    community = get_object_or_404(Community, id=community_id)

    if request.method == 'POST':
        form = PostForm(request.POST, request.FILES)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.community = community
            post.save()

            Notification.objects.create(
                user=request.user,
                message=f"Your post '{post.title}' was created successfully!"
            )
            messages.success(request, "Post created successfully!")
            return redirect("main")
        else:
            messages.error(request, "There was an error in your form.")
    else:
        form = PostForm()
    return render(request, 'create_post.html', {'form': form, 'community': community})

@login_required
def load_community_posts(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    posts = community.posts.order_by('-created_at')
    comment_form = CommentForm()
    return render(request, 'postList.html', {
        'posts': posts, 
        'comment_form': comment_form,
        'community_id': community_id
    })

@login_required
def save_academic_profile(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user
            user.campus_involvement = data.get('campus_involvement', '')
            user.achievements = data.get('achievements', '')
            user.save()
            Notification.objects.create(
                user=request.user,
                message=f"Your new academic profile has been saved successfully!"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def save_interests(request):
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user = request.user
            user.interests = data.get('interests', '')
            if data.get('is_onboarding'):
                user.is_first_login = False
            user.save()
            Notification.objects.create(
                user=request.user,
                message=f"Your interests have been saved successfully!"
            )
            return JsonResponse({'success': True})
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)})
    return JsonResponse({'success': False, 'error': 'Invalid request method'})

@login_required
def get_community_members(request, community_id):
    try:
        community = Community.objects.get(id=community_id)
        current_user = request.user
        members_data = []
        creator = community.created_by
        creator_data = {
            'id': str(creator.id),  # Converts to string to match JavaScript comparison
            'name': f"{creator.get_full_name()} ({creator.username})",
            'role': 'Community Leader',
        }
        if creator != current_user:
            creator_data['friend_status'] = get_friend_status(current_user, creator)
        members_data.append(creator_data)
        
        # Adds other members
        for member in community.members.all():
            if member != creator:  # Skips the creator as they're already added
                member_data = {
                    'id': str(member.id),  # Converts to string to match JavaScript comparison
                    'name': f"{member.get_full_name()} ({member.username})",
                    'role': 'Member',
                }
                if member != current_user:
                    member_data['friend_status'] = get_friend_status(current_user, member)
                members_data.append(member_data)
        
        return JsonResponse({
            'success': True,
            'members': members_data
        })
    except Community.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Community not found'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

def get_friend_status(user1, user2):
    """Helper function to determine friend status between two users"""
    # Checks if they're already friends
    if user1.friends.filter(id=user2.id).exists():
        return 'friends'
    
    # Checks for pending friend requests
    pending_request = FriendRequest.objects.filter(
        (models.Q(from_user=user1, to_user=user2) | 
         models.Q(from_user=user2, to_user=user1)),
        status='pending'
    ).first()
    
    if pending_request:
        return 'pending'
    
    return 'send'

@login_required
def send_friend_request(request, user_id):
    to_user = get_object_or_404(CustomUser, id=user_id)
    from_user = request.user

    if from_user == to_user:
        messages.error(request, "You cannot send a friend request to yourself.")
        return JsonResponse({'success': False, 'error': 'Cannot friend yourself'})

    # Checks if a friend request already exists in either direction
    existing_request = FriendRequest.objects.filter(
        (models.Q(from_user=from_user, to_user=to_user) |
         models.Q(from_user=to_user, to_user=from_user)),
        status='pending'
    ).first()

    if existing_request:
        messages.error(request, "A friend request already exists between you and this user.")
        return JsonResponse({'success': False, 'error': 'Request already exists'})

    # Checks if they're already friends
    if from_user.friends.filter(id=to_user.id).exists():
        messages.error(request, "You are already friends with this user.")
        return JsonResponse({'success': False, 'error': 'Already friends'})

    # Creates the friend request
    FriendRequest.objects.create(from_user=from_user, to_user=to_user)
    Notification.objects.create(
        user=request.user,
        message=f"You have sent a friend request to {to_user.get_full_name()}!"
    )
    messages.success(request, f"Friend request sent to {to_user.get_full_name()}")
    return JsonResponse({'success': True, 'redirect': '/myapp/main/#home'})

@login_required
def handle_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    action = request.POST.get('action')

    if action == 'accept':
        friend_request.accept()
        Notification.objects.create(
            user=request.user,
            message=f"You are now friends with {friend_request.from_user.get_full_name()}!"
        )
        messages.success(request, f"You are now friends with {friend_request.from_user.get_full_name()}")
    elif action == 'reject':
        friend_request.reject()
        messages.info(request, f"You rejected the friend request from {friend_request.from_user.get_full_name()}")
    
    return redirect('/myapp/main/#friend-requests')

@login_required
def friend_requests_view(request):
    # Gets all the pending friend requests for the current user
    pending_requests = FriendRequest.objects.filter(
        to_user=request.user,
        status='pending'
    ).select_related('from_user').order_by('-created_at')
    
    context = {
        'friend_requests': pending_requests,
        'active_tab': 'friend-requests',
    }
    return render(request, 'accounts/main.html', context)

@login_required
def friends_view(request):
    user_friends = request.user.friends.all()
    return render(request, 'accounts/main.html', {'friends': user_friends, 'active_tab': 'friends'})

@login_required
def remove_friend(request, friend_id):
    if request.method == "POST":
        friend = get_object_or_404(CustomUser, id=friend_id)
        user = request.user
        
        # Removes both users from each other's friends list
        user.friends.remove(friend)
        friend.friends.remove(user)
        Notification.objects.create(
            user=request.user,
            message=f"You have succesfully removed {friend.get_full_name()} from your friends list!"
        )
        messages.success(request, f"{friend.get_full_name()} has been removed from your friends list.")
        return redirect('/myapp/main/#friends')
    return redirect('/myapp/main/#friends')

@login_required
def search_users(request):
    search_query = request.GET.get('user_query', '')
    if search_query:
        # Searches in "users" by name or interests
        user_search_results = CustomUser.objects.filter(
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query) |
            Q(interests__icontains=search_query)
        ).exclude(id=request.user.id)  # Exclude the current user

        # Annotates each user with their friend request status
        for user_result in user_search_results:
            pending_request = FriendRequest.objects.filter(
                (Q(from_user=request.user) & Q(to_user=user_result)) |
                (Q(from_user=user_result) & Q(to_user=request.user)),
                status='pending'
            ).exists()
            is_friend = request.user.friends.filter(id=user_result.id).exists()
            
            user_result.friend_status = 'friends' if is_friend else 'pending' if pending_request else 'send'
    else:
        user_search_results = []

    # Gets users community IDs for filtering of events
    user = request.user
    joined_communities = user.joined_communities.all()
    owned_communities = user.owned_communities.all()
    user_communities = (joined_communities | owned_communities).distinct()
    user_community_ids = user_communities.values_list('id', flat=True)
    
    # Gets events and filters out past events
    if user.is_superuser:
        # For admins, show all events
        events = Event.objects.all()
    else:
        # Regular users see only public events and events from their communities
        public_events = Event.objects.filter(event_type='Public')
        
        # Gets the community-only events for communities the user is a member of
        community_events = Event.objects.filter(
            event_type='Community', 
            community__id__in=user_community_ids
        )
        
        # Combines the two querysets
        events = public_events | community_events
    
    # Filters out past events
    current_time = timezone.now()
    events = events.filter(
        Q(end_date__isnull=True) | Q(end_date__gt=current_time)
    ).order_by('date')

    context = {
        'user_search_results': user_search_results,
        'user_search_query': search_query,  # Changed to user_search_query
        'full_name': f"{request.user.first_name} {request.user.last_name}",
        'email': request.user.email,
        'student_number': request.user.student_number,
        'username': request.user.username,
        'is_superuser': request.user.is_superuser,
        'friend_requests': FriendRequest.objects.filter(to_user=request.user, status='pending'),
        'all_communities': Community.objects.all(),
        'user_communities': Community.objects.filter(members=request.user),
        'events': events,
        'user': request.user,
    }
    
    return render(request, "accounts/main.html", context)

@login_required
def update_profile_image(request):
    if request.method == 'POST' and request.FILES.get('profile_image'):
        user = request.user
        image = request.FILES['profile_image']
        
        # Creates the profile_images directory if it doesn't exist
        upload_path = os.path.join(settings.MEDIA_ROOT, 'profile_images')
        os.makedirs(upload_path, exist_ok=True)
        
        # Saves the file
        filename = f'profile_{user.id}_{image.name}'
        filepath = os.path.join(upload_path, filename)
        
        with open(filepath, 'wb+') as destination:
            for chunk in image.chunks():
                destination.write(chunk)
        
        # Updates the user's profile_image field
        user.profile_image = f'profile_images/{filename}'
        user.save()
        Notification.objects.create(
            user=request.user,
            message=f"You have successfully updated your profile image!"
        )
        
        return JsonResponse({'success': True})
    return JsonResponse({'success': False, 'error': 'Invalid request'})

@login_required
def remove_community_member(request, community_id, member_id):
    if request.method == "POST":
        community = get_object_or_404(Community, id=community_id)
        member = get_object_or_404(CustomUser, id=member_id)
        
        # Check if the current user is the community leader
        if request.user != community.created_by:
            return JsonResponse({
                'success': False,
                'error': 'Only community leaders can remove members'
            })
            
        # Ensures the community leader cannot be removed
            return JsonResponse({
                'success': False,
                'error': 'Cannot remove the community leader'
            })
            
        # Member removal
        community.members.remove(member)
        RemovedMember.objects.create(
            user=member,
            community=community,
            removed_by=request.user
        )
        Notification.objects.create(
            user=request.user,
            message=f"You have succesfully removed {member.get_full_name()} from the community '{community.name}'!"
        )
        
        return JsonResponse({
            'success': True,
            'message': f'Successfully removed {member.get_full_name()} from the community'
        })
        
    return JsonResponse({
        'success': False,
        'error': 'Invalid request method'
    })

@login_required
def add_comment(request, post_id):
    post = get_object_or_404(Post, id=post_id)

    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.user = request.user
            comment.save()
            Notification.objects.create(
                user=request.user,
                message=f"Your have succesfully commented on the post '{post.title}'!"
            )
            messages.success(request, "Comment added.")
        else:
            messages.error(request, "Error adding comment.")
    
    return redirect('main') 

@login_required
def notification_view(request):
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    return render(request, 'notifications.html', {'notifications': notifications})

@login_required 
def delete_comment(request, comment_id):
    comment = get_object_or_404(Comments, id=comment_id)
    post = comment.post
    # Allows deletion only if the current user created the comment or is the community leader
    if request.user != comment.user and request.user != post.community.created_by:
        messages.error(request, "You do not have permission to delete this comment.")
        return redirect('main')
    
    if request.method == 'POST':
        comment.delete()
        Notification.objects.create(
            user=request.user,
            message=f"You have successfully deleted your comment on the post '{post.title}'!"
        )
        messages.success(request, "Comment deleted.")
    
    return redirect('main')

@login_required
def delete_post(request, post_id):
    post = get_object_or_404(Post, id=post_id)
    # Allows deletion only if the current user created the post or is the community leader for that community
    if request.user != post.user and request.user != post.community.created_by:
        messages.error(request, "You do not have permission to delete this post.")
        return redirect('main')
    
    if request.method == 'POST':
        post.delete()
        Notification.objects.create(
            user=request.user,
            message=f"You have successfully deleted the post '{post.title}'!"
        )
        messages.success(request, "Post deleted.")
    
    return redirect('main')

@login_required
def search_community_posts(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    query = request.GET.get('post_query', '').strip()
    comment_form = CommentForm()
    
    if query:
        # Searches for posts by title, content, category, or tags
        posts = Post.objects.filter(
            community=community
        ).filter(
            Q(title__icontains=query) | 
            Q(content__icontains=query) | 
            Q(category__icontains=query) |
            Q(tags__icontains=query)
        ).order_by('-created_at')
    else:
        # If no query, return all posts
        posts = community.posts.order_by('-created_at')
    
    # Check if it's an AJAX request
    is_ajax = request.headers.get('X-Requested-With') == 'XMLHttpRequest'
    
    if is_ajax:
        # For AJAX requests, render the post list template without layout
        return render(request, 'postList.html', {
            'posts': posts, 
            'comment_form': comment_form,
            'search_query': query,
            'community_id': community_id
        })
    else:
        # For direct URL access, redirect to communities tab
        return redirect(f'/myapp/main/#communities')