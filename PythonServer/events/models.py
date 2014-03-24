from django.db import models
from accounts.models import Account


class Event(models.Model):
    creator = models.ForeignKey(Account)
    name = models.CharField(max_length=255, default='New Event')
    start_time = models.DateTimeField(db_index=True, null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True) 
    location_name = models.CharField(max_length=255, null=True, blank=True)
    location_address = models.CharField(max_length=255, null=True, blank=True)
    location_coordinates = models.CharField(max_length=255, null=True, blank=True)
    event_over = models.NullBooleanField(default=False)
    cancelled = models.NullBooleanField(default=False)
    private = models.NullBooleanField(default=False)
    friends_can_invite = models.NullBooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    def __unicode__(self):
        return str('{0} : {1}'.format(self.pk,self.name))


class EventComment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(Account)
    description = models.TextField() 
    created = models.DateTimeField(auto_now_add=True)
    private =  models.NullBooleanField(default=False)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)


class InvitedFriend(models.Model):
    user = models.ForeignKey(Account)
    event = models.ForeignKey(Event)
    can_invite_friends = models.NullBooleanField(default=True)
    attenting = models.NullBooleanField(null=True, blank=True, default=False)

    class Meta:
        unique_together = (('user', 'event',),)