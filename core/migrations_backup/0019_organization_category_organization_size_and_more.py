# Generated by Django 5.1.1 on 2024-11-14 04:23

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0018_merge_20241108_2336'),
    ]

    operations = [
        migrations.AddField(
            model_name='organization',
            name='category',
            field=models.CharField(choices=[('academic', 'Academic'), ('professional', 'Professional'), ('social', 'Social'), ('other', 'Other')], default='other', max_length=20),
        ),
        migrations.AddField(
            model_name='organization',
            name='size',
            field=models.CharField(choices=[('small', '1-10'), ('medium', '11-50'), ('large', '51+')], default='small', max_length=20),
        ),
        migrations.AddField(
            model_name='project',
            name='priority',
            field=models.CharField(choices=[('low', 'Low'), ('medium', 'Medium'), ('high', 'High')], default='medium', max_length=10),
        ),
    ]