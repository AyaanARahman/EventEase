from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path

from core import views

"""
URL configuration for mysite project.

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
from django.urls import include, path

urlpatterns = [
    path('admin/', admin.site.urls),
    path('accounts/', include('allauth.urls')),
    path('', views.home, name='home'),
    path('dashboard/', views.dashboard, name='dashboard'),

    # Admin routes
    path('admin/projects/', views.admin_project_list, name='admin_project_list'),
    path('admin/analytics/', views.admin_analytics, name='admin_analytics'),
    path('generate-report/', views.generate_report, name='generate_report'),
    path('send-newsletter/', views.send_newsletter, name='send_newsletter'),

    # User routes
    path('profile/', views.my_profile, name='my_profile'),
    path('profile/<str:username>/', views.user_profile, name='user_profile'),
    path('profile/edit/<str:username>/', views.edit_profile, name='edit_profile'),

    # Project routes
    path('create-project/', views.create_project, name='create_project'),
    path('projects/feed/', views.project_feed, name='project_feed'),    path('project/<slug:slug>/', views.project_detail, name='project_detail'),
    path('project/<slug:slug>/edit/', views.edit_project, name='edit_project'),
    path('project/<slug:slug>/todos/', views.project_todos, name='project_todos'),
    path('project/<slug:slug>/calendar/', views.project_calendar, name='project_calendar'),
    path('project/<slug:slug>/events/', views.get_calendar_events, name='get_calendar_events'),
    path('create_calendar_event/', views.create_calendar_event, name='create_calendar_event'),
    path('project/<slug:slug>/create-todo/', views.create_todo, name='create_todo'),
    path('project/<slug:slug>/create-event/', views.create_event, name='create_event'),
    path('projects/<str:slug>/create-calendar-event/', views.create_calendar_event, name='create_calendar_event'),
    path('project/<slug:slug>/download/<int:file_id>/', views.download_file, name='download_file'),
    path('project/<slug:slug>/delete/', views.delete_project, name='delete_project'),
    path('project/<slug:slug>/delete-file/<int:file_id>/', views.delete_file, name='delete_file'),
    path('project/<slug:slug>/upload-file/', views.upload_file, name='upload_file'),
    path('project/<slug:slug>/manage-members/', views.manage_members, name='manage_members'),
    path('project/<int:project_id>/remove-member/<int:user_id>/', views.remove_member, name='remove_member'),
    path('file-preview/<int:file_id>/', views.file_preview, name='file_preview'),
    path('project/<slug:slug>/add-budget-item/', views.add_budget_item, name='add_budget_item'),
    path('projects/<slug:project_slug>/post_announcement/', views.post_announcement, name='post_announcement'),
    path('project/<slug:slug>/leave/', views.leave_project, name='leave_project'),
    path('projects/<slug:slug>/join/', views.request_to_join_project, name='request_to_join_project'),
    path('projects/<slug:slug>/manage-requests/', views.manage_project_join_requests, name='manage_project_join_requests'),

    # Event routes
    path('event/<int:event_id>/', views.event_detail, name='event_detail'),
    path('event/<int:event_id>/edit/', views.edit_event, name='edit_event'),
    path('event/<int:event_id>/delete/', views.delete_event, name='delete_event'),

    # Organization routes
    path('create-organization/', views.create_organization, name='create_organization'),
    path('organization/<slug:slug>/', views.organization_detail, name='organization_detail'),
    path('organizations/<slug:slug>/manage/', views.manage_organization, name='manage_organization'),
    path('organization/<slug:slug>/memberss/', views.manage_organization_members, name='manage_organization_members'),
    path('organization/<slug:slug>/remove-member/<int:user_id>/', views.remove_organization_member, name='remove_organization_member'),
    path('organization/<slug:slug>/join/', views.join_organization, name='join_organization'),
    path('organizations/<slug:slug>/request-to-join/', views.request_to_join_organization, name='request_to_join_organization'),
    path('organizations/<slug:slug>/manage-join-requests/', views.manage_join_requests, name='manage_join_requests'),
    path('organizations/<slug:slug>/leave/', views.leave_organization, name='leave_organization'),
    path('organizations/feed/', views.organization_feed, name='organization_feed'),

    # Miscellaneous rotes
    path('search/', views.search, name='search'),
    path('get_calendar_events/', views.get_calendar_events, name='get_calendar_events'),
    path('create_calendar_event/', views.create_calendar_event, name='create_calendar_event'),
    path('logout/', views.logout_view, name='logout'),
    path('file_preview/<int:file_id>/', views.file_preview, name='file_preview'),

    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
