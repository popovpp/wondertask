from django.db import models
from django.utils import timezone
from taggit.managers import TaggableManager

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
    start_date = models.DateTimeField(default='', blank=True, null=True)
    finish_date = models.DateTimeField(default='', blank=True, null=True)
    last_start_time = models.DateTimeField(default='', blank=True, null=True)
    sum_elapsed_time = models.DateTimeField(default='', blank=True, null=True)
    status = models.IntegerField(default=CREATED)
    priority = models.PositiveIntegerField(default=0)
    creator = models.ForeignKey(User, on_delete=models.CASCADE,
                                related_name='task_authors')
    parent_task = models.OneToOneField('Task', related_name='super_task', on_delete=models.CASCADE,
    	                               blank=True, null=True)
    tags = TaggableManager()

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
