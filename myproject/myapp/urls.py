from django.urls import path
from .views import login_view, signup_view, main_view

urlpatterns = [
    path('login/', login_view, name="login"),
    path('signup/', signup_view, name="signup"),
    path('main/', main_view, name="main"),
]
