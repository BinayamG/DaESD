from django.urls import path
from django.contrib.auth import views as auth_views
from .views import login_view, signup_view, main_view, delete_account_view, create_community_view, join_community

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
    path('logout/', auth_views.LogoutView.as_view(next_page='login'), name='logout'),
    path('delete-account/', delete_account_view, name='delete-account'),
    path('create_community/', create_community_view, name="create_community"),
    path('join-community/<int:community_id>/', join_community, name='join_community'),

]
