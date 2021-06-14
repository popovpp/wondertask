from django.contrib import admin

from journals.models import NotificationToUser, Notification

admin.site.register(NotificationToUser)


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'message', 'type', 'created']
