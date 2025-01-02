import datetime
import json
import mimetypes
import os
import urllib.parse
from datetime import datetime, timedelta
from venv import logger

import boto3
from botocore.exceptions import ClientError
from django.conf import settings
from django.contrib import messages
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.db.models import Q
from django.forms import ValidationError
from django.http import (FileResponse, HttpResponse, HttpResponseForbidden,
                         JsonResponse)
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods, require_POST

from core.utils import is_pma_admin

from .forms import (AnnouncementForm, BudgetItemForm, EventForm, FileForm,
                    OrganizationForm, OrganizationJoinRequestForm,
                    OrganizationMembershipForm, OrganizationSettingsForm,
                    ProjectForm, ProjectJoinRequestForm, ProjectMembershipForm,
                    TodoForm, UserProfileForm)
from .models import (Announcement, CalendarEvent, File, Organization,
                     OrganizationJoinRequest, OrganizationMembership, Project,
                     ProjectJoinRequest, ProjectMembership, TodoItem, User,
                     UserProfile)


def home(request):
    projects = Project.objects.filter(status='active').order_by('-created_at')[:10000]
    return render(request, 'core/home.html', {'projects': projects})

@login_required
def dashboard(request):
    context = {}
    user_is_pma_admin = is_pma_admin(request.user)


    if user_is_pma_admin:
        context['projects'] = Project.objects.all()
        context['organizations'] = Organization.objects.all()
    

        # Get recent activities (last 7 days)
        seven_days_ago = timezone.now() - timedelta(days=7)
        recent_projects = Project.objects.filter(created_at__gte=seven_days_ago).order_by('-created_at')[:5]
        recent_memberships = ProjectMembership.objects.filter(created_at__gte=seven_days_ago, status='APPROVED').order_by('-created_at')[:5]
        recent_organizations = Organization.objects.filter(created_at__gte=seven_days_ago).order_by('-created_at')[:5]


        context['recent_activities'] = [
            f"New project created: {project.title}" for project in recent_projects
        ] + [
            f"New member added to {membership.project.title}: {membership.user.username}" for membership in recent_memberships
        ] + [
            f"New organization created: {org.name}" for org in recent_organizations

        ]
        
        template = 'core/admin/admin_dashboard.html'
    else:
        context['user_projects'] = request.user.owned_projects.filter(status='active')
        context['member_projects'] = Project.objects.filter(members=request.user, status='active').exclude(owner=request.user)
        context['user_organizations'] = request.user.organizations.all()
        context['owned_organizations'] = request.user.owned_organizations.all()
        todos = TodoItem.objects.filter(user=request.user).order_by('due_date', 'priority')
        # Adding calendar events for next 30 days
        thirty_days_from_now = timezone.now() + timedelta(days=30)
        context['calendar_events'] = CalendarEvent.objects.filter(
            user=request.user,
            start_time=thirty_days_from_now,
            end_time=timezone.now()
        ).order_by('start_time')
        template = 'core/user_dashboard.html'

    context['is_pma_admin'] = user_is_pma_admin
    return render(request, template, context)

def admin_project_list(request):
    return render(request, 'admin_project_list.html')

def admin_analytics(request):
    return render(request, 'admin_analytics.html')

def generate_report(request):
    return HttpResponse("Report has been generated.")

def send_newsletter(request):
    return render(request, 'core/admin/admin_dashboard.html') #change to an actual newsletter later
def logout_view(request):
    logout(request)
    messages.success(request, "You have been successfully logged out.")
    return redirect('home')

@login_required
def create_organization(request):
    user_is_pma_admin = is_pma_admin(request.user)
    if user_is_pma_admin:
        return HttpResponseForbidden("You are not allowed to create organizations")
    if request.method == 'POST':
        form = OrganizationForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                organization = form.save(commit=False)
                organization.owner = request.user
                organization.save()
                OrganizationMembership.objects.create(organization=organization, user=request.user, role='ADMIN')
                messages.success(request, f"Organization '{organization.name}' has been created successfully.")
                return redirect('organization_detail', slug=organization.slug)
            except IntegrityError:
                messages.error(request, "An error occured whole creating the organization.")
    else:
        form = OrganizationForm()
    return render(request, 'core/organization/create_organization.html', {'form': form})

