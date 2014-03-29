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


class EventCreatorLocation(models.Model):
    event = models.ForeignKey(Event)
    coordinates = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)


class EventNotification(models.Model):
    event = models.ForeignKey(Event)
    recipient = models.ForeignKey(Account)
    message = models.CharField(max_length=255, blank=True, null=True)
    created = models.DateField(auto_now_add=True)
    facebook = models.NullBooleanField(null=True, blank=True, default=False)
    def __unicode__(self):
        return self.message


class InvitedFriend(models.Model):
    user = models.ForeignKey(Account)
    event = models.ForeignKey(Event)
    can_invite_friends = models.NullBooleanField(default=True)
    attenting = models.NullBooleanField(null=True, blank=True, default=False) # need to be changed to attending!!
    class Meta:
        unique_together = (('user', 'event',),)

    def save(self, user=None, *args, **kwargs):
        if not self.pk:
            event_notification = EventNotification(recipient=self.user, event=self.event)
            event_notification.message = '{0} has invited you to {1}'.format(self.event.creator.user_name, self.event.name)
            event_notification.save()
        super(InvitedFriend, self).save()


class EventComment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(Account)
    description = models.TextField() 
    created = models.DateTimeField(auto_now_add=True)
    private =  models.NullBooleanField(default=False)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    def save(self, user=None, *args, **kwargs):
        if not self.pk:
            if self.user != self.event.creator:
                event_notification = EventNotification(recipient=self.event.creator, event=self.event)
                event_notification.message = '{0} said on event {1} : {2}'.format(self.user.user_name, self.event.name, self.description)
                event_notification.save()

            invited_friends = InvitedFriend.objects.filter(event=self.event)
            for invited_friend in invited_friends:
                if invited_friend != self.user:
                    event_notification = EventNotification(recipient=invited_friend.user, event=self.event)
                    event_notification.message = '{0} said on event {1} : {2}'.format(self.user.user_name, self.event.name, self.description)
                    event_notification.save()
        super(EventComment, self).save()



