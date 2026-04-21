from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import ItemInventario
from .mongo_sync import delete_item_inventario_from_mongo, sync_item_inventario_to_mongo


@receiver(post_save, sender=ItemInventario)
def item_inventario_post_save_sync(sender, instance: ItemInventario, **kwargs):
    sync_item_inventario_to_mongo(instance)


@receiver(post_delete, sender=ItemInventario)
def item_inventario_post_delete_sync(sender, instance: ItemInventario, **kwargs):
    delete_item_inventario_from_mongo(instance.id)
