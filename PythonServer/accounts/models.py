import timedelta
from django.db import models
from django.contrib.auth.models import User
from ios_notifications.models import APNService, Notification, Device
from notifications.api import createNotification, sendNotification

GENDER = (
    ('male', 'Male'),
    ('female', 'Female'),
)

# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(User)
    user_name = models.CharField(max_length=255, unique=True)
    display_name = models.CharField(max_length=255, null=True, blank=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, unique=True)
    facebook_id = models.CharField(max_length=255, null=True, blank=True)
    uber = models.CharField(max_length=255, null=True, blank=True)
    profile_pic =  models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True, choices=GENDER)
    birthday = models.DateField(null=True,blank=True)
    home_town = models.CharField(max_length=255, null=True, blank=True)
    is_active = models.NullBooleanField(default=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    def __unicode__(self):
        return str('{0} : {1} {2}'.format(self.user_name,self.first_name, self.last_name))
    def save(self, user=None, *args, **kwargs):
        if self.pk:
            if not self.display_name:
                self.display_name = '{0} {1}'.format(self.first_name, self.last_name)
        super(Account, self).save()


class AccountDeviceID(models.Model):
    account = models.ForeignKey(Account)
    device_id = models.CharField(max_length=255, null=True, blank=True)
    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)


class AccountSettings(models.Model):
    account = models.OneToOneField(Account)
    private = models.NullBooleanField(default=False)
    searchable = models.NullBooleanField(default=True)
    reminder_on = models.NullBooleanField(default=True)
    reminder_delta = timedelta.fields.TimedeltaField(null=True,blank=True)
    vibrate_on_notification = models.NullBooleanField(default=True)


class AccountSetting(models.Model):
    account = models.ForeignKey(Account)
    setting_name = models.CharField(max_length=255)
    setting_value = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateField(auto_now_add=True, null=True, blank=True)    # NOW
    modified = models.DateField(auto_now=True)                              # auto update time

    class Meta:
        unique_together = (('account', 'setting_name'),)


class AccountLink(models.Model):
    account_user = models.ForeignKey(Account, related_name='account_user')
    friend = models.ForeignKey(Account, related_name='friend')
    invited_count = models.IntegerField(default=0)
    created = models.DateTimeField(auto_now_add=True)
    blocked = models.NullBooleanField(default=False)

    def save(self, create_notification=None, *args, **kwargs):
        if not self.pk and create_notification:
            try:
                user = self.account_user.user
                message = "You have just been joined by {0} on Meep".format(self.friend.user_name)
                custom_payload = {"joined_by_name": friend.user_name, "joined_by_id": friend.id}
                custom_payload = json.dumps(custom_payload)
                notification = createNotification(message, custom_payload)
                notification.recipients.add(user)
                tokens = []
                device = Device.objects.get(users__pk=user.id)
                tokens.append(device.token)
                sendNotification(notification, tokens)
            except Exception as e:
                print 'Unable to send push notification when {0} tried adding friend {1}'.format(self.account_user, self.friend)
        super(AccountLink, self).save()

    def __unicode__(self):
        return str('{0} : {1}'.format(self.account_user.user_name,self.friend.user_name))
    class Meta:
        unique_together = (('account_user', 'friend'),)
    

class Group(models.Model):
    group_creator = models.ForeignKey(Account, related_name='group_creator') 
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Account)
    is_active = models.NullBooleanField(default=True)
    created = models.DateTimeField(auto_now_add=True)
    def __unicode__(self):
        return str('{0} : {1}'.format(self.name,self.group_creator.id))
    class Meta:
        unique_together = (('group_creator', 'name'),)