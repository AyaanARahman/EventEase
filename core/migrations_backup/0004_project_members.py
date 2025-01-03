# Generated by Django 5.1.1 on 2024-09-30 03:28

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0003_remove_project_members_projectmembership'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='members',
            field=models.ManyToManyField(related_name='projects', through='core.ProjectMembership', to=settings.AUTH_USER_MODEL),
        ),
    ]
