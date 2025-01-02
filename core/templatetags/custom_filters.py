from django import template
from django.contrib.auth.models import User
from core.models import Organization, Project 

register = template.Library()

@register.filter
def isinstance_of(value, class_name):
    if class_name == 'User':
        return isinstance(value, User)
    elif class_name == 'Organization':
        return isinstance(value, Organization)
    elif class_name == 'Project':
        return isinstance(value, Project)
    return False