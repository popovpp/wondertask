from django.contrib import admin

from journals.models import NotificationToUser, Notification

admin.site.register(NotificationToUser)
admin.site.register(Notification)