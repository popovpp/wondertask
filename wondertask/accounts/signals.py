from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from accounts.models import User


@receiver(pre_delete, sender=User)
def avatar_delete(sender, instance, **kwargs):
    if instance.avatar_image:
        instance.avatar_image.delete(False)

#@receiver(models.signals.post_delete, sender=User)
#def auto_delete_file_on_delete(sender, instance, **kwargs):
#    if instance.avatar:
#        if os.path.isfile(instance.avatar.path):
#            os.remove(instance.avatar.path)