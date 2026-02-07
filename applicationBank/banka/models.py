from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager

# Create your models here.

class ClientsManager(BaseUserManager):
    def create_user(self, nom, email, password=None, **extra_fields):
        if not nom:
            raise ValueError('The Username must be set')
        email = self.normalize_email(email)
        user = self.model(nom=nom, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, nom, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')
        
        from .models import Role
        role_admin, _ = Role.objects.get_or_create(nom="Administrateur", description="Superutilisateur")

        extra_fields['role'] = role_admin

        return self.create_user(nom, email, password, **extra_fields)
class User(AbstractBaseUser, PermissionsMixin):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100, null=True, blank=True)
    age = age = models.IntegerField(null=True, blank=True)
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=15, unique=True, null=True, blank=True)
    adresse = models.CharField(max_length=255, null=True, blank=True)
    pays = models.CharField(max_length=100, null=True, blank=True)
    ville = models.CharField(max_length=100, null=True, blank=True)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    permission = models.ManyToManyField('Permission', through='RolePermission')
    agence = models.ForeignKey('Agence', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False) 
    is_superuser = models.BooleanField(default=False)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    objects = ClientsManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nom']
    
    class Meta:
        ordering = ['date_creation']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.email}"
    
class Compte(models.Model):
    TYPE_CHOICES = [ ("courant", "Courant"), ("epargne", "Épargne"), ] 
    STATUS_CHOICES = [ ("actif", "Actif"), ("inactif", "Inactif"), ]
    numero_compte = models.CharField(max_length=20, unique=True)
    solde = models.DecimalField(max_digits=15, decimal_places=2)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comptes')
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="actif")
    type = models.CharField(max_length=50, choices=TYPE_CHOICES)
    currency = models.CharField(max_length=10)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date_creation']
    
    def __str__(self):
        return f"Compte {self.numero_compte} - Solde: {self.solde}"
    
class Transaction(models.Model):
    compte_source = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='transactions_source')
    compte_destination = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='transactions_destination')
    montant = models.DecimalField(max_digits=15, decimal_places=2)
    type_transaction = models.CharField(max_length=50)
    date_transaction = models.DateTimeField(auto_now_add=True)
    statut = models.CharField(max_length=50)
    
    class Meta:
        ordering = ['-date_transaction']
    
    def __str__(self):
        return f"Transaction {self.id} - Montant: {self.montant} from {self.compte_source.numero_compte} to {self.compte_destination.numero_compte}"
    
class Agence(models.Model):
    nom = models.CharField(max_length=100)
    adresse = models.CharField(max_length=255)
    ville = models.CharField(max_length=100)
    pays = models.CharField(max_length=100)
    telephone = models.CharField(max_length=15)
    email = models.EmailField()
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date_creation']
    
    def __str__(self):
        return f"Agence {self.nom} - {self.ville}"
    
class Role(models.Model):
    nom = models.CharField(max_length=50, unique=True)
    description = models.TextField()
    
    def __str__(self):
        return self.nom
    
class Permission(models.Model):
    nom = models.CharField(max_length=100)
    description = models.TextField()
    
    def __str__(self):
        return self.nom
    
class RolePermission(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='role_permissions')
    role = models.ForeignKey(Role, on_delete=models.CASCADE, related_name='permissions')
    permission = models.ForeignKey(Permission, on_delete=models.CASCADE, related_name='roles')
    
    class Meta:
        unique_together = ('role', 'permission')
    
    def __str__(self):
        return f"{self.role} - {self.permission.nom}"
    
class AuditLog(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    event = models.ForeignKey('Event', on_delete=models.CASCADE)
    agence = models.ForeignKey(Agence, on_delete=models.CASCADE, null=True, blank=True)
    action = models.CharField(max_length=255)
    date_action = models.DateTimeField(auto_now_add=True)
    details = models.TextField()
    
    class Meta:
        ordering = ['-date_action']
    
    def __str__(self):
        return f"AuditLog {self.id} - User: {self.utilisateur.email} - Action: {self.action}"
    
class Event(models.Model):
    nom = models.CharField(max_length=100)
    source_service = models.CharField(max_length=100)
    processed = models.BooleanField(default=False)
    description = models.TextField()
    date_debut = models.DateTimeField()
    date_fin = models.DateTimeField()
    
    class Meta:
        ordering = ['date_debut']
    
    def __str__(self):
        return self.nom
    
class Notification(models.Model):
    utilisateur = models.ForeignKey(User, on_delete=models.CASCADE)
    message = models.TextField()
    lu = models.BooleanField(default=False)
    status = models.CharField(max_length=50)
    channel = models.CharField(max_length=50)
    date_notification = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-date_notification']
    
    def __str__(self):
        return f"Notification {self.id} - User: {self.utilisateur.email}"
    
class FraudAlert(models.Model):
    compte = models.ForeignKey(Compte, on_delete=models.CASCADE, related_name='fraud_alerts')
    transaction = models.ForeignKey(Transaction, on_delete=models.CASCADE, related_name='fraud_alerts')
    description = models.TextField()
    status = models.CharField(max_length=50)
    risk_level = models.CharField(max_length=50)
    date_alert = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)
    
    class Meta:
        ordering = ['-date_alert']
    
    def __str__(self):
        return f"FraudAlert {self.id} - Compte: {self.compte.numero_compte}"
    

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)
    solde = models.FloatField(default=0)
    currency = models.CharField(max_length=3, default="XAF")

    def __str__(self):
        return f"Profil de {self.user.username}"

class Message(models.Model):
    sender = models.ForeignKey(User, related_name="sent_messages", on_delete=models.CASCADE)
    recipient = models.ForeignKey(User, related_name="received_messages", on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
