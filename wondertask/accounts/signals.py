from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from accounts.models import User


@receiver(pre_delete, sender=User)
def avatar_delete(sender, instance, **kwargs):
    if instance.avatar_image:
        instance.avatar_image.delete(True)
