from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_view, signup_view, main_view, delete_account_view, create_community_view, join_community, leave_community #delete_community #search_communities

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-account/', delete_account_view, name='delete-account'),
    path('create_community/', create_community_view, name="create_community"),
    path('join-community/<int:community_id>/', join_community, name='join_community'),
    path("leave-community/", leave_community, name="leave_community"),
    # path('search-communities/', search_communities, name='search_communities'),
    # path('delete-community/', delete_community, name='delete_community'),

]
