from django.db import models
from accounts.models import MeepUser


class Event(models.Model):
    creator = models.ForeignKey(MeepUser)
    name = models.CharField(max_length=255, null=True, blank=True)
    time = models.DateTimeField(db_index=True, null=True, blank=True)
    description = models.TextField(null=True, blank=True) 
    location_name = models.CharField(max_length=255, null=True, blank=True)
    location_address = models.CharField(max_length=255, null=True, blank=True)
    location_coordinates = models.CharField(max_length=255, null=True, blank=True)
    event_over = models.NullBooleanField(null=True, blank=True, default=False)
    cancelled = models.NullBooleanField(null=True, blank=True, default=False)


class InvitedFriend(models.Model):
    user = models.ForeignKey(MeepUser)
    event = models.ForeignKey(Event)
    attenting = models.NullBooleanField(null=True, blank=True, default=False)