from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('student_number', 'degree_program', 'major')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)