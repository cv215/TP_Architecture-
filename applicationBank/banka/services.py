from .models import Transaction
from django.contrib.auth.models import User
from .tasks import handle_fraud_detected

def process_transaction(user, montant, type_transaction, compte_destination=None):
    solde = user.profile.solde  # supposons que tu as un champ solde dans le profil

    if solde < montant:
        # Créer une transaction échouée
        tx = Transaction.objects.create(
            compte_source=user,
            compte_destination=compte_destination,
            type_transaction=type_transaction,
            montant=montant,
            statut="failed"
        )

        # Compter les échecs récents
        failed_count = Transaction.objects.filter(
            compte_source=user,
            statut="failed"
        ).count()

        if failed_count >= 5:
            tx.statut = "blocked"
            tx.fraud_flag = True
            tx.save()
            # Publier un événement de fraude
            handle_fraud_detected.delay(user.id, tx.id)
            # Retour spécial pour signaler au client 
            return {"status": "blocked", "message": "Votre transaction est bloquée pour suspicion de fraude. Contactez l’administrateur."}

        return {"status": "failed", "reason": "Solde insuffisant"}

    else:
        # Transaction réussie
        tx = Transaction.objects.create(
            compte_source=user,
            compte_destination=compte_destination,
            type_transaction=type_transaction,
            montant=montant,
            statut="success"
        )
        # Débiter le solde
        user.profile.solde -= montant
        user.profile.save()
        return {"status": "success", "transaction_id": tx.id}
