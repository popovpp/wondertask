from django.db.models.signals import pre_delete, pre_save
from django.dispatch.dispatcher import receiver
from taggit.models import Tag

from tasks.models import Doc, Image, Audio, TaskSchedule, TaskTag


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


@receiver(pre_delete, sender=TaskSchedule)
def delete_m2m_related_objects(sender, instance, *args, **kwargs):
    instance.repeated_tasks.all().delete()
    instance.periodic_tasks.all().delete()
    instance.task.system_tags.remove("$РЕГУЛЯРНАЯ")


@receiver(pre_save, sender=Tag)
def change_system_tag_name_to_upper(sender, instance, *args, **kwargs):
    instance.name = instance.name.upper()


@receiver(pre_save, sender=TaskTag)
def change_tag_name_to_upper(sender, instance, *args, **kwargs):
    instance.name = instance.name.upper()
