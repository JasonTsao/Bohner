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


def createNotification(request):
	rtn_dict = {'success': False, "msg": ""}
	service = APNService.objects.get(pk=2)
	notification = Notification.objects.create(message='Test message', service=service)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def sendNotification(devices_to_notify):
	rtn_dict = {'success': False, "msg": ""}
	service = APNService.objects.get(pk=2)
	notification = Notification.objects.create(message='Test message', service=service)
	devices = []
	for device in devices_to_notify:
		try:
			devices.append(Device.objects.get(pk=device))
		except Exception as e:
			print "Couldn't grab device with device id {0}: {1}".format(device, e)
	service.push_notification_to_devices(notification=notification, devices=devices)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def registerDevice(request):
	rtn_dict = {'success': False, "msg": ""}
	url = 'http://127.0.0.1:8000/ios-notifications/device/'

	if request.method == 'POST':
		try:
			TOKEN = request.POST['token']
			service_id = request.POST['service_id']
			service_id = 2
			service = APNService.objects.get(pk=service_id)
			device = Device.objects.create(token=TOKEN, service=service)

			#NEED TO CHANGE TO ACTUALLY POSTING TO DEVICE CREATE METHOD IN CLASS
			client = Client()
			resp = client.post(reverse('ios-notifications-device-create'),
	                                {'token': device.token,
	                                 'service': service.id})
			content = resp.content
			device_json = json.loads(content)
			#device_data = urllib2.urlopen(url)
			rtn_dict['success'] = True
			rtn_dict['msg'] = 'Successfully registered device :{0}'.format(device.id)
		except Exception as e:
			print 'Error retrieving device data: {0}'.format(e)
	else:
		rtn_dict['msg'] = 'Called using GET instead of POST'

	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateDevice(request):
	rtn_dict = {'success': False, "msg": ""}
	try:
		#device_id = request.POST['device_id']
		device_id = 1
		device = Device.objects.get(pk=device_id)
		#token = device.token
		token = TOKEN
		#service_id = request.POST['service_id']
		service_id = 2
		service = APNService.objects.get(pk=service_id)
		
		kwargs = {'token': token, 'service__id': service.id}
		url = reverse('ios-notifications-device', kwargs=kwargs)
		client = Client()
		resp = client.put(url, 'users=%d&platform=iPhone' % request.user.id,
                               content_type='application/x-www-form-urlencode')
		device_json = json.loads(resp.content)
		print device_json
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'Successfully updated device {0}'.format(device.id)
	except Exception as e:
		print 'Error updating device: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def getDeviceDetails(request, device_id):
	rtn_dict = {'success': False, "msg": ""}
	try:
		device = Device.objects.get(pk=device_id)
		kwargs = {'token': device.token, 'service__id': device.service.id}
		url = reverse('ios-notifications-device', kwargs=kwargs)
		client = Client()
		resp = client.get(url)
		content = resp.content
		device_json = json.loads(content)
		print device_json
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
