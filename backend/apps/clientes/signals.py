from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Cliente
from .mongo_sync import delete_cliente_from_mongo, sync_cliente_to_mongo


@receiver(post_save, sender=Cliente)
def cliente_post_save_sync(sender, instance: Cliente, **kwargs):
    sync_cliente_to_mongo(instance)


@receiver(post_delete, sender=Cliente)
def cliente_post_delete_sync(sender, instance: Cliente, **kwargs):
    delete_cliente_from_mongo(instance.id)
