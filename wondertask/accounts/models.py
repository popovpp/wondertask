import hashlib
import uuid

from django.contrib.auth.models import PermissionsMixin
from django.db import models
from django.contrib.auth.base_user import AbstractBaseUser

from accounts.managers import AccountManager


class User(AbstractBaseUser, PermissionsMixin):

    def image_directory_path(instance, filename):
        filename = str(instance.id) + '_' + uuid.uuid4().hex[:6] + '_' + filename
        return 'avatar_img/{0}'.format(filename)

    email = models.EmailField(unique=True, blank=False)
    full_name = models.CharField(max_length=150, blank=True, null=True, default='')
    avatar_image = models.ImageField(upload_to=image_directory_path,
                                     default='', max_length=255,
                                     blank=True, null=True)

    created = models.DateTimeField(auto_now_add=True)
    is_email_confirmed = models.BooleanField(default=False)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)

    last_login = models.DateTimeField(blank=True, null=True, verbose_name='last login')
    secret = models.CharField(max_length=50, blank=True, null=True,
                              verbose_name='Secret for recover password')

    objects = AccountManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def secret_set(self):
        self.secret = hashlib.md5((str(self.last_login) + self.email).encode()).hexdigest()
        self.save()
        return self.secret

    def secret_check(self, secret):
        return secret == self.secret_set()

    def secret_clear(self):
        self.secret = ''
        self.save()
        return self.secret
