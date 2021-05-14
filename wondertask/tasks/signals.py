from django.db.models.signals import pre_delete
from django.dispatch.dispatcher import receiver

from tasks.models import Doc, Image, Audio


@receiver(pre_delete, sender=Doc)
def doc_file_delete(sender, instance, **kwargs):
    if instance.doc_file:
        instance.doc_file.delete(False)


@receiver(pre_delete, sender=Image)
def image_file_delete(sender, instance, **kwargs):
    if instance.image_file:
        instance.image_file.delete(False)


@receiver(pre_delete, sender=Audio)
def audio_file_delete(sender, instance, **kwargs):
    if instance.audio_file:
        instance.audio_file.delete(False)
