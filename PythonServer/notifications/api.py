import json
import logging
import ast
from celery import task
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from accounts.api import pushToNOSQLHash, pushToNOSQLSet
from accounts.models import Account, AccountLink, Group, AccountSetting, AccountSettings
from events.models import Event, EventNotification, EventCreatorLocation, EventComment, InvitedFriend
from notifications.models import Notification
from rediscli import r as R

logger = logging.getLogger("django.request")


def createEventNotificationDict(notification):
	notification_dict = {}
	try:
		notification_dict['event'] = notification.event.id
	except:
		notification_dict['event'] = ""
	notification_dict['creator'] = notification_creator
	notification_dict['message'] = notification.message
	notification_dict['created'] = str(notification.created)
	return notification_dict


def getNotifications(request):
	rtn_dict = {'success': False, "msg": "", "notifications": []}
	try:
		r = R.r
		account = Account.objects.get(user=request.user)
		r_notifications_key = 'account.{0}.notifications.set'.format(account.id)
		notifications_list = r.zrange(r_notifications_key, 0, 10)

		if not notifications_list:
			notifications_list = []
			notifications = Notification.objects.filter(recipients__id=account.id)
			for notification in notifications:
				notification_dict = createEventNotificationDict(notification)
				notifications_list.append(notification_dict)
				# TODO create task to fill redis with this information

		rtn_dict['notifications'] = notifications_list
	except Exception as e:
		logger.info('Error retrieving notifications: {0}'.format(e))
		rtn_dict['msg'] = 'Error retrieving notifications: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def addedFriendPushNotification(friend, recipient):
	notification = Notification(notification_creator=friend)
	notification.message = '{0} has just added you as a friend'.format(friend.user_name)
	notification.save()
	r_notification_key = 'account.{0}.notifications.set'.format(recipient.id)
	notification_string = json.loads(createEventNotificationDict(notification))
	pushToNOSQLSet(r_notification_key, notification_string, False, 0)
	sendPushNotification(recipient, notification)


def eventPushNotification(event, notification_type, notification_creator):
	invited_friends = InvitedFriend.objects.filter(event=event)
	notification = Notification(event=event)
	message = '{0} changed {1} on event {2}'.format(notification_creator, notification_type, event.name)
	notification.message = message
	notification.save()
	for invited_friend in invited_friends:
		notification.recipients.add(invited_friend)

	r = R.r
	for recipient in notification.recipients.all():
		r_notification_key = 'account.{0}.notifications.set'.format(recipient.id)
		notification_string = json.loads(createEventNotificationDict(notification))
		pushToNOSQLSet(r_notification_key, notification_string, False, 0)
		sendPushNotification(recipient, notification)


def sendPushNotification(recipient, notification):
	pass
