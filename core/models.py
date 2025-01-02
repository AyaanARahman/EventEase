from django.db import models
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import timezone
from django.utils.text import slugify
from django.core.files.storage import default_storage

class EventFile(models.Model):
    title = models.CharField(max_length=100)
    file = models.FileField(upload_to='uploads/')

class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    USER_TYPES = (
        ('common', 'Common User'),
        ('pma_admin', 'PMA Administrator'),
    )
    user_type = models.CharField(max_length=10, choices=USER_TYPES, default='common')
    google_account = models.EmailField(max_length=254, blank=True)
    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True, null=True)
    interests = models.TextField(blank=True)
    join_date = models.DateTimeField(default=timezone.now)

    def is_pma_admin(self):
        return self.user_type == 'pma_admin'
        
    def __str__(self):
        return f"{self.user.username} - {self.get_user_type_display()}"
    
    @property
    def search_fields(self):
        return [self.user.username, self.user.first_name, self.user.last_name, self.user.email]

class Organization(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    description = models.TextField(blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_organizations')
    members = models.ManyToManyField(User, through='OrganizationMembership', related_name='organizations')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    feed_visible = models.BooleanField(default=True) # if visible in feed or not add functionality to change?
    organization_picture = models.ImageField(upload_to='organization_pics/', blank=True, null=True)
    category = models.CharField(max_length=20, choices=[
        ('academic', 'Academic'),
        ('professional', 'Professional'),
        ('social', 'Social'),
        ('other', 'Other')
    ], default='other')
    size = models.CharField(max_length=20, choices=[
        ('small', 'Small (1-10)'),
        ('medium', 'Medium (11-50)'),
        ('large', 'Large (51+)')
    ], default='small')

    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
            # Check for existing slugs
            original_slug = self.slug
            count = 1
            while Organization.objects.filter(slug=self.slug).exists():
                self.slug = f"{original_slug}-{count}"
                count += 1
        super().save(*args, **kwargs)

    @property
    def search_fields(self):
        return [self.name, self.description]
    
class OrganizationMembership(models.Model):
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    ROLE_CHOICES = [
        ('MEMBER', 'Member'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ('organization', 'user')
    
    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.role})"

class OrganizationJoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='organization_join_requests')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='join_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')

    class Meta:
        unique_together = ('user', 'organization')

    def __str__(self):
        return f"{self.user.username} - {self.organization.name} ({self.get_status_display()})"


class Project(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(max_length=200, unique=True, blank=True)
    owner = models.ForeignKey(User, on_delete=models.CASCADE, related_name='owned_projects')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='projects', null=True, blank=True)
    members = models.ManyToManyField(User, through='ProjectMembership', related_name='projects')
    description = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = (
        ('active', 'Active'),
        ('archived', 'Archived'),
        ('deleted', 'Deleted'),
    )
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='active')
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High')
    ]
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')

    def is_pma_admin(self):
        return self.user_type == 'pma_admin'

    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
            # Check for existing slugs
            if Project.objects.filter(slug=self.slug).exists():
                # If slug exists, add a number to the end
                count = 1
                while Project.objects.filter(slug=f"{self.slug}-{count}").exists():
                    count += 1
                self.slug = f"{self.slug}-{count}"
        super().save(*args, **kwargs)
    
    def delete(self, *args, **kwargs):
        # instead of deleting now sets status to 'deleted'
        self.status = 'deleted'
        self.save()
    
    def has_pending_request(self, user):
        return self.join_requests.filter(user=user, status='PENDING').exists()

    @property
    def search_fields(self):
        return [self.title, self.description]

class ProjectJoinRequest(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_join_requests')
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='join_requests')
    created_at = models.DateTimeField(auto_now_add=True)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    message = models.TextField(blank=True)

    class Meta:
        unique_together = ('user', 'project')

    def __str__(self):
        return f"{self.user.username} - {self.project.title} ({self.get_status_display()})"

