import json
import logging
import ast
import urllib2
import os
import time
import datetime


from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required

from django.forms.models import model_to_dict

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
from ios_notifications.utils import generate_cert_and_pkey
#from accounts.models import Account, AccountLink, Group, AccountSetting, AccountSettings
#from events.models import Event, EventNotification, EventCreatorLocation, EventComment, InvitedFriend
#from notifications.models import Notification as MeepNotification
from rediscli import r as R

logger = logging.getLogger("django.request")

TOKEN = '0fd12510cfe6b0a4a89dc7369c96df956f991e66131dab63398734e8000d0029'
TEST_PEM = os.path.abspath(os.path.join(os.path.dirname(__file__), 'test.pem'))
DEV_PEM = os.path.abspath(os.path.join(os.path.dirname(__file__), 'meep_dev_key.pem'))

SSL_SERVER_COMMAND = ('openssl', 's_server', '-accept', '2195', '-cert', TEST_PEM)

CERTIFICATE = '-----BEGIN CERTIFICATE-----MIIFfjCCBGagAwIBAgIIJAD7fEH9Fd8wDQYJKoZIhvcNAQEFBQAwgZYxCzAJBgNVBAYTAlVTMRMwEQYDVQQKDApBcHBsZSBJbmMuMSwwKgYDVQQLDCNBcHBsZSBXb3JsZHdpZGUgRGV2ZWxvcGVyIFJlbGF0aW9uczFEMEIGA1UEAww7QXBwbGUgV29ybGR3aWRlIERldmVsb3BlciBSZWxhdGlvbnMgQ2VydGlmaWNhdGlvbiBBdXRob3JpdHkwHhcNMTQwNTI0MTgxODQwWhcNMTUwNTI0MTgxODQwWjB+MR0wGwYKCZImiZPyLGQBAQwNY29tLm1lZXAubWVlcDE7MDkGA1UEAwwyQXBwbGUgRGV2ZWxvcG1lbnQgSU9TIFB1c2ggU2VydmljZXM6IGNvbS5tZWVwLm1lZXAxEzARBgNVBAsMCjRIMkVaQTVDRDgxCzAJBgNVBAYTAlVTMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIBCgKCAQEAx24ngR2LDRJ9Mb+N5cC049zy0ZhUm6BesE2kH/nDSRaFDacMj4am7wbIt+ZJvKvjl8FmK5FzzzpbzLYtl2rA1xsYfruRaafQBdE9oCluKCMQ/AJUygLt1TmGhwfsvyNEvEOWvb5fUsSXJBEAvf+PQb7LtMDM6JdOPj1n2XFzcoyrebPb/OItd/6IBwKBFJ1lqxBg0sgAP5+aRLLJsbL1J1cwHvziZisbLCScR/jpOeTAeuHh8U7f6uwLds68VqvtyY6OkEqzpNjjWIMxZP5mtquftbPz5BfKLwnBM0Y5yQdgWQwt8GgUd6dwv+unjIO/wZVUJmvdM4D7Z/MHzLXzJwIDAQABo4IB5TCCAeEwHQYDVR0OBBYEFL/OplbD7WtzVI857YahlRXagAxJMAkGA1UdEwQCMAAwHwYDVR0jBBgwFoAUiCcXCam2GGCL7Ou69kdZxVJUo7cwggEPBgNVHSAEggEGMIIBAjCB/wYJKoZIhvdjZAUBMIHxMIHDBggrBgEFBQcCAjCBtgyBs1JlbGlhbmNlIG9uIHRoaXMgY2VydGlmaWNhdGUgYnkgYW55IHBhcnR5IGFzc3VtZXMgYWNjZXB0YW5jZSBvZiB0aGUgdGhlbiBhcHBsaWNhYmxlIHN0YW5kYXJkIHRlcm1zIGFuZCBjb25kaXRpb25zIG9mIHVzZSwgY2VydGlmaWNhdGUgcG9saWN5IGFuZCBjZXJ0aWZpY2F0aW9uIHByYWN0aWNlIHN0YXRlbWVudHMuMCkGCCsGAQUFBwIBFh1odHRwOi8vd3d3LmFwcGxlLmNvbS9hcHBsZWNhLzBNBgNVHR8ERjBEMEKgQKA+hjxodHRwOi8vZGV2ZWxvcGVyLmFwcGxlLmNvbS9jZXJ0aWZpY2F0aW9uYXV0aG9yaXR5L3d3ZHJjYS5jcmwwCwYDVR0PBAQDAgeAMBMGA1UdJQQMMAoGCCsGAQUFBwMCMBAGCiqGSIb3Y2QGAwEEAgUAMA0GCSqGSIb3DQEBBQUAA4IBAQCzG5eMhY4yRmTTqhgXk2Bm128aIPGgjZZCSLcnSOvqcwvMTecVoG77iVpVIbiKlKQfhWCEfgXYjnXMwpScVjDb0u+ywsI12tfuy6wmMCTV2Go3Ux+DGB+wrxPFWQFLyMGLkPtUJ3przEZYmzx1Dd869FjSFvORXNImYhywJZWKZ1IIFFmyR8d/a5rVIjIjnh160ONxiJtYSO7xkVHl7jr82M40VyB3IUxyPM2m/zxlhFIjPgukXliZTzXlRNOKDRXYaRF4cb23W0YzJGtY3mqQuMyDTVkmZi0fO8jU0+WMwgVOn6+JJVQaLiHRmH+2Zef6CFNnOYyzpH7O04ckR25Z-----END CERTIFICATE-----'
PRIVATE_KEY = '-----BEGIN RSA PRIVATE KEY-----MIIEpAIBAAKCAQEAx24ngR2LDRJ9Mb+N5cC049zy0ZhUm6BesE2kH/nDSRaFDacMj4am7wbIt+ZJvKvjl8FmK5FzzzpbzLYtl2rA1xsYfruRaafQBdE9oCluKCMQ/AJUygLt1TmGhwfsvyNEvEOWvb5fUsSXJBEAvf+PQb7LtMDM6JdOPj1n2XFzcoyrebPb/OItd/6IBwKBFJ1lqxBg0sgAP5+aRLLJsbL1J1cwHvziZisbLCScR/jpOeTAeuHh8U7f6uwLds68VqvtyY6OkEqzpNjjWIMxZP5mtquftbPz5BfKLwnBM0Y5yQdgWQwt8GgUd6dwv+unjIO/wZVUJmvdM4D7Z/MHzLXzJwIDAQABAoIBAQCakrpzzN4155q5sGrfJRoPcvWRlqwdY5OAuuz3C7NdNuMxzcRiik9g/LUeNJP6dJAW04PJSRemCumUJa/4qHmHQC0gLWlrpvIJUECfnv0Ohv9nFLd7TAHjPo8SogXRsBhag1iXALMJh+5NuhAFM8tpfeSN2NH5hSzT+OxBEToWEaucnrtnJHLs3QMektp3j45YiAuCgglrE2zRSJAQYF5dQLS3JqTcfpgNIv1tneZd9VfC5L0z8Wfh8giN5JF/VR2PyL1bgY73jdegAxL43PLIrGZtguuJZzhmhLbpO1OId09aevpYww3GEwwfX78MIFFIinksC61rOgIB9972vY5hAoGBAOS5t8jnNO/RWvaHbXk6ZU92q6gMpFEUCLwdQ6HFnAGG5eBrmkqAtyWhbcW/uPmFn6ucGBmiWaW7phY+DYSjUjmffeAEgBwd1ligUmH5o2o8l0scE+HMHNZRjK2cX9Nu3LpdCrMuS1cSg/M0ddqIXad77aD0/N5e54NrWhzthZILAoGBAN82JTLtMrQegUxLXDeY2msImIzvcAHBoQdLjWNECp7j1s1kqs2VkLkv3LQ361QtfN+HNvamk4RkubgE5mTbfn1TvhWZFOfqh/qXzTWbIf+SvPIIZH7PVVENQowr0uwb0gevtk1cgOW/cnZqmf6MNJ9VYWBjGeqyc/JKuXMS0FDVAoGAK/pNjRJvikDtxYMKmImS2zGNFdXAblp0x36091Dgiyad4oWt9+9Bx7l/Ost/THLV3ZA4zgz6QbSP3az2um8Qq0WwVTdoTn+qLAY/cNkoA5A84tM2O28ciFTLwMHVZvjk9exX11XqZIaJ2mRW2Lrpjv90FEOmrzb+OrWUcQV2bjsCgYEAo0EZ0faUmBKbpO6VYwCD97bQxHu3Y0F4gjprDchNMEsZ5x2So0yaDigIdzNTBj1C0MY3mAzbZgC5qPLEg83Z5NYj9+3/0WPC0rDGYUe2hROQ6EDlJ66DCwX0v0qqORBb/E0yu8BFckQk9qEfQoLPVh3/W5z/7p1YmkS3AIgpHoUCgYBDr/uG769itCkG/IHwZfx1uaeKrV8woWs3htAgQbk4TZ/PMttPiPq3u0nLqkCiSwDmG7JUtFPmzS5L3JSzqlhrU29JpKbAYS4cEtoHHh/wPko3yzTLWCcOO/m/3k5XiPrugjy8/inqT1TnyUYWoB8ywEUZftHFbUcGlCDGXY6j1A==-----END RSA PRIVATE KEY-----'

