import os
from django.core.mail import send_mail
from django.utils import timezone
from .models import TodoItem
from django.conf import settings
from celery import shared_task
import logging

logger = logging.getLogger(__name__)


@shared_task
def send_due_date_reminders():
    logger.info("Task started.")
    current_time = timezone.now()
    time_window = current_time + timezone.timedelta(days=1)
    logger.info(f"Current time: {current_time}, Time window: {time_window}")

    tasks_due_soon = TodoItem.objects.filter(due_date__range=(current_time, time_window))
    logger.info(f"Tasks found: {[task.title for task in tasks_due_soon]}")

    for task in tasks_due_soon:
        if task.user.email:
            logger.info(f"Sending email to {task.user.email} for task '{task.title}' due on {task.due_date}")
            send_mail(
                subject=f"Reminder: '{task.title}' is due soon!",
                message=f"Dear {task.user.username}, your task '{task.title}' is due on {task.due_date}.",
                from_email=os.environ.get('EMAIL_HOST_USER'),
                recipient_list=[task.user.email],
            )
            logger.info(f"Email sent to {task.user.email} for task: {task.title}")
        else:
            logger.warning(f"No email for user {task.user.username} for task: {task.title}")