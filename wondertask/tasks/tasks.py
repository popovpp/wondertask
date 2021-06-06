from django.utils import timezone

from django.core.mail import send_mail
from taggit.models import Tag

from django_celery import app
from tasks.models import Task, TaskSchedule


@app.task(name="send_invite_in_group")
def send_invite_in_group(group_name, url, email):
    send_mail(
        subject=f'Your invited in {group_name} group',
        message=f'Click if you want to accept invite: {url}',
        from_email="example@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )


@app.task(name="send_mail_thread")
def send_mail_thread(url, email):
    send_mail('For recoverinr the passvord go to the link',
              f'For recovering the password go to the link: {url}',
              'expamole@example.com', [f'{email}'], fail_silently=False)


@app.task(name="create_repeats_tasks")
def create_repeats_tasks(task_id: int):
    task = Task.objects.get(pk=task_id)
    system_tag, _ = Tag.objects.get_or_create(name="РЕГУЛЯРНАЯ")
    task.system_tags.add(system_tag)
    task_schedule = TaskSchedule.objects.get(task_id=task_id)
    deadline = task.deadline - task.creation_date

    remaining_estimate = task_schedule.crontab.schedule.remaining_estimate(timezone.now())
    creation_date = timezone.now() + remaining_estimate

    repeat_task_list = []
    counter = 0
    while True:
        repeat_task = Task.objects.create(title=task.title, creator=task.creator)
        repeat_task.creation_date = creation_date
        repeat_task.start_date = task.start_date
        repeat_task.finish_date = task.finish_date
        repeat_task.sum_elapsed_time = task.sum_elapsed_time
        repeat_task.priority = task.priority
        repeat_task.user_tags = task.user_tags
        repeat_task.system_tags = task.system_tags
        repeat_task.group = task.group
        repeat_task.deadline = creation_date + deadline

        repeat_task.save()
        repeat_task_list.append(repeat_task)

        remaining_estimate = task_schedule.crontab.schedule.remaining_estimate(creation_date)
        creation_date = timezone.now() + remaining_estimate

        counter += 1
        if task_schedule.number_of_times and counter >= task_schedule.number_of_times:
            break
        if task_schedule.end_date and creation_date >= task_schedule.end_date:
            break
        if creation_date >= timezone.now() + timezone.timedelta(days=365) or counter >= 365:
            break

    task_schedule.repeated_tasks.add(*repeat_task_list)

