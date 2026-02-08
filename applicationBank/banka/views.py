from mailbox import Message
from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages

from .tasks import send_registration_email
from .models import Compte, Transaction, Event, AuditLog
from django.contrib.auth.decorators import user_passes_test, login_required
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Event, AuditLog,Role,Profile,Transaction
from django.utils.timezone import now
from datetime import timedelta
from django.db.models import Sum

from banka import models

# Create your views here.

def index(request):
    return render(request, 'banka/index.html')

def login_user(request):
    roles = Role.objects.all()
    
    if request.method == "POST":
        username = request.POST.get("email")
        password = request.POST.get("password")
        role_id = request.POST.get("role")

        user = authenticate(request, username=username, password=password)

        if user is not None:

           if str(user.role.id) == str(role_id): 
               login(request, user) 
               if user.role.nom == "Administrateur": 
                   return redirect("acceuilAdmin") 
               else: 
                   return redirect("acceuilClient") 
           else: 
                messages.error(request, "Le rôle sélectionné est incorrect.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

    return render(request, "banka/login.html", {"roles": roles})

def register_user(request):
    if request.method == "POST":
        nom = request.POST["nom"]
        prenom = request.POST["prenom"]
        age = request.POST["age"]
        adresse = request.POST["adresse"]
        telephone = request.POST["telephone"]
        email = request.POST["email"]
        ville = request.POST["ville"]
        pays = request.POST["pays"]
        role_name = request.POST["role"]
        password1 = request.POST["password1"]
        password2 = request.POST["password2"]

        if password1 != password2:
            messages.error(request, "Les mots de passe ne correspondent pas")
            return redirect("register")

        if User.objects.filter(nom=nom).exists() and User.objects.filter(prenom=prenom).exists():
            messages.error(request, "il y a un utilisateur qui porte exactement le même nom et prénom")
            return redirect("register")

        if User.objects.filter(email=email).exists():
            messages.error(request, "Cet email est déjà utilisé")
            return redirect("register")
        
        role_instance, created = Role.objects.get_or_create(nom=role_name)

        user = User.objects.create_user(
            nom=nom, 
            prenom=prenom,
            age=age,
            adresse=adresse,
            ville=ville,
            pays=pays,
            email=email, 
            role = role_instance,
            password=password1)
        user.save()
        # Déclenche la tâche Celery → RabbitMQ 
        send_registration_email.delay(user.email)

        messages.success(request, "Inscription réussie ! Vérifiez votre email pour confirmation.")
        return redirect("login")

    return render(request, "banka/register.html")

@receiver(post_save, sender=User)
def user_created_event(sender, instance, created, **kwargs):
    if created:
        # Créer un événement
        event = Event.objects.create(
            nom="USER_CREATED",
            source_service="UserService",
            description=f"Nouvel utilisateur créé: {instance.email}",
            date_debut=instance.date_creation,
            date_fin=instance.date_creation
        )
        # Créer un audit log lié
        AuditLog.objects.create(
            utilisateur=instance,
            event=event,
            action="Création utilisateur",
            details=f"Utilisateur {instance.email} créé avec rôle {instance.role.nom}"
        )

@receiver(post_save, sender=Transaction)
def transaction_event(sender, instance, created, **kwargs):
    if created:
        event = Event.objects.create(
            nom="TRANSACTION_CREATED",
            source_service="TransactionService",
            description=f"Transaction de {instance.montant} du compte {instance.compte_source.numero_compte} vers {instance.compte_destination.numero_compte}",
            date_debut=instance.date_transaction,
            date_fin=instance.date_transaction
        )
        AuditLog.objects.create(
            utilisateur=instance.compte_source.proprietaire,
            event=event,
            action="Transaction effectuée",
            details=f"Montant: {instance.montant}, statut: {instance.statut}"
        )

def is_admin(user): 
    return user.role.nom == "Administrateur" 

@user_passes_test(is_admin)
def index_admin(request):
    today = now().date()
    last_week = today - timedelta(days=6)

    nb_comptes = Compte.objects.count()
    
    nb_transactions = Transaction.objects.filter(date_transaction__date=today).count()

    total_depots = Transaction.objects.filter(
        type_transaction="depot", date_transaction__date=today).aggregate(total=Sum("montant"))["total"] or 0

    total_retraits = Transaction.objects.filter(
        type_transaction="retrait", date_transaction__date=today
    ).aggregate(total=Sum("montant"))["total"] or 0

    total_virements = Transaction.objects.filter(
        type_transaction="virement", date_transaction__date=today
    ).aggregate(total=Sum("montant"))["total"] or 0

    nb_alertes = Transaction.objects.filter(fraud_alerts=True).count()

    transactions = (
        Transaction.objects.filter(date_transaction__date__gte=last_week)
        .values("date_transaction__date", "type_transaction")
        .annotate(total=Sum("montant"))
        .order_by("date_transaction__date")
    )

    labels = sorted(set([t["date_transaction__date"].strftime("%d/%m") for t in transactions]))
    depots, retraits, virements = [], [], []
    for label in labels:
        depots.append(sum(t["total"] for t in transactions if t["date_transaction__date"].strftime("%d/%m") == label and t["type_transaction"]=="depot"))
        retraits.append(sum(t["total"] for t in transactions if t["date_transaction__date"].strftime("%d/%m") == label and t["type_transaction"]=="retrait"))
        virements.append(sum(t["total"] for t in transactions if t["date_transaction__date"].strftime("%d/%m") == label and t["type_transaction"]=="virement"))

    context = {
        "nb_comptes": nb_comptes,
        "nb_transactions": nb_transactions,
        "total_depots": total_depots,
        "total_retraits": total_retraits,
        "total_virements": total_virements,
        "nb_alertes": nb_alertes,
        "labels": labels,
        "depots": depots,
        "retraits": retraits,
        "virements": virements,
    }
    return render(request, "banka/index_admin.html", context)


@login_required
def comptes(request):

    comptes_user = Compte.objects.filter(proprietaire=request.user)
    context = { "comptes": comptes_user }
    return render(request, 'banka/comptes.html', context)

def transactions(request):
    transactions_user = Transaction.objects.filter(compte_source__proprietaire=request.user).order_by('-date_transaction')
    context = { "transactions": transactions_user }
    return render(request, 'banka/transactions.html', context)

def messageries(request):
    return render(request, 'banka/messageries.html')

@login_required
def transaction_retrait(request):
    solde = request.user.profile.solde  # Exemple: solde stocké dans le profil utilisateur
    profile, created = Profile.objects.get_or_create(user=request.user)
    
    if request.method == "POST":
        try:
            montant = float(request.POST.get("montant"))
            operateur = request.POST.get("operateur")  # "mtn" ou "orange"
            numero = request.POST.get("numero")       # numéro du bénéficiaire
        except (TypeError, ValueError):
            messages.error(request, "Montant invalide.")
            return redirect("transaction_retrait")

        if montant <= 0:
            messages.error(request, "Le montant doit être supérieur à zéro.")
        elif montant > solde:
            messages.error(request, f"Impossible d'effectuer le retrait car vous n'avez que {solde} FCFA dans votre compte.")
        elif not numero or len(numero) < 8:
            messages.error(request, "Veuillez saisir un numéro valide.")
        else:
            # Ici tu intègres l’API MTN ou Orange Money
            if operateur == "mtn":
                # appel API MTN Money
                messages.success(request, f"Retrait de {montant} FCFA vers {numero} via MTN Money effectué avec succès.")
            elif operateur == "orange":
                # appel API Orange Money
                messages.success(request, f"Retrait de {montant} FCFA vers {numero} via Orange Money effectué avec succès.")
            else:
                messages.error(request, "Opérateur non reconnu.")
            
            # Mise à jour du solde
            request.user.profile.solde -= montant
            request.user.profile.save()

        return redirect("transaction_retrait")

    return render(request, "transactions/retrait.html", {"solde": solde})


# --- Vue Django --- 
@login_required 
def transaction_depot(request): 
    if request.method == "POST": 
        try: 
            montant = float(request.POST.get("montant")) 
            operateur = request.POST.get("operateur") 
            numero = request.POST.get("numero") 
        except (TypeError, ValueError):
            messages.error(request, "Montant invalide.") 
            return redirect("transaction_depot") 
        if montant <= 0: 
            messages.error(request, "Le montant doit être supérieur à zéro.") 
        elif not numero or len(numero) < 8: 
            messages.error(request, "Veuillez saisir un numéro valide.") 
        else: 
            if operateur == "mtn": 
                status, result = depot_mtn(numero, montant) 
                
                if status == 202: 
                    messages.success(request, f"Dépôt de {montant} FCFA depuis {numero} via MTN Money effectué avec succès.") 
                    request.user.profile.solde += montant 
                    request.user.profile.save() 
                else: 
                    messages.error(request, f"Erreur MTN Money: {result}") 
                
            elif operateur == "orange": 
                status, result = depot_orange(numero, montant) 
                if status == 200: 
                    messages.success(request, f"Dépôt de {montant} FCFA depuis {numero} via Orange Money effectué avec succès.") 
                    request.user.profile.solde += montant 
                    request.user.profile.save() 
                else: 
                    messages.error(request, f"Erreur Orange Money: {result}") 
            else: 
                messages.error(request, "Opérateur non reconnu.") 
                return redirect("transaction_depot") 
    return render(request, "transactions/depot.html")

@login_required
def transaction_virement(request):
    return render(request, "transactions/virement.html")

import random

@login_required
def creer_compte(request):
    if request.method == "POST":
        type_compte = request.POST.get("type")
        solde_initial = request.POST.get("solde")
        currency = request.POST.get("currency", "XAF")  # valeur par défaut si non fourni

        # Génération d'un numéro de compte aléatoire (16 chiffres)
        nombre = ""
        for i in range(16):
            aleatoire = random.randint(0, 9)
            nombre += str(aleatoire)

        # Création du compte
        Compte.objects.create(
            proprietaire=request.user,
            type=type_compte,
            solde=solde_initial,
            numero_compte=nombre,
            status="actif",
            currency=currency
        )

        messages.success(request, f"Compte créé avec succès en {currency}.")
        return redirect("mes_comptes")
    # Texte d’avertissement envoyé au template 
    warning_text = ( "⚠️ Important : Seuls les comptes courants sont autorisés à effectuer des virements. " "Toute tentative de virement avec un compte épargne constitue une violation des règles " "et votre transaction sera automatiquement bloquée." )

    return render(request, "comptes/creer_compte.html", {"warning_text": warning_text})


import requests

def retrait_mtn(numero, montant):
    # Credentials (à récupérer via MTN Developer Portal)
    subscription_key = "TON_SUBSCRIPTION_KEY"
    api_user = "TON_API_USER"
    api_key = "TON_API_KEY"
    base_url = "https://sandbox.momodeveloper.mtn.com"

    # 1. Obtenir un token
    token_url = f"{base_url}/collection/token/"
    headers = {
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Authorization": f"Basic {api_user}:{api_key}"
    }
    token_response = requests.post(token_url, headers=headers)
    access_token = token_response.json().get("access_token")

    # 2. Initier la transaction
    request_url = f"{base_url}/collection/v1_0/requesttopay"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "X-Reference-Id": "transaction12345",  # ID unique
        "X-Target-Environment": "sandbox",
        "Ocp-Apim-Subscription-Key": subscription_key,
        "Content-Type": "application/json"
    }
    body = {
        "amount": str(montant),
        "currency": "XAF",
        "externalId": "123456",
        "payer": {
            "partyIdType": "MSISDN",
            "partyId": numero
        },
        "payerMessage": "Retrait",
        "payeeNote": "Retrait via MTN Money"
    }
    response = requests.post(request_url, headers=headers, json=body)

    return response.status_code, response.json()

