from django.db import models
from django.contrib.auth.models import User


# Create your models here.
class Account(models.Model):
    user = models.ForeignKey(User)
    user_name = models.CharField(max_length=255)
    first_name = models.CharField(max_length=255)
    last_name = models.CharField(max_length=255)
    phone_number = models.CharField(max_length=255, null=True, blank=True)
    email = models.CharField(max_length=255, null=True, blank=True) 
    facebook = models.CharField(max_length=255, null=True, blank=True)
    uber = models.CharField(max_length=255, null=True, blank=True)

    created = models.DateTimeField(auto_now_add=True) 
    def __unicode__(self):
        return str('{0} : {1} {2}'.format(self.user_name,self.first_name, self.last_name))


class AccountLink(models.Model):
	account_user = models.ForeignKey(Account, related_name='account_user')
	friend = models.ForeignKey(Account, related_name='friend')
	invited_count = models.IntegerField(default=0)
	models.DateTimeField(auto_now_add=True)
	def __unicode__(self):
		return str('{0} : {1}'.format(self.user.user_name,self.friend.user_name))


class Group(models.Model):
	group_creator = models.ForeignKey(Account, related_name='group_creator') 
	name = models.CharField(max_length=255)
	created = models.DateTimeField(auto_now_add=True)
	members = models.ManyToManyField(Account)

