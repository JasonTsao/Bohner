from django.db import models
from events.models import *
from accounts.models import *

# Create your models here.
class Notification(models.Model):
    event = models.ForeignKey(Event, null=True, blank=True)
    recipient = models.ForeignKey(Account)
    message = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateField(auto_now_add=True)
    facebook = models.NullBooleanField(null=True, blank=True, default=False)
    def __unicode__(self):
        return self.message