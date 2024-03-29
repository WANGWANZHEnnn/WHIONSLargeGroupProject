import logging
from celery import shared_task
from django.utils import timezone
from .models import FlowerGrowth, JournalEntry
from django.core.mail import send_mail
from .models import UserPreferences
from datetime import datetime
import task_manager.settings as settings 
from datetime import timedelta
import time
from django.core.mail import EmailMultiAlternatives


""" Contains tasks that will be scheduled by Celery 
Will reset flower growth when a day of journalling is missed and at the start of the week 
To run:
    redis-server
    celery -A task_manager inspect registered
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
"""

@shared_task(bind=True, max_retries=3)
def send_reminder_emails(self, user_email):
    try:
        subject = 'Reminder: Journal Entry'
        text_content = "Hello,\n\nThis is a friendly reminder to make your journal entry for today. Thank you!"
        msg = EmailMultiAlternatives(subject, text_content, settings.EMAIL_FROM, [user_email])
        msg.send()
    except Exception as exc:
        self.retry(exc=exc)

@shared_task
def check_and_trigger_reminder_emails():
    today = datetime.now().strftime('%A').lower()
    user_preferences = UserPreferences.objects.filter(**{f"{today}": True})
    
    for index, preference in enumerate(user_preferences):
        if preference.opt_out:
            continue
        # we have to introduce a delay to avoid sending all emails at the same time, due to the capacity of the email server we are using in the scope of our project
        # in an ideal world, we would change the service so that it can handle a large number of emails at once
        scheduled_time = datetime.combine(datetime.today(), preference.journal_time) + timedelta(seconds=index * 10) 
        logging.info(f"Scheduling reminder for {preference.user.email} at {scheduled_time}")
        
        try:
            send_reminder_emails.apply_async(args=[preference.user.email], eta=scheduled_time)
        except Exception as e:
            logging.error(f"Failed to schedule reminder for {preference.user.email}: {e}")
    