@task
def pushToNOSQLHash(key, push_item):
	r = R.r
	r.hmset(key, push_item)


@task
def pushToNOSQLSet(key, push_item, delete_item, score):
	r = R.r
	r.zadd(key, push_item, score)
	if delete_item:
		r.zrem(key, delete_item)


@login_required
@csrf_exempt
def getNotifications(request):
	rtn_dict = {'success': False, "msg": "", "notifications":[]}
	try:
		service = APNService.objects.get(pk=1)
		notifications = Notification.objects.filter(recipients__pk=request.user.id, service=service).order_by('-created_at')
		notifications_array = []
		for notification in notifications:
			notification_dict = {}
			notification_dict['message'] = notification.message
			created_at = time.mktime(notification.created_at.timetuple())
			notification_dict['created_at'] = created_at
			notification_dict['id'] = notification.id
			notification_dict['notification_type'] = notification.notification_type
			notification_dict['extra'] = notifications.custom_payload
			notifications_array.append(notification_dict)
		rtn_dict['notifications'] = notifications_array
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'Successfully pulled notifications'
	except Exception as e:
		print 'unable to grab notifications for user: {0}'.format(e)
		rtn_dict['msg'] = 'unable to grab notifications for user: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def testIOSNotificationAPI(request):
	rtn_dict = {'success': False, "msg": ""}
	try:
		pass
	except Exception as e:
		print 'Error running ios notification test: {0}'.format(e)
		rtn_dict['msg'] = 'Error running ios notification test: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def createAPNService(request):
	#cert, key = generate_cert_and_pkey()
	service = APNService.objects.create(name='sandbox', hostname='gateway.sandbox.push.apple.com', certificate=CERTIFICATE, private_key=PRIVATE_KEY)


