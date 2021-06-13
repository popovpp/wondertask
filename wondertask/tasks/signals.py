from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch.dispatcher import receiver
from taggit.models import Tag

from journals.services import notify_service
from tasks.models import Doc, Image, Audio, Task
from tasks.models import TaskSchedule, TaskTag


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


@receiver(pre_save, sender=Task)
def pre_save_task(sender, instance, **kwargs):
    if not instance.creator:
        return None
    if not instance.id:
        return None
    previous_instance = Task.objects.get(id=instance.id)
    if previous_instance.group != instance.group:
        notify_service.send_changed_group_notification(task=instance,
                                                       previous_task=previous_instance)
    else:
        notify_service.send_notification(task=instance)


@receiver(pre_delete, sender=Task)
def create_notification_task_delete_action(sender, instance, **kwargs):
    if not instance.creator:
        return None
    notify_service.send_notification(task=instance)
