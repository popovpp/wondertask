from django.contrib import admin

from accounts.models import User

class UserModelAdmin(admin.ModelAdmin):
    list_display = ['id', 'email', 'last_login', 'secret', 'password']
    list_display_links = ['email']
    search_fields = ['email']

    class Meta:
        model = User


admin.site.register(User, UserModelAdmin)
