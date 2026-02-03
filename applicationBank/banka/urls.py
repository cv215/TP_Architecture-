from django.urls import path
from .views import ( index, index_admin, login_user, register_user, comptes, transactions, messageries, transaction_retrait, transaction_depot, transaction_virement, creer_compte )
from django.contrib.auth.views import LogoutView

from banka import views
# Register your models here.

urlpatterns = [
    path("acceuilClient/", index, name='acceuilClient'),
    path("acceuilAdmin/", index_admin, name="acceuilAdmin"),
    path("login/", login_user, name="login"),
    path("", register_user, name="register"),
    path("mes_comptes/", comptes, name="mes_comptes"),
    path("mes_transactions/", transactions, name="mes_transactions"),
    path("mes_messages/", messageries, name="mes_messages"),
    path("logout/", LogoutView.as_view(next_page="login"), name="logout"),
    path("transactions/retrait/", transaction_retrait, name="transaction_retrait"),
    path("transactions/depot/", transaction_depot, name="transaction_depot"),
    path("transactions/virement/", transaction_virement, name="transaction_virement"),
    path("creer_compte/", creer_compte, name="creer_compte"),
    path("get-compte-info/", views.get_compte_info, name="get_compte_info"),

     
]