@login_required
def organization_detail(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    user_is_pma_admin = is_pma_admin(request.user)
    is_member = organization.members.filter(id=request.user.id).exists()
    is_owner = organization.owner == request.user
    has_pending_request = OrganizationJoinRequest.objects.filter(
        user=request.user, 
        organization=organization, 
        status='PENDING'
    ).exists()

    if not user_is_pma_admin and not is_member and not is_owner and not organization.feed_visible:
        return HttpResponseForbidden("You don't have permission to view this organization.")
    
    projects = organization.projects.all()
    members = organization.members.all()
    
    context = {
        'organization': organization,
        'projects': projects,
        'members': members,
        'is_owner': is_owner,
        'is_member': is_member,
        'has_pending_request': has_pending_request,
        'is_pma_admin': user_is_pma_admin,

    }
    return render(request, 'core/organization/organization_detail.html', context)

@login_required
def manage_organization(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    if organization.owner != request.user:
        return HttpResponseForbidden("You don't have permission to manage this organization.")
    
    if request.method == 'POST':
        form = OrganizationSettingsForm(request.POST, instance=organization)
        if form.is_valid():
            form.save()
            messages.success(request, f"Organization '{organization.name}' has been updated successfully.")
            return redirect('organization_detail', slug=organization.slug)
    else:
        form = OrganizationSettingsForm(instance=organization)
    
    return render(request, 'core/organization/manage_organization.html', {
        'form': form,
        'organization': organization
    })

@login_required
def manage_organization_members(request, slug):
    user_is_pma_admin = is_pma_admin(request.user)
    if user_is_pma_admin:
        return HttpResponseForbidden("You are not allowed to manage members")
    organization = get_object_or_404(Organization, slug=slug)
    if organization.owner != request.user:
        return HttpResponseForbidden("You don't have permission to manage members for this organization.")

    if request.method == 'POST':
        form = OrganizationMembershipForm(organization=organization, data=request.POST)
        if form.is_valid():
            membership = form.save(commit=False)
            membership.organization = organization
            membership.save()
            messages.success(request, f"{membership.user.username} has been added to the organization.")
            return redirect('manage_organization_members', slug=organization.slug)
    else:
        form = OrganizationMembershipForm(organization=organization)

    memberships = OrganizationMembership.objects.filter(organization=organization)
    return render(request, 'core/organization/manage_organization_members.html', {
        'organization': organization,
        'memberships': memberships,
        'form': form
    })

login_required
def remove_organization_member(request, slug, user_id):
    organization = get_object_or_404(Organization, slug=slug)
    if organization.owner != request.user:
        return HttpResponseForbidden("You don't have permission to remove members from this organization.")

    membership = get_object_or_404(OrganizationMembership, organization=organization, user_id=user_id)
    if request.method == 'POST':
        membership.delete()
        messages.success(request, f"{membership.user.username} has been removed from the organization.")
        return redirect('manage_organization_members', slug=organization.slug)
    
    return render(request, 'core/organization/confirm_remove_organization_member.html', {
        'membership': membership,
        'organization': organization
    })

@login_required
def join_organization(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    if not organization.members.filter(id=request.user.id).exists():
        OrganizationMembership.objects.create(organization=organization, user=request.user, role='MEMBER')
        messages.success(request, f"You have joined the organization: {organization.name}")
    else:
        messages.info(request, f"You are already a member of the organization: {organization.name}")
    return redirect('organization_detail', slug=organization.slug)


@login_required
def request_to_join_organization(request, slug):
    user_is_pma_admin = is_pma_admin(request.user)
    if user_is_pma_admin:
        return HttpResponseForbidden("You are not allowed to request to join")
    organization = get_object_or_404(Organization, slug=slug)
    if request.method == 'POST':
        form = OrganizationJoinRequestForm(request.POST)
        if form.is_valid():
            join_request, created = OrganizationJoinRequest.objects.get_or_create(
                user=request.user,
                organization=organization,
                defaults={'status': 'PENDING'}
            )
            if created:
                messages.success(request, f"Your request to join {organization.name} has been submitted.")
            else:
                messages.info(request, f"You have already submitted a request to join {organization.name}.")
            return redirect('organization_detail', slug=organization.slug)
    else:
        form = OrganizationJoinRequestForm()
    return render(request, 'core/organization/request_to_join.html', {'form': form, 'organization': organization})

@login_required
def manage_join_requests(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    if organization.owner != request.user:
        return HttpResponseForbidden("You don't have permission to manage join requests for this organization.")
    
    pending_requests = organization.join_requests.filter(status='PENDING')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(OrganizationJoinRequest, id=request_id, organization=organization)
        
        if action == 'approve':
            join_request.status = 'APPROVED'
            OrganizationMembership.objects.create(organization=organization, user=join_request.user, role='MEMBER')
            messages.success(request, f"{join_request.user.username}'s request to join has been approved.")
        elif action == 'reject':
            join_request.status = 'REJECTED'
            messages.success(request, f"{join_request.user.username}'s request to join has been rejected.")
        
        join_request.save()
        return redirect('manage_join_requests', slug=organization.slug)
    
    return render(request, 'core/organization/manage_join_requests.html', {
        'organization': organization,
        'pending_requests': pending_requests
    })

@login_required
def leave_organization(request, slug):
    organization = get_object_or_404(Organization, slug=slug)
    if request.user == organization.owner:
        return HttpResponseForbidden("Organization owners cannot leave, delete the organization instead.")
        
    if request.method == 'POST':
        OrganizationMembership.objects.filter(
            organization=organization,
            user=request.user
        ).delete()
        messages.success(request, f"You have left {organization.name}")
        return redirect('dashboard')
        
    return render(request, 'core/organization/leave_organization.html', {
        'organization': organization
    })

def organization_feed(request):
    organizations = Organization.objects.filter(feed_visible=True).order_by('-created_at')
    return render(request, 'core/organization/organization_feed.html', {'organizations': organizations})

@login_required
def create_project(request):
    user_is_pma_admin = is_pma_admin(request.user)
    if user_is_pma_admin:
        return HttpResponseForbidden("You are not allowed to create projects.")
    
    if request.method == 'POST':
        project_form = ProjectForm(request.POST)
        
        if project_form.is_valid():
            project = project_form.save(commit=False)
            project.owner = request.user
            project.save()
            ProjectMembership.objects.create(project=project, user=request.user, role='ADMIN', status='APPROVED')
            return redirect('dashboard')
    else:
        project_form = ProjectForm()
    
    user_organizations = request.user.organizations.all()
    project_form.fields['organization'].queryset = user_organizations

    return render(request, 'core/project/create_project.html', {
        'project_form': project_form,
        'user_organizations': user_organizations
    })

def project_feed(request):
    projects = Project.objects.filter(status='active').order_by('-created_at')
    return render(request, 'core/project/project_feed.html', {
        'projects': projects
    })

@login_required
def download_file(request, slug, file_id):
    project = get_object_or_404(Project, slug=slug)
    file = get_object_or_404(File, id=file_id, project=project)
    if project.owner == request.user or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        return FileResponse(file.file, as_attachment=True)
    else:
        return HttpResponseForbidden("You don't have permission to access this file.")

@login_required
def delete_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if is_pma_admin(request.user) or project.owner == request.user:
        if request.method == 'POST':
            project.status = 'deleted'
            project.save()
            return redirect('dashboard')
    else:
        return HttpResponseForbidden("You don't have permission to delete this project.")
    return render(request, 'core/project/confirm_delete_project.html', {'project': project})

@login_required
def delete_file(request, slug, file_id):
    """
    View to handle the deletion of a file associated with a project.
    """
    # Retrieve the project and file
    project = get_object_or_404(Project, slug=slug)
    file = get_object_or_404(File, id=file_id, project=project)

    # Check if the current user has permission to delete the file
    if project.owner != request.user and not (is_pma_admin(request.user)):
        return HttpResponseForbidden("You don't have permission to delete this file.")

    # Handle POST request for deletion
    if request.method == 'POST':
        file.delete()  # Permanently delete the file
        messages.success(request, "File has been deleted successfully.")
        return redirect('project_detail', slug=project.slug) 

    # Render confirmation page for GET request
    return render(request, 'core/project/confirm_delete_file.html', {'file': file, 'project': project})

@login_required
def upload_file(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user != project.owner and not ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        return HttpResponseForbidden("You don't have permission to upload files to this project.")

    if request.method == 'POST':
        form = FileForm(request.POST, request.FILES)
        if form.is_valid():
            file = form.save(commit=False)
            file.project = project
            file.uploaded_by = request.user
            file.name = file.file.name
            file.save()
            messages.success(request, "File uploaded successfully.")
            return redirect('project_detail', slug=project.slug)
    else:
        form = FileForm()

    # ProjectActivity.objects.create(
    #     project=project,
    #     user=request.user,
    #     activity_type='FILE_UPLOAD',
    #     description=f"{request.user.username} uploaded {file.name}"
    # )
        # Example of implementing recenet activity leaving commented out for now
    return render(request, 'core/project/upload_file.html', {'form': form, 'project': project})

@login_required
def edit_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user != project.owner:
        return HttpResponseForbidden("You don't have permission to edit this project.")
    
    if request.method == 'POST':
        form = ProjectForm(request.POST, instance=project)
        if form.is_valid():
            form.save()
            messages.success(request, "Project updated successfully.")
            return redirect('project_detail', slug=project.slug)
    else:
        form = ProjectForm(instance=project)
    
    return render(request, 'core/project/edit_project.html', {'form': form, 'project': project})

@login_required
def project_todos(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user == project.owner or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        todos = project.todo_items.all().order_by('-priority', 'due_date')
        return render(request, 'core/project/project_todos.html', {'project': project, 'todos': todos})
    else:
        return HttpResponseForbidden("You don't have permission to view this project's todos.")

@login_required
def project_calendar(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user == project.owner or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        # events = project.calendar_events.all()
        # return render(request, 'core/project/project_calendar.html', {'project': project, 'events': events})

        # commeneted out to try to fix project specific event calendar 
        return render(request, 'core/project/project_calendar.html', {'project': project})

    else:
        return HttpResponseForbidden("You don't have permission to view this project's calendar.")

@login_required
def get_calendar_events(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user == project.owner or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        events = project.calendar_events.all()
        event_list = [{
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
        } for event in events]
        return JsonResponse(event_list, safe=False)
    else:
        return HttpResponseForbidden("You don't have permission to view this project's events.")


@login_required
def create_event(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user == project.owner or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        if request.method == 'POST':
            form = EventForm(request.POST)
            if form.is_valid():
                event = form.save(commit=False)
                event.project = project
                event.user = request.user
                event.save()
                messages.success(request, "Event created successfully.")
                return redirect('project_detail', slug=project.slug)
        else:
            form = EventForm()
        return render(request, 'core/project/create_event.html', {'form': form, 'project': project})
    else:
        return HttpResponseForbidden("You don't have permission to create events for this project.")

@login_required
def event_detail(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    project = event.project
    
    print(f"Event: {event}, Project: {project}")  # Debug print


    if request.user != event.user and request.user != event.project.owner and not ProjectMembership.objects.filter(project=event.project, user=request.user, status='APPROVED').exists():
        return HttpResponseForbidden("You don't have permission to view this event.")
    
    if request.method == 'POST':
        todo_form = TodoForm(request.POST)
        if todo_form.is_valid():
            todo = todo_form.save(commit=False)
            todo.project = project
            todo.user = request.user
            todo.save()
            print(f"New Todo created: {todo}")  # Debug print
            messages.success(request, "Todo item added successfully.")
            return redirect('event_detail', event_id=event.id)
        else:
            print(f"Form errors: {todo_form.errors}")  # Debug print
    else:
        todo_form = TodoForm()

    todos = project.todo_items.all().order_by('-priority', 'due_date')
    print(f"Todos: {todos}")  # Debug print

    context = {
        'event': event,
        'project': project,
        'todo_form': todo_form,
        'todos': todos,
    }
    return render(request, 'core/project/event_detail.html', context)
    
@login_required
def edit_event(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    
    # Check if the user has permission to edit this event
    if request.user != event.user and request.user != event.project.owner and not ProjectMembership.objects.filter(project=event.project, user=request.user, status='APPROVED').exists():
        return HttpResponseForbidden("You don't have permission to edit this event.")

    if request.method == 'POST':
        form = EventForm(request.POST, instance=event)
        if form.is_valid():
            form.save()
            messages.success(request, "Event updated successfully.")
            return redirect('event_detail', event_id=event.id)
    else:
        form = EventForm(instance=event)
    
    return render(request, 'core/project/edit_event.html', {'form': form, 'event': event})

@login_required
def delete_event(request, event_id):
    event = get_object_or_404(CalendarEvent, id=event_id)
    
    # Check if the user has permission to delete this event
    if request.user != event.user and request.user != event.project.owner and not ProjectMembership.objects.filter(project=event.project, user=request.user, status='APPROVED').exists():
        return HttpResponseForbidden("You don't have permission to delete this event.")

    if request.method == 'POST':
        project_slug = event.project.slug
        event.delete()
        messages.success(request, "Event deleted successfully.")
        return redirect('project_calendar', slug=project_slug)
    
    return render(request, 'core/project/confirm_delete_event.html', {'event': event})
    
@login_required
def manage_members(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.owner != request.user:
        return HttpResponseForbidden("You don't have permission to manage members for this project.")

    if request.method == 'POST':
        form = ProjectMembershipForm(project=project, data=request.POST)
        if form.is_valid():
            user = form.cleaned_data['user']
            role = form.cleaned_data['role']
            ProjectMembership.objects.update_or_create(
                project=project, user=user,
                defaults={'role': role, 'status': 'APPROVED'}
            )
            return redirect('manage_members', slug=project.slug)
    else:
        form = ProjectMembershipForm(project=project)

    memberships = project.memberships.filter(status='APPROVED')
    return render(request, 'core/project/manage_members.html', {
        'project': project,
        'memberships': memberships,
        'form': form
    })

@login_required
def remove_member(request, project_id, user_id):
    project = get_object_or_404(Project, id=project_id)
    if project.owner != request.user:
        return HttpResponseForbidden("You don't have permission to remove members from this project.")

    membership = get_object_or_404(ProjectMembership, project=project, user_id=user_id)
    if request.method == 'POST':
        membership.delete()
        return redirect('manage_members', slug=project.slug)
    
    return render(request, 'core/project/confirm_remove_member.html', {'membership': membership})

@login_required
def request_to_join_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.method == 'POST':
        form = ProjectJoinRequestForm(request.POST)
        if form.is_valid():
            existing_pending_request = ProjectJoinRequest.objects.filter(
                user=request.user,
                project=project,
                status='PENDING',
            ).exists()
            
            if existing_pending_request:
                messages.info(request, f"You have already submitted a request to join {project.title}.")
            else:
                ProjectJoinRequest.objects.filter(user=request.user, project=project).delete()
                join_request = ProjectJoinRequest.objects.create(
                    user=request.user,
                    project=project,
                    status='PENDING',
                    message=form.cleaned_data['message']
                )
                messages.success(request, f"Your request to join {project.title} has been submitted.")
            return redirect('project_detail', slug=project.slug)
    else:
        form = ProjectJoinRequestForm()
    return render(request, 'core/project/request_to_join.html', {'form': form, 'project': project})

@login_required
def manage_project_join_requests(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if project.owner != request.user:
        return HttpResponseForbidden("You don't have permission to manage join requests for this project.")
    
    pending_requests = project.join_requests.filter(status='PENDING')
    
    if request.method == 'POST':
        request_id = request.POST.get('request_id')
        action = request.POST.get('action')
        join_request = get_object_or_404(ProjectJoinRequest, id=request_id, project=project)
        
        if action == 'approve':
            join_request.status = 'APPROVED'
            ProjectMembership.objects.create(
                project=project,
                user=join_request.user,
                role='MEMBER',
                status='APPROVED'
            )
            messages.success(request, f"{join_request.user.username}'s request to join has been approved.")
        elif action == 'reject':
            join_request.status = 'REJECTED'
            messages.success(request, f"{join_request.user.username}'s request to join has been rejected.")
        
        join_request.save()
        return redirect('manage_project_join_requests', slug=project.slug)
    
    return render(request, 'core/project/manage_join_requests.html', {
        'project': project,
        'pending_requests': pending_requests
    })

@login_required
def project_detail(request, slug):
    project = get_object_or_404(Project, slug=slug)
    context = {
        'project': project,
        'is_owner': project.owner == request.user,
        'is_member': project.members.filter(id=request.user.id).exists(),
        'has_pending_request': project.has_pending_request(request.user) if request.user.is_authenticated else False
    }

    # only add these to context if user is authorized
    if is_pma_admin(request.user) or context['is_owner'] or context['is_member']:
        context.update({
            'files': project.files.all(),
            'memberships': project.memberships.filter(status='APPROVED'),
            'todos': project.todo_items.all().order_by('-priority', 'due_date')[:5],
            'upcoming_events': project.calendar_events.filter(
                start_time__gte=timezone.now()
            ).order_by('start_time')[:5],
            'announcements': project.announcements.select_related('user').order_by('-created_at'),
            'budget_items': project.budget_items.all().order_by('-date')[:5],
            'total_income': sum(item.amount for item in project.budget_items.filter(is_expense=True)),
            'total_expenses': sum(item.amount for item in project.budget_items.filter(is_expense=True)),
        })
        # Budget items
        if 'total_income' in context:
            context['budget_balance'] = context['total_income'] - context['total_expenses']

    return render(request, 'core/project/project_detail.html', context)


@login_required
def add_budget_item(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user != project.owner and not ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        return HttpResponseForbidden("You don't have permission to add budget items to this project.")

    if request.method == 'POST':
        form = BudgetItemForm(request.POST)
        if form.is_valid():
            budget_item = form.save(commit=False)
            budget_item.project = project
            budget_item.save()
            messages.success(request, "Budget item added successfully.")
            return redirect('project_detail', slug=project.slug)
    else:
        form = BudgetItemForm()

    return render(request, 'core/project/add_budget_item.html', {'form': form, 'project': project})

@login_required
def create_todo(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user == project.owner or ProjectMembership.objects.filter(project=project, user=request.user, status='APPROVED').exists():
        if request.method == 'POST':
            form = TodoForm(request.POST)
            if form.is_valid():
                todo = form.save(commit=False)
                todo.project = project
                todo.user = request.user
                todo.save()
                messages.success(request, "Todo item created successfully.")
                return redirect('project_detail', slug=project.slug)
        else:
            form = TodoForm()
        return render(request, 'core/project/create_todo.html', {'form': form, 'project': project})
    else:
        return HttpResponseForbidden("You don't have permission to create todos for this project.")

@login_required
@xframe_options_exempt
def file_preview(request, file_id):
    file = get_object_or_404(File, id=file_id)
    project = file.project

    file_name, file_extension = os.path.splitext(file.name)
    file_extension = file_extension.lower()
    mime_type, _ = mimetypes.guess_type(file.name)

    context = {
        'project': project,
        'is_owner': project.owner == request.user,
        'is_member': project.members.filter(id=request.user.id).exists(),
        'file': file
    }
    if not (is_pma_admin(request.user) or context['is_owner'] or context['is_member']):
        return HttpResponseForbidden("You don't have permission to view this project.")

    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
        Params={'Bucket': settings.AWS_STORAGE_BUCKET_NAME,
                                                            'Key': file.file.name},
                                                    ExpiresIn=3600)
    except ClientError as e:
        print(e)
        return HttpResponse("Error generating file URL", status=500)

    context['file_url'] = response

    if file_extension == '.pdf':
        context.update({'file_url': file.file.url, 'file_type': 'pdf'})
        return render(request, 'core/project/file_preview.html', context)
    
    #Image files
    elif file_extension in ['.png', '.jpg', '.jpeg', '.gif', '.bmp']:
        context.update({'file_url': file.file.url, 'file_type': 'image'})
        return render(request, 'core/project/file_preview.html', context)

    # Text files
    elif file_extension in ['.txt', '.py', '.js', '.html', '.css', '.json', '.xml']:
        with file.file.open() as f:
            content = f.read().decode('utf-8')
        context.update({'file_content': content, 'file_type': 'text'})
        return render(request, 'core/project/file_preview.html', context)
    
    elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        google_viewer_url = f"https://docs.google.com/viewer?url={urllib.parse.quote(response)}&embedded=true"
        context.update({
            'file_url': google_viewer_url,
            'file_type': 'office',
            'mime_type': mime_type
        })
        return render(request, 'core/project/file_preview.html', context)
    # Not working for some reason not sure why
    # Office docs (Word, Excel, PowerPoint)
    #elif file_extension in ['.doc', '.docx', '.xls', '.xlsx', '.ppt', '.pptx']:
        #context.update({'file_url': file.file.url, 'file_type': 'office', 'mime_type': mime_type})
        #return render(request, 'core/project/file_preview.html', context)

    # Audio files
    elif file_extension in ['.mp3', '.wav', '.ogg']:
        context.update({'file_url': file.file.url, 'file_type': 'audio'})
        return render(request, 'core/project/file_preview.html', context)

    # Video files
    elif file_extension in ['.mp4', '.webm', '.ogg']:
        context.update({'file_url': file.file.url, 'file_type': 'video'})
        return render(request, 'core/project/file_preview.html', context)

    else:
        context.update({'file_type': 'unsupported'})
        return render(request, 'core/project/file_preview.html', context)
    

def get_office_online_viewer_url(file_url, file_extension):
    encoded_url = urllib.parse.quote(file_url)
    
    if file_extension in ['.doc', '.docx']:
        return f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
    elif file_extension in ['.xls', '.xlsx']:
        return f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
    elif file_extension in ['.ppt', '.pptx']:
        return f"https://view.officeapps.live.com/op/embed.aspx?src={encoded_url}"
    else:
        return file_url
    
@login_required
def user_profile(request, username):
    user = get_object_or_404(User, username=username)
    return render(request, 'core/user/user_profile.html', {'user': user})
'''
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)
'''
@login_required
def my_profile(request):
    return redirect('user_profile', username=request.user.username)

@login_required
def edit_profile(request, username):
    logger.debug(f"User: {username}")
    logger.debug(f"User: {request.user.username}")
    try:
        # Attempt to retrieve the user's profile
        # user_profile = request.user.userprofile
        user_profile = UserProfile.objects.get(user__username=username)
    except UserProfile.DoesNotExist:
        logger.warning("UserProfile does not exist for the user.")
        messages.error(request, "Profile does not exist. Please create one first.")
        return redirect('create_profile')  # Redirect to the profile create page
    
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=user_profile)
        if form.is_valid():
            form.save()
            messages.success(request, 'Your profile has been updated successfully.')
            return redirect('user_profile', username=username)
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = UserProfileForm(instance=user_profile)

    return render(request, 'core/user/edit_profile.html', {'form': form})

def search(request):
    query = request.GET.get('q')
    results = []
    if query:
        for user in User.objects.all():
            if any(query.lower() in field.lower() for field in user.userprofile.search_fields):
                results.append(user)
        
        for org in Organization.objects.all():
            if any(query.lower() in field.lower() for field in org.search_fields):
                results.append(org)
        
        for project in Project.objects.filter(status='active'):
            if any(query.lower() in field.lower() for field in project.search_fields):
                results.append(project)

        for file in File.objects.all():
            if any(query.lower() in field.lower() for field in file.search_fields):
                results.append(file)
                
    return render(request, 'core/search_results.html', {'results': results, 'query': query})

@login_required
def get_calendar_events(request):
    start = request.GET.get('start')
    end = request.GET.get('end')
    events = CalendarEvent.objects.filter(user=request.user, start_time__range=[start, end])
    event_list = []
    for event in events:
        event_list.append({
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'url': f'/event/{event.id}/'  # need to create this view
        })
    return JsonResponse(event_list, safe=False)

import logging

logger = logging.getLogger(__name__)

@login_required
@require_POST
@csrf_protect
def create_calendar_event(request):
    try:
        data = json.loads(request.body)
        logger.debug(f"Received data: {data}")  # Log received data
        project = get_object_or_404(Project, id=data['project_id'])

        if not (project.owner == request.user or project.members.filter(id=request.user.id).exists()):
            return JsonResponse({'error': 'Permission denied'}, status=403)

        try:
            start_time = timezone.make_aware(datetime.strptime(data['start'], '%Y-%m-%dT%H:%M'))
            end_time = timezone.make_aware(datetime.strptime(data['end'], '%Y-%m-%dT%H:%M'))
        except ValueError as e:
            return JsonResponse({'error': f'Invalid date format: {str(e)}'}, status=400)
        
        event = CalendarEvent.objects.create(
            project=project,
            user=request.user,
            title=data.get('title'),
            start_time=start_time,
            end_time=end_time, 
            description=data.get('description', ''),
            location=data.get('location', '')
        )
        
        return JsonResponse({
            'id': event.id,
            'title': event.title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'description': event.description
        }, status=200)

    except KeyError as e:
        logger.error(f"Missing required field: {str(e)}")  # Log missing field
        return JsonResponse({'error': f'Missing required field: {str(e)}'}, status=400)
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")  # Log other errors
        return JsonResponse({'error': str(e)}, status=500)


def project_feed(request):
    projects = Project.objects.exclude(status='deleted')
    
    # Apply filters
    status = request.GET.get('status')
    priority = request.GET.get('priority')
    search = request.GET.get('search')
    sort = request.GET.get('sort', '-created_at')
    
    if status and status != 'all':
        projects = projects.filter(status=status)
    if priority and priority != 'all':
        projects = projects.filter(priority=priority)
    if search:
        projects = projects.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Apply sorting
    if sort == 'name-asc':
        projects = projects.order_by('title')
    elif sort == 'name-desc':
        projects = projects.order_by('-title')
    elif sort == 'date-asc':
        projects = projects.order_by('created_at')
    elif sort == 'date-desc':
        projects = projects.order_by('-created_at')
    
    return render(request, 'core/project/project_feed.html', {
        'projects': projects,
        'current_filters': {
            'status': status or 'all',
            'priority': priority or 'all',
            'search': search or '',
            'sort': sort
        }
    })

def organization_feed(request):
    organizations = Organization.objects.filter(feed_visible=True)
    
    # Apply filters
    category = request.GET.get('category')
    size = request.GET.get('size')
    search = request.GET.get('search')
    sort = request.GET.get('sort', '-created_at')
    
    if category and category != 'all':
        organizations = organizations.filter(category=category)
    if size and size != 'all':
        organizations = organizations.filter(size=size)
    if search:
        organizations = organizations.filter(
            Q(name__icontains=search) |
            Q(description__icontains=search)
        )
    
    # Apply sorting
    if sort == 'name-asc':
        organizations = organizations.order_by('name')
    elif sort == 'name-desc':
        organizations = organizations.order_by('-name')
    elif sort == 'date-asc':
        organizations = organizations.order_by('created_at')
    elif sort == 'date-desc':
        organizations = organizations.order_by('-created_at')
    
    return render(request, 'core/organization/organization_feed.html', {
        'organizations': organizations,
        'current_filters': {
            'category': category or 'all',
            'size': size or 'all',
            'search': search or '',
            'sort': sort
        }
    })

@login_required
def post_announcement(request, project_slug):
    project = get_object_or_404(Project, slug=project_slug)

    if request.method == 'POST':
        form = AnnouncementForm(request.POST)
        if form.is_valid():
            announcement = form.save(commit=False)
            announcement.user = request.user
            announcement.project = project
            announcement.save()
            return redirect('project_detail', slug=project.slug)
        else:
            print("Form errors:", form.errors)
    else:
        form = AnnouncementForm()

    return render(request, 'core/project/post_announcement.html', {'form': form, 'project': project})

def leave_project(request, slug):
    project = get_object_or_404(Project, slug=slug)
    if request.user in project.members.all():
        project.members.remove(request.user)
        messages.success(request, "You have left the project successfully.")
    else:
        messages.error(request, "You are not a member of this project.")
    return redirect('dashboard')