# accounts/signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.mail import send_mail
from .models import User

@receiver(post_save, sender=User)
def send_welcome_email(sender, instance, created, **kwargs):
    if created:  # only on new user creation
        subject = "Welcome to Grievance Redressal System"
        message = f"Hi {instance.username},\n\nThank you for registering! Your account has been successfully created."
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [instance.email]
        
        # send email
        send_mail(subject, message, from_email, recipient_list)
