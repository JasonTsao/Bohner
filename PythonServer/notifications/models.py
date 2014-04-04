from django.db import models
from events.models import Event
from accounts.models import Account


# Create your models here.
class Notification(models.Model):
    event = models.ForeignKey(Event, null=True, blank=True)
    notification_creator = models.ForeignKey(Account, related_name='notification_creator')
    notification_recipient = models.ForeignKey(Account, related_name='notification_recipient')
    message = models.CharField(max_length=255, blank=True, null=True)
    notification_type = models.CharField(max_length=255, blank=True, null=True)
    recipients = models.ManyToManyField(Account)
    created = models.DateField(auto_now_add=True)
    facebook = models.NullBooleanField(null=True, blank=True, default=False)
    def __unicode__(self):
        return self.message