from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Cuenta
from .mongo_sync import delete_cuenta_from_mongo, sync_cuenta_to_mongo


@receiver(post_save, sender=Cuenta)
def cuenta_post_save_sync(sender, instance: Cuenta, **kwargs):
    sync_cuenta_to_mongo(instance)


@receiver(post_delete, sender=Cuenta)
def cuenta_post_delete_sync(sender, instance: Cuenta, **kwargs):
    delete_cuenta_from_mongo(instance.id)
