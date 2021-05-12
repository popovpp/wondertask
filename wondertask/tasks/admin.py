from django.contrib import admin

from tasks.models import Task, Comment, Doc, Image, Audio

admin.site.register(Task)
admin.site.register(Comment)
admin.site.register(Doc)
admin.site.register(Image)
admin.site.register(Audio)
