from django.db import models
from django.utils import timezone

from accounts.models import User

IMAGES_DIR = 'images/%Y/%m/'
FILES_DIR = 'files/%Y/%m/'


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
    parent_task = models.OneToOneField('Task', related_name='super_task', on_delete=models.CASCADE,
                                       blank=True, null=True)

    class Meta:
        db_table = 'tasks'

    def set_status(self):
        pass

    def set_sum_elapsed_time(self):
        pass


class Executor(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='task_executor')
    executor = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_executor')

    class Meta:
        db_table = 'executors'


class Observer(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='task_observer')
    observer = models.ForeignKey(User, on_delete=models.CASCADE,
                                 related_name='task_observer')

    class Meta:
        db_table = 'observers'


class Comment(models.Model):
    author = models.ForeignKey(User, on_delete=models.CASCADE,
                               related_name='comments')
    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             related_name='comments')
    text = models.TextField(default='', blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.SET_NULL,
                               blank=True, null=True,
                               related_name='super_comment',)

    class Meta:
        db_table = 'comments'


class Doc(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='docs')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='docs')
    doc_file = models.FileField(upload_to=FILES_DIR,
                                blank=True, null=True,)

    class Meta:
        db_table = 'docs'


class Image(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='images')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='images')
    image_file = models.ImageField(upload_to=IMAGES_DIR,
                                   blank=True, null=True,)

    class Meta:
        db_table = 'images'


class Audio(models.Model):

    task = models.ForeignKey(Task, on_delete=models.CASCADE,
                             blank=True, null=True,
                             related_name='audios')
    comment = models.ForeignKey(Comment, on_delete=models.CASCADE,
                                blank=True, null=True,
                                related_name='audios')
    audio_file = models.FileField(upload_to=FILES_DIR,
                                  blank=True, null=True,)

    class Meta:
        db_table = 'audio'
