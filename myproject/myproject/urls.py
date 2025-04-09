"""
URL configuration for myproject project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

from django.contrib import admin
from django.urls import path,include
from myapp.views import home_view, community_detail, leave_community, create_post_view

urlpatterns = [
    path("admin/", admin.site.urls),
    path('myapp/', include('myapp.urls')),
    path('', home_view, name="home"),
    path('community/<int:community_id>/', community_detail, name='community_detail'),
    # 新增两个路由
    path('leave-community/<int:community_id>/', leave_community, name='leave_community'),
    path('create-post/<int:community_id>/', create_post_view, name='create_post'),
]
