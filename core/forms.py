from typing import Any
from django import forms
from django.contrib.auth.models import User
from django.utils.text import slugify
from .models import Project, ProjectMembership, File, UserProfile, Organization, OrganizationMembership, TodoItem, CalendarEvent, BudgetItem, Announcement
from allauth.account.forms import SignupForm

class ProjectForm(forms.ModelForm):
    class Meta:
        model = Project
        fields = ['title', 'description', 'status', 'organization', 'priority']
        widgets = {
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the contents of the project'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'status': forms.Select(attrs={'class': 'form-control'}),
            'organization': forms.Select(attrs={'class': 'form-control'}),
            'priority': forms.Select(attrs={'class': 'form-control'})
        }

    def clean_title(self):
        title = self.cleaned_data['title']
        if self.instance.pk is None:  # Only for new projects
            slug = slugify(title)
            if Project.objects.filter(slug=slug).exists():
                raise forms.ValidationError("A project with a similar title already exists.")
        return title

class TodoForm(forms.ModelForm):
    class Meta:
        model = TodoItem
        fields = ['title', 'description', 'due_date', 'priority']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 3}),
        }
    def clean_due_date(self):
        due_date = self.cleaned_data.get('due_date')
        if not due_date:
            raise forms.ValidationError("Due date is required")
        return due_date

class BudgetItemForm(forms.ModelForm):
    class Meta:
        model = BudgetItem
        fields = ['description', 'amount', 'is_expense', 'date']
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
        }

class EventForm(forms.ModelForm):
    class Meta:
        model = CalendarEvent
        fields = ['title', 'description', 'start_time', 'end_time', 'location']
        widgets = {
            'start_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'end_time': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def clean(self):
        cleaned_data = super().clean()
        start_time = cleaned_data.get('start_time')
        end_time = cleaned_data.get('end_time')
        if end_time and start_time and end_time < start_time:
            raise forms.ValidationError({
                'end_time': ["End time must be after start time"]
            })
        return cleaned_data

class FileForm(forms.ModelForm):
    class Meta:
        model = File
        fields = ['file', 'title', 'description', 'keywords']
        widgets = {
            'file': forms.FileInput(attrs={'class': 'form-control-file'}),
            'title': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter the file title'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Describe the contents of the file'}),
            'keywords': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter keywords separated by commas'}),
        }

class ProjectMembershipForm(forms.Form):
    user = forms.ModelChoiceField(queryset=User.objects.all())
    role = forms.ChoiceField(choices=ProjectMembership.ROLE_CHOICES)

class UserProfileForm(forms.ModelForm):
    first_name = forms.CharField(max_length=30, required=False)
    last_name = forms.CharField(max_length=30, required=False)
    email = forms.EmailField(required=False)

    class Meta:
        model = UserProfile
        fields = ['profile_picture', 'interests', 'google_account']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.user:
            self.fields['first_name'].initial = self.instance.user.first_name
            self.fields['last_name'].initial = self.instance.user.last_name
            self.fields['email'].initial = self.instance.user.email

    def save(self, commit=True):
        profile = super().save(commit=False)
        if commit:
            profile.save()
            user = profile.user
            user.first_name = self.cleaned_data['first_name']
            user.last_name = self.cleaned_data['last_name']
            user.email = self.cleaned_data['email']
            user.save()
        return profile
    
class CustomSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, required=True)
    last_name = forms.CharField(max_length=30, required=True)

    def save(self, request):
        user = super().save(request)
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        user.save()

        # Create UserProfile for new user if needed
        UserProfile.objects.get_or_create(user=user)

        return user

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'feed_visible','organization_picture', 'category', 'size']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'feed_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'organization_picture': forms.FileInput(attrs={'class': 'form-control-file'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'size': forms.Select(attrs={'class': 'form-control'})
        }
    def clean_name(self):
        name = self.cleaned_data['name']
        if self.instance.pk is None:  # Only for new organizations
            slug = slugify(name)
            if Organization.objects.filter(slug=slug).exists():
                raise forms.ValidationError("An organization with a similar name already exists.")
        return name


class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = ['name', 'description', 'feed_visible', 'category', 'size']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'rows': 4}),
            'feed_visible': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'category': forms.Select(attrs={'class': 'form-control'}),
            'size': forms.Select(attrs={'class': 'form-control'})
        }

class OrganizationMembershipForm(forms.ModelForm):
    class Meta:
        model = OrganizationMembership
        fields = ['user', 'role']
        widgets = {
            'user': forms.Select(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-control'})
        }

    def __init__(self, organization=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if organization:
            # Exclude users who are already members
            existing_members = organization.members.all()
            self.fields['user'].queryset = User.objects.exclude(
                id__in=existing_members.values_list('id', flat=True)
            )

class OrganizationJoinRequestForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Optional message to the organization owner"
    )

class ProjectMembershipForm(forms.Form):
    user = forms.ModelChoiceField(
        queryset=User.objects.all(),
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    role = forms.ChoiceField(
        choices=ProjectMembership.ROLE_CHOICES,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, project=None, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if project:
            # Exclude users who are already members
            existing_members = project.members.all()
            self.fields['user'].queryset = User.objects.exclude(
                id__in=existing_members.values_list('id', flat=True)
            )

class ProjectJoinRequestForm(forms.Form):
    message = forms.CharField(
        widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        required=False,
        help_text="Optional message to the project owner"
    )
    
class AnnouncementForm(forms.ModelForm):
    class Meta:
        model = Announcement
        fields = ['content']

    content = forms.CharField(widget=forms.Textarea, required=True)
