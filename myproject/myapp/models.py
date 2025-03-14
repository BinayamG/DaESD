from django.db import models
from django.contrib.auth.models import AbstractUser

# Create your models here.
class CustomUser(AbstractUser):
    
    # Custom fields from the signup form:
    student_number = models.CharField(max_length=20, unique=True)
    
    DEGREE_CHOICES = [
        ('Bachelors', 'Bachelors Degree'),
        ('Masters', 'Masters Degree'),
        ('Phd', 'Phd Degree'),
    ]
    degree_program = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    major = models.CharField(max_length=100)
    
    def __str__(self):
        return self.username