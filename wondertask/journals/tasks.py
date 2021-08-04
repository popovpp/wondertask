from push_notifications.models import GCMDevice

from django_celery import app


@app.task(name="fcm_send_message", serializer='json')
def fcm_send_message(user_ids, message, notification_id):
    fcm_devices = GCMDevice.objects.filter(user_id__in=user_ids)
    res = fcm_devices.send_message(None, extra={
        "priority": "high",
        "body": message,
        "notification_id": notification_id,
    })
    return res
