import json
from django.db import models
from accounts.models import Account
from ios_notifications.models import APNService, Notification, Device
from notifications.api import createNotification, sendNotification


class Event(models.Model):
    creator = models.ForeignKey(Account)
    name = models.CharField(max_length=255, default='New Event')
    start_time = models.DateTimeField(db_index=True, null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    meetup_spot = models.CharField(max_length=255, null=True, blank=True, default="In front")
    location_name = models.CharField(max_length=255, null=True, blank=True)
    location_address = models.CharField(max_length=255, null=True, blank=True)
    location_coordinates = models.CharField(max_length=255, null=True, blank=True)
    event_type = models.CharField(max_length=255, null=True, blank=True)
    event_over = models.NullBooleanField(default=False)
    cancelled = models.NullBooleanField(default=False)
    private = models.NullBooleanField(default=False)
    friends_can_invite = models.NullBooleanField(default=False)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)

    def save(self, invited_friends=None,*args, **kwargs):
        if self.pk and invited_friends:
            try:
                message = "{0} updated {1}".format(self.creator.user_name, self.name)
                custom_payload = {
                                "creator_name": self.creator.user_name,
                                "creator_id": self.creator.id,
                                "event_name": self.name,
                                "event_id": self.id}

                custom_payload = json.dumps(custom_payload)
                notification = createNotification(message, custom_payload)
                tokens = []
                devices = []
                for invited_friend in invited_friends:
                    device = Device.objects.get(users__pk=invited_friend.user.user.id)
                    tokens.append(device.token)
                    notification.recipients.add(invited_friend.user.user)
                sendNotification(notification, tokens)
            except Exception as e:
                print 'Unable to send push notification when updateing event {0}: {1}'.format(self.id, e)
        super(Event, self).save()

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
    coordinates = models.CharField(max_length=255, null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    attending = models.NullBooleanField(null=True, blank=True, default=False) # need to be changed to attending!!
    class Meta:
        unique_together = (('user', 'event',),)

    def save(self, create_notification=None, *args, **kwargs):
        try:
            if not self.pk and create_notification:
                message = "You have been invited by {0} to go to {1}".format(self.event.creator.user_name, self.event.name)
                custom_payload = {
                                "invited_by_name": self.event.creator.user_name,
                                "invited_by_id": self.event.creator.id,
                                "event_name": self.event.name,
                                "event_id": self.event.id}
                custom_payload = json.dumps(custom_payload)
                notification = createNotification(message, custom_payload)
                notification.recipients.add(self.user.user)
                tokens = []
                user = self.user.user
                device = Device.objects.get(users__pk=user.id)
                tokens.append(device.token)
                sendNotification(notification, tokens)
        except Exception as e:
                print 'Unable to send push notification to {0} abouve updating event {1}'.format(self.user.id, self.event.id)
        super(InvitedFriend, self).save()


class EventComment(models.Model):
    event = models.ForeignKey(Event)
    user = models.ForeignKey(Account)
    description = models.TextField() 
    created = models.DateTimeField(auto_now_add=True)
    private =  models.NullBooleanField(default=False)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    def save(self, invited_friends=None, *args, **kwargs):
        if not self.pk:
            try:
                message = "{0} added comment to event {1}".format(self.user.user_name, self.event.name)
                custom_payload = {
                                "creator_name": self.user.user_name,
                                "creator_id": self.user.id,
                                "event_name": self.event.name,
                                "event_id": self.event.id}
                custom_payload = json.dumps(custom_payload)
                notification = createNotification(message, custom_payload)
                tokens = []
                devices = []
                if self.user != self.event.creator:
                    device = Device.objects.get(users__pk=self.user.user.id)
                    tokens.append(device.token)
                    notification.recipients.add(self.user.user)
                for invited_friend in invited_friends:
                    device = Device.objects.get(users__pk=invited_friend.user.user.id)
                    tokens.append(device.token)
                    notification.recipients.add(invited_friend.user.user)
                sendNotification(notification, tokens)
            except Exception as e:
                print 'Unable to send push notification when updateing event {0}'.format(self.id)
            '''
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
            '''
        super(EventComment, self).save()



