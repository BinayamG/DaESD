from django.urls import path
from django.contrib.auth import views as auth_views
from .views import (
    login_view, signup_view, main_view, delete_account_view, 
    join_community, leave_community, request_community_creation_view, 
    community_request_review_view, create_event_view, delete_community,
    search_communities, search_events, create_post, load_community_posts, toggle_event_interest,
    update_event_view, delete_event, save_academic_profile
)

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-account/', delete_account_view, name='delete-account'),
    path('join-community/<int:community_id>/', join_community, name='join_community'),
    path("leave-community/", leave_community, name="leave_community"),
    path('delete-community/', delete_community, name='delete_community'),
    path("request_community/", request_community_creation_view, name="request_community"),
    path("review_admin_dashboard/", community_request_review_view, name="review_admin_dashboard"),
    path('create-event/<int:community_id>/', create_event_view, name='create_event'),
    path('update-event/<int:event_id>/', update_event_view, name='update_event'),
    path('delete-event/<int:event_id>/', delete_event, name='delete_event'),
    path('search-communities/', search_communities, name='search_communities'),
    path('search-events/', search_events, name='search_events'),
    path('community/<int:community_id>/post/', create_post, name='create_post'), #SUMANTH
    path('community/<int:community_id>/posts/', load_community_posts, name='load_community_posts'), #SUMANTH
    path('event/<int:event_id>/toggle-interest/', toggle_event_interest, name='toggle_event_interest'),
    path('save-academic-profile/', save_academic_profile, name='save_academic_profile'),
]