def retrait_orange(numero, montant):
    base_url = "https://api.orange.com/orange-money-webpay/cm/v1"
    client_id = "TON_CLIENT_ID"
    client_secret = "TON_CLIENT_SECRET"

    # 1. Obtenir un token
    token_url = "https://api.orange.com/oauth/v2/token"
    data = {"grant_type": "client_credentials"}
    headers = {"Authorization": f"Basic {client_id}:{client_secret}"}
    token_response = requests.post(token_url, data=data, headers=headers)
    access_token = token_response.json().get("access_token")

    # 2. Initier la transaction
    request_url = f"{base_url}/transactions"
    headers = {
        "Authorization": f"Bearer {access_token}",
        "Content-Type": "application/json"
    }
    body = {
        "amount": str(montant),
        "currency": "XAF",
        "receiver": numero,
        "description": "Retrait via Orange Money"
    }
    response = requests.post(request_url, headers=headers, json=body)

    return response.status_code, response.json()

def depot_mtn(numero, montant):
    # Vérification simple du numéro MTN
    if str(numero).startswith(("67", "68")):
        # Simulation d'appel API MTN
        return 202, "Transaction validée"
    return 400, "Numéro MTN invalide"

def depot_orange(numero, montant):
    # Vérification simple du numéro Orange
    if str(numero).startswith(("69", "65")):
        # Simulation d'appel API Orange
        return 200, "Transaction validée"
    return 400, "Numéro Orange invalide"

