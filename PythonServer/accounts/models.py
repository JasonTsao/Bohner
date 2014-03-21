from django.db import models
from django.contrib.auth.models import User

# Create your models here.
class MeepUser(models.Model):
    user = models.ForeignKey(User)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    facebook = models.CharField(max_length=255, null=True, blank=True)
    uber = models.CharField(max_length=255, null=True, blank=True)