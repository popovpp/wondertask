from django.contrib import admin
from push_notifications.models import APNSDevice, WNSDevice, WebPushDevice

from journals.models import NotificationToUser, Notification

admin.site.register(NotificationToUser)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'type', 'created', 'task_id_del', 'group_name_del']


admin.site.unregister(APNSDevice)
admin.site.unregister(WNSDevice)
admin.site.unregister(WebPushDevice)
