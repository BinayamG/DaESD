from django.urls import path
from .views import login_view, signup_view, main_view, create_community_view

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
    path('create_community/', create_community_view, name="create_community"),
]
