# Generated by Django 5.1.1 on 2024-09-30 03:21

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0002_project_file'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='members',
        ),
        migrations.CreateModel(
            name='ProjectMembership',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('role', models.CharField(choices=[('MEMBER', 'Member'), ('EDITOR', 'Editor'), ('ADMIN', 'Admin')], default='MEMBER', max_length=10)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='memberships', to='core.project')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='project_memberships', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'unique_together': {('project', 'user')},
            },
        ),
    ]
