import json
import logging
import ast
import urllib2
import os

from ios_notifications.management.commands.push_ios_notification import Command
from ios_notifications.models import APNService, Notification, Device
from ios_notifications.utils import generate_cert_and_pkey
from django.test.client import Client

from celery import task
from django.http import HttpResponse
from django.core.urlresolvers import reverse
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from accounts.api import pushToNOSQLHash, pushToNOSQLSet
from accounts.models import Account, AccountLink, Group, AccountSetting, AccountSettings
from events.models import Event, EventNotification, EventCreatorLocation, EventComment, InvitedFriend
from notifications.models import Notification as MeepNotification
from rediscli import r as R

logger = logging.getLogger("django.request")

TOKEN = '0fd12510cfe6b0a4a89dc7369c96df956f991e66131dab63398734e8000d0029'
TEST_PEM = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.pem'))

SSL_SERVER_COMMAND = ('openssl', 's_server', '-accept', '2195', '-cert', TEST_PEM)


def testIOSNotificationAPI(request):
	rtn_dict = {'success': False, "msg": ""}
	try:
		pass
	except Exception as e:
		print 'Error running ios notification test: {0}'.format(e)
		rtn_dict['msg'] = 'Error running ios notification test: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def createAPNService(request):
	cert, key = generate_cert_and_pkey()
	service = APNService.objects.create(name='test-service', hostname='127.0.0.1', certificate=cert, private_key=key)


def createNotification(message, custom_payload=False):
	service = APNService.objects.get(hostname='gateway.push.apple.com', name='sandbox')
	notification = Notification(message=message, service=service)
	if custom_payload:
		notification.custom_payload = custom_payload
	notification.badge = None
	notification.save()
	return notification


def sendNotification(notification, device_tokens):
	rtn_dict = {'success': False, "msg": ""}

	try:
		service = APNService.objects.get(hostname='gateway.push.apple.com', name='sandbox')
		devices = Device.objects.filter(token__in=device_tokens, service=service)
		service.push_notification_to_devices(notification=notification, devices=devices, chunk_size=200)
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'successfully pushed notifications to devices {0}'.format(device_tokens)
	except Exception as e:
			print "Error sending push notifications: {1}".format(e)
			rtn_dict['msg'] = "Error sending push notifications: {1}".format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def registerDevice(user, token):
	service = APNService.objects.get(hostname='gateway.push.apple.com', name='sandbox')
	device = Device(token=token, service=service)
	device.save()
	device.users.add(user)
	return True


def updateDevice(request):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'PUT':
		try:
			device = Device.objects.get(token=request.PUT['token'], service=request.PUT['service'])
		except Device.DoesNotExist:
			return JSONResponse({'error': 'Device with token %s and service %s does not exist' %
                                (request.PUT['token'], request.PUT['service__id'])}, status=400)

		if 'users' in request.PUT:
			try:
				user_ids = request.PUT.getlist('users')
				device.users.remove(*[u.id for u in device.users.all()])
				device.users.add(*User.objects.filter(id__in=user_ids))
			except (ValueError, IntegrityError) as e:
				return JSONResponse({'error': e.message}, status=400)
			del request.PUT['users']

		device.is_active = request.PUT['is_active']
		device.platform = request.PUT['platform']
		device.display = request.PUT['display']
		device.os_version = request.PUT['os_version']
		device.save()
	else:
		'Request method was {0} not PUT'.format(request.method)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def getDeviceDetails(request, device_id):
	rtn_dict = {'success': False, "msg": ""}
	try:
		device = Device.objects.get(pk=device_id)
		rtn_dict['device'] = model_to_dict(device)
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'Successfully got device details for device {0}'.format(device_id)
	except Exception as e:
		print 'Error getting device details for device {0}'.format(device_id)
		rtn_dict['msg'] = 'Error getting device details for device {0}'.format(device_id)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


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
