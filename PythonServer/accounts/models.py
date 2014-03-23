import timedelta
from django.db import models
from django.contrib.auth.models import User

GENDER = (
    ('male', 'Male'),
    ('female', 'Female'),
)

# Create your models here.
class Account(models.Model):
    user = models.OneToOneField(User)
    user_name = models.CharField(max_length=255, unique=True)
    first_name = models.CharField(max_length=255, null=True, blank=True)
    last_name = models.CharField(max_length=255, null=True, blank=True)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, unique=True) 
    facebook_id = models.CharField(max_length=255, null=True, blank=True)
    uber = models.CharField(max_length=255, null=True, blank=True)
    avatar =  models.CharField(max_length=255, null=True, blank=True)
    gender = models.CharField(max_length=255, null=True, blank=True, choices=GENDER)
    birthday = models.DateField(null=True,blank=True)
    home_town = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True)
    modified = models.DateTimeField(auto_now=True, blank=True, null=True)
    def __unicode__(self):
        return str('{0} : {1} {2}'.format(self.user_name,self.first_name, self.last_name))


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

    def __unicode__(self):
        return str('{0} : {1}'.format(self.user.user_name,self.friend.user_name))
    class Meta:
        unique_together = (('account_user', 'friend'),)
    

class Group(models.Model):
    group_creator = models.ForeignKey(Account, related_name='group_creator') 
    name = models.CharField(max_length=255)
    members = models.ManyToManyField(Account)
    created = models.DateTimeField(auto_now_add=True)