from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, update_session_auth_hash
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.decorators import login_required
from .forms import CustomUserCreationForm, CommunityForm, PostForm
from django.contrib import messages
from .models import Community, Post


def home_view(request):
     # 获取最新的帖子（按时间倒序排列）
    latest_posts = Post.objects.all().order_by('-created_at')[:5]  # 例如：显示最新的5篇帖子
    
    context = {
        'latest_posts': latest_posts,  # 传递给模板
        'user': request.user  # 检查用户是否登录
    }
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

    context = {
        'full_name': user.get_full_name(),
        'username': user.username,
        'email': user.email,
        'first_name': user.first_name,
        'last_name': user.last_name,
        'student_number': user.student_number,
        'user_communities': user_communities,
        'all_communities': all_communities,
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


def create_community_view(request):
    if request.method == "POST":
        form = CommunityForm({
            'name': request.POST.get('name'),
            'description': request.POST.get('description'),
            'tags': request.POST.get('tags'),
        })

        if form.is_valid():
            community = form.save(commit=False)
            community.created_by = request.user 
            community.save()
            community.members.add(request.user) 
            return redirect("main")  
        else:
            return render(request, "communityForm.html", {"form": form, "form_errors": form.errors})
    
    else:
        form = CommunityForm()

    return render(request, "communityForm.html", {"form": form})

@login_required
def join_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.user in community.members.all():
        messages.info(request, "You are already a member of this community.")
    else:
        community.members.add(request.user)
        messages.success(request, f"You have successfully joined the community: {community.name}")
    return redirect('main')  # Redirect to the main page or communities tab


# 离开社区功能
@login_required
def leave_community(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.user in community.members.all():
        community.members.remove(request.user)
        messages.success(request, f"You have left {community.name}")
    return redirect('community_detail', community_id=community_id)

# 创建帖子功能
@login_required
def create_post_view(request, community_id):
    community = get_object_or_404(Community, id=community_id)
    if request.method == 'POST' and request.user in community.members.all():
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.user = request.user
            post.community = community
            post.save()
            return redirect('community_detail', community_id=community.id)
    return redirect('community_detail', community_id=community.id)
