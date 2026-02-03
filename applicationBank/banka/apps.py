from django.apps import AppConfig


class BankaConfig(AppConfig):
    name = 'banka'

def ready(self):
    import banka.signals