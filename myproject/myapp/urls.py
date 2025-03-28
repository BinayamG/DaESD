from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_view, signup_view, main_view, delete_account_view, request_community_creation_view, community_request_review_view, create_event_view

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-account/', delete_account_view, name='delete-account'),
    path("request_community/", request_community_creation_view, name="request_community"),
    path("review_admin_dashboard/", community_request_review_view, name="review_admin_dashboard"),
    path('create-event/<int:community_id>/', create_event_view, name='create_event_view'),
]
