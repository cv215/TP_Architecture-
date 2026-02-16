from .models import Transaction
from django.contrib.auth.models import User
from .tasks import handle_fraud_detected

def process_transaction(user, montant, type_transaction, compte_destination=None):
    solde = user.profile.solde 

    if solde < montant:
        tx = Transaction.objects.create(
            compte_source=user,
            compte_destination=compte_destination,
            type_transaction=type_transaction,
            montant=montant,
            statut="failed"
        )

        failed_count = Transaction.objects.filter(
            compte_source=user,
            statut="failed"
        ).count()

        if failed_count >= 5:
            tx.statut = "blocked"
            tx.fraud_flag = True
            tx.save()
            handle_fraud_detected.delay(user.id, tx.id)
            return {"status": "blocked", "message": "Votre transaction est bloquée pour suspicion de fraude. Contactez l’administrateur."}

        return {"status": "failed", "reason": "Solde insuffisant"}

    else:
        tx = Transaction.objects.create(
            compte_source=user,
            compte_destination=compte_destination,
            type_transaction=type_transaction,
            montant=montant,
            statut="success"
        )
        user.profile.solde -= montant
        user.profile.save()
        return {"status": "success", "transaction_id": tx.id}