from django.http import JsonResponse

def get_compte_info(request):
    numero = request.GET.get("numero")
    try:
        compte = Compte.objects.get(numero_compte=numero)
        data = {
            "nom": compte.proprietaire.get_full_name() or compte.proprietaire.username,
            "type": compte.type,
        }
        return JsonResponse({"status": "ok", "data": data})
    except Compte.DoesNotExist:
        return JsonResponse({"status": "error", "message": "Compte introuvable"})


from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from .models import Compte

# Vérifie que l'utilisateur est admin/staff
def is_admin(user):
    return user.is_staff or user.is_superuser

@login_required
@user_passes_test(is_admin)
def admin_comptes(request):
    comptes = Compte.objects.all().order_by("-id")
    return render(request, "admin/comptes.html", {"comptes": comptes})


from .models import Compte, Message

@user_passes_test(lambda u: u.is_staff)
def admin_modifier_compte(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id)
    client = compte.proprietaire

    if request.method == "POST":
        # Anciennes valeurs
        ancien_nom = client.nom
        ancien_prenom = client.prenom
        ancien_email = client.email
        ancien_tel = client.telephone
        ancienne_adresse = client.adresse
        ancien_pays = client.pays
        ancienne_ville = client.ville

        # Mise à jour compte
        compte.numero_compte = request.POST.get("numero_compte")
        compte.type = request.POST.get("type")
        compte.solde = request.POST.get("solde")
        compte.currency = request.POST.get("currency")
        compte.save()

        # Mise à jour client
        client.nom = request.POST.get("nom")
        client.prenom = request.POST.get("prenom")
        client.email = request.POST.get("email")
        client.telephone = request.POST.get("telephone")
        client.adresse = request.POST.get("adresse")
        client.pays = request.POST.get("pays")
        client.ville = request.POST.get("ville")
        client.save()

        # Construire message automatique
        changements = []
        if client.nom != ancien_nom:
            changements.append(f"Nom: {ancien_nom} → {client.nom}")
        if client.prenom != ancien_prenom:
            changements.append(f"Prénom: {ancien_prenom} → {client.prenom}")
        if client.email != ancien_email:
            changements.append(f"Email: {ancien_email} → {client.email}")
        if client.telephone != ancien_tel:
            changements.append(f"Téléphone: {ancien_tel} → {client.telephone}")
        if client.adresse != ancienne_adresse:
            changements.append(f"Adresse: {ancienne_adresse} → {client.adresse}")
        if client.pays != ancien_pays:
            changements.append(f"Pays: {ancien_pays} → {client.pays}")
        if client.ville != ancienne_ville:
            changements.append(f"Ville: {ancienne_ville} → {client.ville}")

        if changements:
            contenu = "Vos informations ont été modifiées par l’administrateur:\n" + "\n".join(changements)
            Message.objects.create(
                sender=request.user,
                recipient=client,
                content=contenu
            )

        messages.success(request, "Compte et informations du client modifiés avec succès.")
        return redirect("gerer_comptes")

    return render(request, "banka/modifier_compte.html", {"compte": compte, "client": client})



