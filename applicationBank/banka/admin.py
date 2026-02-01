from django.contrib import admin
<<<<<<< HEAD
from .models import User, Compte, Transaction, Agence, Role, AuditLog, Notification, FraudAlert, Event, Permission

# Register your models here.

class AdminUser(admin.ModelAdmin):
    list_display = ('prenom', 'nom', 'email', 'telephone', 'role', 'is_active', 'date_creation')
    search_fields = ('prenom', 'nom', 'email', 'telephone')
    list_filter = ('role', 'is_active', 'date_creation')
    ordering = ('-date_creation',)
    
class AdminCompte(admin.ModelAdmin):
    list_display = ('numero_compte', 'proprietaire', 'solde', 'status', 'currency', 'date_creation')
    search_fields = ('numero_compte', 'proprietaire__prenom', 'proprietaire__nom')
    list_filter = ('status', 'currency', 'date_creation')
    
class AdminTransaction(admin.ModelAdmin):
    list_display = ('id', 'compte_source', 'compte_destination', 'montant', 'type_transaction', 'statut', 'date_transaction')
    search_fields = ('compte_source__numero_compte', 'compte_destination__numero_compte')
    list_filter = ('type_transaction', 'statut', 'date_transaction')
    ordering = ('-date_transaction',)
    
class AdminAgence(admin.ModelAdmin):
    list_display = ('nom', 'adresse', 'ville', 'pays')
    search_fields = ('nom', 'ville', 'pays')
    ordering = ('nom',)
    
class AdminRole(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom',)
    ordering = ('nom',)
    
class AdminNotification(admin.ModelAdmin):
    list_display = ('status', 'utilisateur', 'lu', 'date_notification')
    search_fields = ('status', 'utilisateur__prenom', 'utilisateur__nom')
    list_filter = ('lu', 'date_notification')
    ordering = ('-date_notification',)
    
class AdminFraudAlert(admin.ModelAdmin):
    list_display = ('compte', 'status', 'resolved', 'date_alert')
    search_fields = ('compte__numero_compte', 'status')
    list_filter = ('resolved', 'date_alert')
    ordering = ('-date_alert',)

class AdminEvent(admin.ModelAdmin):
    list_display = ('nom', 'description', 'date_debut', 'date_fin')
    search_fields = ('nom',)
    list_filter = ('date_debut', 'date_fin')
    ordering = ('-date_debut',)

class AdminPermission(admin.ModelAdmin):
    list_display = ('nom', 'description')
    search_fields = ('nom', 'description')
    ordering = ('nom',)
    
class AdminAuditLog(admin.ModelAdmin):
    list_display = ('action', 'utilisateur', 'date_action')
    search_fields = ('action', 'utilisateur__prenom', 'utilisateur__nom')
    list_filter = ('action',)
    ordering = ('-date_action',)
    
class AdminRolePermission(admin.ModelAdmin):
    list_display = ('role', 'permission')
    search_fields = ('role__nom', 'permission__nom')
    ordering = ('role__nom', 'permission__nom')
    
admin.site.register(User, AdminUser)
admin.site.register(Compte, AdminCompte)
admin.site.register(Transaction, AdminTransaction)
admin.site.register(Agence, AdminAgence)
admin.site.register(Role, AdminRole)
admin.site.register(AuditLog, AdminAuditLog)
admin.site.register(Notification, AdminNotification)
admin.site.register(FraudAlert, AdminFraudAlert)
admin.site.register(Event, AdminEvent)
admin.site.register(Permission, AdminPermission)  
=======

# Register your models here.
>>>>>>> 1d57ea70ddecb7bf7ea5f0ae9c7cb23bdc51d621
