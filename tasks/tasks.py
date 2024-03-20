from celery import shared_task
from django.utils import timezone
from .models import FlowerGrowth, JournalEntry
from django.core.mail import send_mail
from .models import UserPreferences
from datetime import datetime
import task_manager.settings as settings 

""" Contains tasks that will be scheduled by Celery 
Will reset flower growth when a day of journalling is missed and at the start of the week 
To run:
    redis-server
    celery -A task_manager worker -l info
    celery -A task_manager beat -l info
"""
@shared_task
def reset_flower_growth_weekly():
    FlowerGrowth.objects.all().update(stage=0, last_entry_date=timezone.now().date())
    
@shared_task
def check_and_reset_growth_daily():
    today = timezone.now().date()
    users_with_entries_yesterday = JournalEntry.objects.filter(
        created_at__date=today - timezone.timedelta(days=1)
    ).values_list('user', flat=True).distinct()

    FlowerGrowth.objects.exclude(user__in=users_with_entries_yesterday).update(stage=0)
    
""" Contains tasks that will be scheduled by Celery 
Will send out reminder emails based on user preferences 
To run:
    redis-server
    celery -A task_manager worker -l info
    celery -A task_manager beat -l info
"""
@shared_task
def send_reminder_emails(user_email):
    send_mail(
        'Reminder: Journal Entry',
        'Don\'t forget to make your journal entry today!',
        settings.EMAIL_FROM, 
        [user_email],
        fail_silently=False,
    )

@shared_task
def check_and_trigger_reminder_emails():
    # Get today's day of the week
    today = datetime.now().strftime('%A').lower()

    # Get user preferences for the current day
    user_preferences = UserPreferences.objects.filter(**{f"{today}": True})
    
    # Trigger reminders for users who have selected the current day
    for preference in user_preferences:
        scheduled_time = datetime.combine(datetime.today(), preference.journal_time)
        send_reminder_emails.apply_async(args=[preference.user.email], eta=scheduled_time)