def createNotification(message, notification_type, custom_payload=False, recipients=[]):
	service = APNService.objects.get(hostname='gateway.sandbox.push.apple.com', name='sandbox')
	notification = Notification(message=message, service=service)
	if custom_payload:
		notification.custom_payload = custom_payload
	notification.badge = None
	notification.notification_type = notification_type
	notification.save()
	for recipient in recipients:
		notification.recipients.add(recipient)
	return notification


def addNotificationToRedis(notification, account_id):
	redis_key = 'account.{0}.notifications.set'.format(account_id)
	score = int(notification.created_at.strftime("%s"))
	notification_dict = model_to_dict(notification)
	notification_dict = json.dumps(notification_dict)
	pushToNOSQLSet(redis_key, notification_dict, False,score)


def sendNotification(notification, device_tokens):
	rtn_dict = {'success': False, "msg": ""}
	try:
		service = APNService.objects.get(hostname='gateway.sandbox.push.apple.com', name='sandbox')
		devices = Device.objects.filter(token__in=device_tokens, service=service)
		service.push_notification_to_devices(notification=notification, devices=devices, chunk_size=100)
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


def registerUserToDevice(request, device_id):
	rtn_dict = {'success': False, "msg": ""}
	try:
		device = Device.objects.get(pk=device_id)
		device.users.add(request.user)
	except Exception as e:
		rtn_dict['msg'] = "Error registering user to device: {0}".format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


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

'''
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
'''
