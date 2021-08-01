from django.db.models.signals import pre_delete, pre_save, post_save
from django.dispatch.dispatcher import receiver
from taggit.models import Tag

from journals.services import notify_service
from tasks.models import Doc, Image, Audio, Task, Comment
from tasks.models import TaskSchedule, TaskTag, Group


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


@receiver(pre_save, sender=Doc)
def doc_file_add_send_notification(sender, instance, **kwargs):
    notify_service.send_add_object_notifications(task=instance.task, object_name="файл")


@receiver(pre_save, sender=Image)
def image_file_add_send_notification(sender, instance, **kwargs):
    notify_service.send_add_object_notifications(task=instance.task, object_name="изображение")


@receiver(pre_save, sender=Audio)
def audio_file_add_send_notification(sender, instance, **kwargs):
    notify_service.send_add_object_notifications(task=instance.task, object_name="аудио")


@receiver(pre_save, sender=Comment)
def comment_add_send_notification(sender, instance, **kwargs):
    notify_service.send_add_object_notifications(task=instance.task, object_name="комментарий")


@receiver(pre_delete, sender=Task)
def delete_m2m_related_objects(sender, instance, *args, **kwargs):
    instance.periodic_tasks.all().delete()
    instance.clocked_shedule.all().delete()


@receiver(post_save, sender=Group)
def group_add_send_notification(sender, instance, **kwargs):
    if instance.creator not in instance.group_members.all():
        return None
    notify_service.send_add_group_notifications(group=instance)


@receiver(pre_delete, sender=Group)
def group_del_send_notification(sender, instance, **kwargs):
    if instance.creator not in instance.group_members.all():
        return None
    notify_service.send_del_group_notifications(group=instance)
