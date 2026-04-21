from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Tecnico
from .mongo_sync import delete_tecnico_from_mongo, sync_tecnico_to_mongo


@receiver(post_save, sender=Tecnico)
def tecnico_post_save_sync(sender, instance: Tecnico, **kwargs):
    sync_tecnico_to_mongo(instance)


@receiver(post_delete, sender=Tecnico)
def tecnico_post_delete_sync(sender, instance: Tecnico, **kwargs):
    delete_tecnico_from_mongo(instance.id)
