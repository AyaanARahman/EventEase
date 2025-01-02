from django.contrib import admin
from django.contrib.auth.models import User
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import CalendarEvent, TodoItem, UserProfile, Project, Announcement

admin.site.register(UserProfile)
admin.site.register(Project)
admin.site.register(Announcement)

# Register your models here.
@admin.register(CalendarEvent)
class CalendarEventAdmin(admin.ModelAdmin):
    list_display = ('title', 'start_time', 'end_time', 'user', 'project')
    list_filter = ('user', 'project')
    search_fields = ('title', 'description')

@admin.register(TodoItem)
class TodoItemAdmin(admin.ModelAdmin):
    list_display = ('title', 'due_date', 'priority', 'completed', 'user', 'project')
    list_filter = ('completed', 'priority', 'user', 'project')
    search_fields = ('title', 'description')


class UserProfileInline(admin.StackedInline):
    model = UserProfile
    can_delete = False
    verbose_name_plural = 'User Profile'

class UserAdmin(BaseUserAdmin):
    inlines = (UserProfileInline,)

# Re-register UserAdmin
admin.site.unregister(User)
admin.site.register(User, UserAdmin)