# class ProjectActivity(models.Model):
#     project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='activities')
#     user = models.ForeignKey(User, on_delete=models.CASCADE)
#     activity_type = models.CharField(max_length=50, choices=[
#         ('FILE_UPLOAD', 'File Upload'),
#         ('MEMBER_JOIN', 'Member Join'),
#         ('MEMBER_LEAVE', 'Member Leave'),
#         ('TODO_CREATE', 'Todo Created'),
#         ('EVENT_CREATE', 'Event Created'),
#         ('ANNOUNCEMENT', 'Announcement Posted'),
#         ('BUDGET_ITEM', 'Budget Item Added')
#     ])
#     description = models.TextField()
#     created_at = models.DateTimeField(auto_now_add=True)

#     class Meta:
#         ordering = ['-created_at']
    

class TodoItem(models.Model):
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
    ]

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    due_date = models.DateField(null=True, blank=True)
    priority = models.CharField(max_length=10, choices=PRIORITY_CHOICES, default='medium')
    completed = models.BooleanField(default=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='todos')
    
    # Set a default project may have to change later
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='todo_items', default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    reminder_sent = models.BooleanField(default=False)
    def __str__(self):
        return self.title

    class Meta:
        ordering = ['due_date', 'priority']

class BudgetItem(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='budget_items')
    description = models.CharField(max_length=200)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    is_expense = models.BooleanField(default=True)
    date = models.DateField()

    def __str__(self):
        return f"{self.description} - {'Expense' if self.is_expense else 'Income'}: ${self.amount}"


class ProjectMembership(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='memberships')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='project_memberships')
    ROLE_CHOICES = [
        ('MEMBER', 'Member'),
        ('EDITOR', 'Editor'),
        ('ADMIN', 'Admin'),
    ]
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='MEMBER')
    created_at = models.DateTimeField(default=timezone.now)
    STATUS_CHOICES = [
        ('PENDING', 'Pending'),
        ('APPROVED', 'Approved'),
        ('REJECTED', 'Rejected'),
    ]
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')


    class Meta:
        unique_together = ('project', 'user')

    def __str__(self):
        return f"{self.user.username} - {self.project.title} ({self.role})"
    
class File(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='files')
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='uploaded_files')
    file = models.FileField(upload_to='uploads/')
    uploaded_at = models.DateTimeField(auto_now_add=True)
    title = models.CharField(max_length=255, default='Untitled')
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, help_text="Description of file contents")  
    keywords = models.CharField(max_length=255, blank=True, help_text="Comma-separated keywords")  

    def __str__(self):
        return self.name

    def delete(self, *args, **kwargs):
        # now using default storage to delete file
        if self.file:
            file_name = self.file.name 
            if default_storage.exists(file_name):
                default_storage.delete(file_name)
        super().delete(*args, **kwargs)

    @property
    def search_fields(self):
        return [self.name, self.title, self.description, self.keywords]

    
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)

@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    try:
        profile = instance.userprofile
    except UserProfile.DoesNotExist:
        profile = UserProfile.objects.create(user=instance)
    
    if instance.is_superuser:
        profile.user_type = 'pma_admin'
    else:
        # Only set to 'common' if it's a new user (profile just created)
        if profile.user_type not in dict(UserProfile.USER_TYPES):
            profile.user_type = 'common'
    profile.save()


class CalendarEvent(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    start_time = models.DateTimeField()
    end_time = models.DateTimeField()
    location = models.CharField(max_length=200, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='events')

    # Set a default project may have to change later
    project = models.ForeignKey('Project', on_delete=models.CASCADE, related_name='calendar_events', default=1)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        ordering = ['start_time']
        
class Announcement(models.Model):
    project = models.ForeignKey(Project, related_name='announcements', on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_visible = models.BooleanField(default=True)


    def __str__(self):
        return f"Announcement by {self.user.username} on {self.created_at}"

    class Meta:
        ordering = ['-created_at']