from django.db import models
from django.utils import timezone
from rest_framework.generics import get_object_or_404
from taggit.managers import TaggableManager
import mptt
from mptt.fields import TreeForeignKey
from taggit.models import TagBase, GenericTaggedItemBase

from accounts.models import User


class FileSave(models.Model):
    def file_save(self, model_name, field_name, *args, **kwargs):
        if self.pk is None:
            return super().save(*args, **kwargs)
        old_self = get_object_or_404(model_name, pk=self.pk)
        if (getattr(old_self, field_name) and
                getattr(self, field_name) != getattr(old_self, field_name)):
            getattr(old_self, field_name).delete(False)
        return super().save(*args, **kwargs)


class TaskTag(TagBase):
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        db_table = 'task_tag'


class TaggedTask(GenericTaggedItemBase):
    tag = models.ForeignKey(TaskTag, on_delete=models.CASCADE,
                            related_name="%(app_label)s_%(class)s_items")

    class Meta:
        db_table = 'tagged_task'


class Group(models.Model):
    group_name = models.CharField(max_length=255, default='', blank=True, null=True)
    is_system = models.BooleanField(default=False)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='group_author', blank=True, null=True)
    group_members = models.ManyToManyField(User, blank=True, null=True)

    class Meta:
        db_table = 'groups'

    def __str__(self):
        return repr(self.group_name)


class Task(models.Model):
    CREATED = 0
    IN_PROGRESS = 1
    IN_WAITING = 2
    DONE = 4
    OVERDUE = 8
    IN_PROGRESS_OVERDUE = IN_PROGRESS + OVERDUE
    IN_WAITING_OVERDUE = IN_WAITING + OVERDUE
    STATUS_DICT = {
        CREATED: 'CREATED',
        IN_PROGRESS: 'IN_PROGRESS',
        IN_WAITING: 'IN_WAITING',
        DONE: 'DONE',
        OVERDUE: 'OVERDUE',
        IN_PROGRESS_OVERDUE: 'IN_PROGRESS_OVERDUE',
        IN_WAITING_OVERDUE: 'IN_WAITING_OVERDUE'
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
                                related_name='task_authors',
                                blank=True, null=True)
    user_tags = TaggableManager(through=TaggedTask, blank=True)
    system_tags = TaggableManager(blank=True)

    group = models.ForeignKey(Group, on_delete=models.CASCADE,
                              related_name='group_tasks', blank=True, null=True)

    class Meta:
        db_table = 'tasks'

    def set_status(self, status):
        self.status = status

    def set_sum_elapsed_time(self):
        pass

    def start_task(self):
        current_time = timezone.now
        if self.status == self.CREATED:
            self.start_date = current_time
        else:
            self.last_start_time = current_time
        if self.deadline > current_time:
            self.set_status(self.IN_PROGRESS)
        else:
            self.set_status(self.IN_PROGRESS_OVERDUE)

    def stop_task(self):
        current_time = timezone.now
        if self.deadline > current_time:
            self.set_status(self.IN_WAITING)
        else:
            self.set_status(self.IN_WAITING_OVERDUE)
        self.set_sum_elapsed_time()

    def finish_task(self):
        self.finish_date = timezone.now
        self.set_status(self.DONE)
        self.set_sum_elapsed_time()


TreeForeignKey(Task, on_delete=models.CASCADE,
               related_name="children", blank=True, null=True).contribute_to_class(Task, 'parent')
mptt.register(Task, order_insertion_by=['id'])


class Executor(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='executors')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='executor_tasks')

    class Meta:
        db_table = 'executors'


class Observer(models.Model):
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='observers')
    observer = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='observer_tasks')

    class Meta:
        db_table = 'observers'


# class TaskGroup(models.Model):
#     task = models.ForeignKey(Task, on_delete=models.CASCADE,
#                              related_name='groups')
#     group = models.ForeignKey(Group, on_delete=models.CASCADE,
#                               related_name='tasks')

#    class Meta:
#        db_table = 'taskgroups'
#        unique_together = ('task', 'group')


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='comments')
    text = models.TextField(default='', blank=True, null=True)

    class Meta:
        db_table = 'comments'
        ordering = ['-id']


TreeForeignKey(Comment, on_delete=models.CASCADE, related_name="children",
               blank=True, null=True).contribute_to_class(Comment, 'parent')
mptt.register(Comment, order_insertion_by=['id'])


class Doc(FileSave):
    def files_directory_path(instance, filename):
        return f'files/{instance.task.pk}/{filename}'

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='docs')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='docs')
    doc_file = models.FileField(upload_to=files_directory_path,
                                blank=True, null=True, )

    def save(self, *args, **kwargs):
        return self.file_save(model_name=Doc,
                              field_name='doc_file',
                              *args, **kwargs)

    class Meta:
        db_table = 'docs'


class Image(FileSave):
    def images_directory_path(instance, filename):
        return f'images/{instance.task.pk}/{filename}'

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='images')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='images')
    image_file = models.ImageField(upload_to=images_directory_path,
                                   blank=True, null=True, )

    def save(self, *args, **kwargs):
        return self.file_save(model_name=Image,
                              field_name='image_file',
                              *args, **kwargs)

    class Meta:
        db_table = 'images'


class Audio(FileSave):
    def audio_directory_path(instance, filename):
        return f'audio/{instance.task.pk}/{filename}'

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='audios')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='audios')
    audio_file = models.FileField(upload_to=audio_directory_path,
                                  blank=True, null=True, )

    def save(self, *args, **kwargs):
        return self.file_save(model_name=Audio,
                              field_name='audio_file',
                              *args, **kwargs)

    class Meta:
        db_table = 'audio'