def admin_supprimer_compte(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id)
    compte.delete()
    messages.success(request, "Compte supprimé.")
    return redirect("gerer_comptes")


def admin_suspendre_compte(request, compte_id):
    compte = get_object_or_404(Compte, id=compte_id)

    if compte.status == "actif":
        compte.status = "inactif"
        messages.warning(request, "Compte suspendu.")
    else:
        compte.status = "actif"
        messages.success(request, "Compte réactivé.")

    compte.save()
    return redirect("gerer_comptes")

def gerer_comptes(request):
    comptes = Compte.objects.all()
    return render(request, "banka/gerer_comptes.html", {"comptes": comptes})


from .models import Message
from .tasks import handle_message_created, send_registration_email

@login_required
def send_message(request):
    if request.method == "POST":
        recipient_id = request.POST.get("recipient")
        content = request.POST.get("content")

        if recipient_id == "admin":
            recipient = User.objects.filter(is_staff=True).first()
        else:
            recipient = User.objects.get(id=recipient_id)

        msg = Message.objects.create(
            sender=request.user,
            recipient=recipient,
            content=content
        )

        handle_message_created.delay(msg.id)
        return redirect("send_message")

    users = User.objects.all()
    admin_user = User.objects.filter(is_staff=True).first()
    messages = Message.objects.all().order_by("-created_at")
    return render(request, "banka/message_form.html", {
        "messages": messages,
        "users": users,
        "admin_user": admin_user
    })



@login_required
def transaction_list(request):
    if not request.user.is_staff:
        return render(request, "unauthorized.html")

    transactions = Transaction.objects.all().order_by("-date_transaction")
    return render(request, "banka/transactions.html", {"transactions": transactions})

@login_required
def client_transactions(request):
    transactions = Transaction.objects.filter(compte_source=request.user).order_by("-date_transaction")
    return render(request, "client_transactions.html", {"transactions": transactions})

from django.contrib.auth.decorators import user_passes_test

@user_passes_test(lambda u: u.is_staff)
def fraud_list(request):
    blocked = Transaction.objects.filter(fraud_alerts__isnull=False, statut="blocked")
    return render(request, "banka/fraud_list.html", {"blocked": blocked})

@user_passes_test(lambda u: u.is_staff)
def validate_transaction(request, tx_id):
    tx = Transaction.objects.get(id=tx_id)
    tx.statut = "success"
    tx.fraud_flag = False
    tx.save()
    return redirect("fraud_list")





