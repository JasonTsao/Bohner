import json
import logging
import ast
from celery import task
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from accounts.models import Account, AccountLink, Group, AccountSetting, AccountSettings
from events.models import Event, EventNotification, EventCreatorLocation, EventComment, InvitedFriend
from rediscli import r as R

logger = logging.getLogger("django.request")


def addedFriendPushNotification(recipient, notification):
	rtn_dict = {'success': False, "msg": ""}
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def eventPushNotification(event, notification):
	rtn_dict = {'success': False, "msg": ""}
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")

def sendPushNotification(recipient, notification):
	rtn_dict = {'success': False, "msg": ""}
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")