from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone

class CustomUser(AbstractUser):
    
    # Adding additional fields to the user model for vision.
    student_number = models.CharField(max_length=20, unique=True)
    date_of_birth = models.DateField(null=True)
    street_address = models.CharField(max_length=255, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    postcode = models.CharField(max_length=20, blank=True, null=True)
    
    DEGREE_CHOICES = [
        ('Bachelors', 'Bachelors Degree'),
        ('Masters', 'Masters Degree'),
        ('Phd', 'Phd Degree'),
    ]
    degree_program = models.CharField(max_length=20, choices=DEGREE_CHOICES)
    major = models.CharField(max_length=100)
    campus_involvement = models.TextField(blank=True)
    achievements = models.TextField(blank=True)
    interests = models.TextField(blank=True)  # New field for user interests
    is_first_login = models.BooleanField(default=True)  # Track if it's first login
    friends = models.ManyToManyField('self', through='Friendship', symmetrical=False)
    profile_image = models.ImageField(upload_to='profile_images/', null=True, blank=True)

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
    date = models.DateTimeField(verbose_name="Start Date and Time", help_text="Start date and time of the event")
    end_date = models.DateTimeField(verbose_name="End Date and Time", null=True, blank=True, help_text="End date and time of the event")
    location = models.CharField(max_length=255, blank=True, help_text="Physical location or virtual meeting link")  # Physical or virtual link
    event_type = models.CharField(max_length=20, choices=EVENT_TYPE_CHOICES)
    maximum_capacity = models.PositiveIntegerField(null=True, blank=True, help_text="Maximum number of attendees (leave blank for unlimited)")
    required_materials = models.TextField(blank=True, help_text="List any materials participants should bring or prepare")

    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name="events")
    created_by = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    interested_users = models.ManyToManyField(CustomUser, related_name="interested_events", blank=True)

    def __str__(self):
        return self.title
    
    def is_virtual(self):
        """Check if the event location is a virtual link"""
        return self.location.startswith('http://') or self.location.startswith('https://')
        
    def is_active(self):
        """Check if the event is still active (end date is in the future or not set)"""
        if not self.end_date:
            return True
        from django.utils import timezone
        return self.end_date > timezone.now()

class Post(models.Model):
    CATEGORY_CHOICES = [
        ('Academic', 'Academic'),
        ('Social', 'Social'),
        ('Events', 'Events'),
    ]

    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='posts', null=True, blank=True) #SUMANTH adding related_name = "posts"lets you access all posts from a community instance:    
    title = models.CharField(max_length=255)
    content = models.TextField()
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    tags = models.CharField(max_length=255, blank=True)  # SUMANTH and below
    attachment = models.FileField(upload_to='post_attachments/', blank=True, null=True)

    def __str__(self):
        return self.title


class Notification(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notification for {self.user.username}"
    
class Friendship(models.Model):
    from_user = models.ForeignKey(CustomUser, related_name='friendships', on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name='friend_of', on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"{self.from_user.username} is friends with {self.to_user.username}"

class FriendRequest(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]
    
    from_user = models.ForeignKey(CustomUser, related_name='sent_friend_requests', on_delete=models.CASCADE)
    to_user = models.ForeignKey(CustomUser, related_name='received_friend_requests', on_delete=models.CASCADE)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        unique_together = ('from_user', 'to_user')

    def __str__(self):
        return f"Friend request from {self.from_user.username} to {self.to_user.username}"

    def accept(self):
        if self.status == 'pending':
            # Add users to each other's friends list
            self.from_user.friends.add(self.to_user)
            self.to_user.friends.add(self.from_user)
            
            self.status = 'accepted'
            self.reviewed_at = timezone.now()
            self.save()

    def reject(self):
        if self.status == 'pending':
            self.status = 'rejected'
            self.reviewed_at = timezone.now()
            self.save()

class RemovedMember(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='removed_from_communities')
    community = models.ForeignKey(Community, on_delete=models.CASCADE, related_name='removed_members')
    removed_at = models.DateTimeField(auto_now_add=True)
    removed_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='member_removals')

    class Meta:
        unique_together = ('user', 'community')

    def __str__(self):
        return f"{self.user.username} removed from {self.community.name}"
    
class Comments(models.Model): #Sumanth
    post = models.ForeignKey(Post, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)