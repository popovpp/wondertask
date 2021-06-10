from django.core.mail import send_mail

from django_celery import app


@app.task(name="send_invite_in_group")
def send_invite_in_group(group_name, link, email):
    send_mail(
        subject=f'Your invited in {group_name} group',
        message=f'Click if you want to accept invite: {link}',
        from_email="example@gmail.com",
        recipient_list=[email],
        fail_silently=False,
    )


@app.task(name="send_mail_thread")
def send_mail_thread(url, email):
        send_mail('For recoverinr the passvord go to the link', 
                  f'For recovering the password go to the link: {url}', 
                  'expamole@example.com',  [f'{email}'], fail_silently=False)
