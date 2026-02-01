from django.urls import path
from banka.views import index,login_user,register_user,index_admin
# Register your models here.

urlpatterns = [
    path('home_client', index, name='home_client'),
    path("home_admin", index_admin, name="home_admin"),
    path("login/", login_user, name="login"),
     path("", register_user, name="register"),
]