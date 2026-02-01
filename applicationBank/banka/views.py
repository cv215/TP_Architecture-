from django.shortcuts import render,redirect
from django.contrib.auth import authenticate, login, logout
from django.contrib import messages
from .models import User, Role
from .models import Transaction, Event, AuditLog
from django.contrib.auth.decorators import user_passes_test
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, Event, AuditLog

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
                   return redirect("index_admin") 
               else: 
                   return redirect("index") 
           else: 
                messages.error(request, "Le rôle sélectionné est incorrect.")
        else:
            messages.error(request, "Nom d'utilisateur ou mot de passe incorrect")

    return render(request, "banka/login.html")

def register_user(request):
    if request.method == "POST":
        nom = request.POST["nom"]
        prenom = request.POST["prenom"]
        age = request.POST["age"]
        adresse = request.POST["adresse"]
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
    return render(request, "banka/index_admin.html")