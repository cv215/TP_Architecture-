# users/tasks.py
from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_welcome_email(email, username):
    subject = "Bienvenue sur notre site"
    message = f"Bonjour {username}, merci de votre inscription !"
    send_mail(
        subject,
        message,
        "ton_adresse@gmail.com",  # expéditeur
        [email],
        fail_silently=False,
    )
