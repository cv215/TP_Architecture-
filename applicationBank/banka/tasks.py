from celery import shared_task
from django.core.mail import send_mail
from .models import Message
from .models import Transaction
from django.contrib.auth.models import User
from django.conf import settings

@shared_task
def send_registration_email(user_email):
    subject = "Bienvenue sur SecuryBank"
    message = (
        f"Bonjour,\n\n"
        "Votre inscription sur la plateforme SecuryBank a été validée avec succès.\n"
        "Vous pouvez désormais profiter de nos services bancaires sécurisés.\n\n"
        "L’équipe SecuryBank."
    )
    send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        [user_email],
        fail_silently=False,
    )



@shared_task
def handle_message_created(message_id):
    message = Message.objects.get(id=message_id)
    print(f"New message from {message.sender}: {message.content}")

@shared_task
def handle_message_replied(message_id):
    message = Message.objects.get(id=message_id)
    print(f"Admin replied: {message.content}")
    


@shared_task
def handle_transaction_created(transaction_id):
    transaction = Transaction.objects.get(id=transaction_id)
    print(f"Event: TransactionCreated - {transaction.user.username} {transaction.transaction_type} {transaction.amount}")
    

from django.core.mail import send_mail
from django.conf import settings

@shared_task
def handle_fraud_detected(user_id, transaction_id):
    user = User.objects.get(id=user_id)
    tx = Transaction.objects.get(id=transaction_id)
    print(f"⚠️ FRAUDE détectée : {user.username} a échoué 5 fois. Transaction {tx.id} bloquée.")

    send_mail(
        subject="Alerte fraude sur votre compte",
        message=(
            f"Bonjour {user.username},\n\n"
            "Votre transaction a été bloquée car vous avez atteint 5 tentatives échouées "
            "pour solde insuffisant. Cela est considéré comme une fraude potentielle.\n"
            "Veuillez contacter l’administrateur pour régulariser la situation."
        ),
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    
# tasks.py
from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth.models import User

@shared_task
def envoyer_alerte_fraude(user_id, type_compte):
    user = User.objects.get(id=user_id)
    message = (
        f"Alerte fraude : L'utilisateur {user.username} a tenté de créer "
        f"un deuxième compte {type_compte}."
    )
    # Exemple : envoi d'un email à l'admin
    send_mail(
        subject="Alerte fraude - Tentative de double compte",
        message=message,
        from_email="tangoua8@gmail.com",
        recipient_list=["admin@banque.com"],
    )

