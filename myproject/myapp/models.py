from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

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
    
class Community(models.Model):
    name = models.CharField(max_length=255, unique=True)
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True)  # For searching
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name="owned_communities")
    members = models.ManyToManyField(CustomUser, related_name="joined_communities")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class CommunityRequest(models.Model):
    name = models.CharField(max_length=255)
    description = models.TextField()
    tags = models.CharField(max_length=255, blank=True)
    requested_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    is_approved = models.BooleanField(default=False)
    is_rejected = models.BooleanField(default=False)
    rejection_reason = models.TextField(blank=True)
    reviewed_by = models.ForeignKey(CustomUser, null=True, blank=True, on_delete=models.SET_NULL, related_name='reviewed_requests')
    reviewed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def approve(self, reviewer):
        # Community.objects.create(
        #     name=self.name,
        #     description=self.description,
        #     tags=self.tags,
        #     created_by=self.requested_by,
        # )

        community = Community.objects.create(
        name=self.name,
        description=self.description,
        tags=self.tags,
        created_by=self.requested_by,
    )
        community.members.add(self.requested_by)

        self.is_approved = True
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

    def reject(self, reviewer, reason):
        self.is_rejected = True
        self.rejection_reason = reason
        self.reviewed_by = reviewer
        self.reviewed_at = timezone.now()
        self.save()

class Event(models.Model):
    EVENT_TYPE_CHOICES = [
        ('Public', 'Public - Open to All'),
        ('Community', 'Community Members Only'),
    ]

    title = models.CharField(max_length=255)
    description = models.TextField()
    date = models.DateTimeField()
    location = models.CharField(max_length=255, blank=True)  # Physical or virtual link
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="events")
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)

    def __str__(self):
        return self.title


class Post(models.Model):
    CATEGORY_CHOICES = [
        ('Academic', 'Academic'),
        ('Social', 'Social'),
        ('Events', 'Events'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, null=True, blank=True)
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"