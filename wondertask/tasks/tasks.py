from django.core.mail import send_mail

from settings import EMAIL_HOST_USER
from django_celery import app


@app.task(name="send_invite_in_group")
def send_invite_in_group(group_name, url, email):
    print(url, email)
    send_mail(
        subject=f'Your invited in {group_name} group',
        message=f'Click if you want to accept invite: {url}',
        from_email=EMAIL_HOST_USER,
        recipient_list=[email],
        fail_silently=False,
    )
