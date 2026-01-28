from django.db import models

# Create your models here.
class User(models.Model):
    nom = models.CharField(max_length=100)
    prenom = models.CharField(max_length=100)
    age = models.IntegerField()
    email = models.EmailField(unique=True)
    telephone = models.CharField(max_length=15, unique=True)
    adresse = models.CharField(max_length=255)
    pays = models.CharField(max_length=100)
    ville = models.CharField(max_length=100)
    password = models.CharField(max_length=128)
    role = models.ForeignKey('Role', on_delete=models.CASCADE)
    permission = models.ManyToManyField('Permission', through='RolePermission')
    agence = models.ForeignKey('Agence', on_delete=models.CASCADE, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    date_creation = models.DateTimeField(auto_now_add=True)
    date_modification = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['date_creation']
    
    def __str__(self):
        return f"{self.prenom} {self.nom} - {self.email}"
    
class Compte(models.Model):
    numero_compte = models.CharField(max_length=20, unique=True)
    solde = models.DecimalField(max_digits=15, decimal_places=2)
    proprietaire = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comptes')
    status = models.CharField(max_length=50)
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