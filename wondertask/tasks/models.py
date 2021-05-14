import uuid

from django.db import models
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from taggit.managers import TaggableManager
import mptt
from mptt.fields import TreeForeignKey

from accounts.models import User


class Task(models.Model):

    CREATED = 0
    IN_PROGRESS = 1
    IN_WAITING = 2
    DONE = 4
    OVERDUE = 8
    IN_PROGRESS_OVERDUE = IN_PROGRESS + OVERDUE
    IN_WAITING_OVERDUE = IN_WAITING + OVERDUE
    STATUS_DICT = {
                   CREATED : 'CREATED',
               IN_PROGRESS : 'IN_PROGRESS',
                IN_WAITING : 'IN_WAITING',
                      DONE : 'DONE',
                   OVERDUE : 'OVERDUE',
       IN_PROGRESS_OVERDUE : 'IN_PROGRESS_OVERDUE',
        IN_WAITING_OVERDUE : 'IN_WAITING_OVERDUE'
    }

    title = models.CharField(max_length=255, default='', blank=True, null=True)
    creation_date = models.DateTimeField(auto_now_add=True)
    deadline = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(blank=True, null=True)
    finish_date = models.DateTimeField(blank=True, null=True)
    last_start_time = models.DateTimeField(blank=True, null=True)
    sum_elapsed_time = models.DateTimeField(blank=True, null=True)
    status = models.IntegerField(default=CREATED)
    priority = models.PositiveIntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='task_authors')

    # user_tags = TaggableManager()

    class Meta:
        db_table = 'tasks'

    def set_status(self):
        pass

    def set_sum_elapsed_time(self):
        pass


TreeForeignKey(Task, on_delete=models.CASCADE, blank=True, null=True).contribute_to_class(Task, 'parent')
mptt.register(Task, order_insertion_by=['id'])


class TaskSystemTags(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='task_field')
    system_tags = TaggableManager()

    class Meta:
        db_table = 'task_system_tags'


class Executor(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='executors')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_executor')

    class Meta:
        db_table = 'executors'


class Observer(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                                related_name='observers')
    observer = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_observer')

    class Meta:
        db_table = 'observers'


class Group(models.Model):

    group_name = models.CharField(max_length=255, default='', blank=True, null=True)
    is_system = models.BooleanField(default=False)

    class Meta:
        db_table = 'groups'

    def __str__(self):
        return repr(self.group_name)


class TaskGroup(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='groups')
    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='task_group_group_field')

    class Meta:
        db_table = 'taskgroups'
        unique_together = ('task', 'group')


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='comments')
    text = models.TextField(default='', blank=True, null=True)

    class Meta:
        db_table = 'comments'


class Doc(models.Model):
    def files_directory_path(instance, filename):
        return f'files/{instance.task.pk}/{filename}'
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='docs')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='docs')
    doc_file = models.FileField(upload_to=files_directory_path,
                                blank=True, null=True,)

    def save(self, *args, **kwargs):
        if self.pk is None:
            return super(Doc, self).save(*args, **kwargs)
        old_self = get_object_or_404(Doc, pk=self.pk)
        if old_self.doc_file and self.doc_file != old_self.doc_file:
            old_self.doc_file.delete(False)
        return super(Doc, self).save(*args, **kwargs)

    class Meta:
        db_table = 'docs'


class Image(models.Model):
    def images_directory_path(instance, filename):
        return f'images/{instance.task.pk}/{filename}'
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='images')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='images')
    image_file = models.ImageField(upload_to=images_directory_path,
                                   blank=True, null=True,)

    def save(self, *args, **kwargs):
        if self.pk is None:
            return super(Image, self).save(*args, **kwargs)
        old_self = get_object_or_404(Image, pk=self.pk)
        if old_self.image_file and self.image_file != old_self.image_file:
            old_self.image_file.delete(False)
        return super(Image, self).save(*args, **kwargs)

    class Meta:
        db_table = 'images'


class Audio(models.Model):
    def audio_directory_path(instance, filename):
        return f'audio/{instance.task.pk}/{filename}'
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='audios')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='audios')
    audio_file = models.FileField(upload_to=audio_directory_path,
                                  blank=True, null=True,)

    def save(self, *args, **kwargs):
        if self.pk is None:
            return super(Audio, self).save(*args, **kwargs)
        old_self = get_object_or_404(Audio, pk=self.pk)
        if old_self.audio_file and self.audio_file != old_self.audio_file:
            old_self.audio_file.delete(False)
        return super(Audio, self).save(*args, **kwargs)

    class Meta:
        db_table = 'audio'
