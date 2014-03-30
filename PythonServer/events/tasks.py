import json
import logging
import pickle
import simplejson
import ast
from celery import task
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.contrib.auth.models import User
from accounts.models import Account, AccountLink
from accounts.api import pushToNOSQLSet, pushToNOSQLHash
from notifications.api import eventPushNotification, sendPushNotification
from models import Event, EventComment, EventNotification, InvitedFriend
from rediscli import r as R

logger = logging.getLogger("django.request")


@task
def populateUserUpcomingEvents(account_id):
	try:
		upcoming_events = []
        owned_events = Event.objects.filter(creator=account_id, event_over=False,cancelled=False).order_by('start_time')
        for event in owned_events:
            upcoming_events.append(model_to_dict(event)) 

        invited_users = InvitedFriend.objects.select_related('event').filter(user=account_id)
        for invited_user in invited_users:
            if not invited_user.event.event_over and not invited_user.event.cancelled:
                if invited_user.event.creator != account_id:
               		upcoming_events.append(json.dumps(model_to_dict(invited_user.event)))

       	r = R.r
       	r_upcoming_events_key = 'account.{0}.events.set'.format(account_id)
       	r.delete(r_upcoming_events_key)
       	for upcoming_event in upcoming_events:
       		r.zadd(r_upcoming_events_key, upcoming_event, 0)
	except Exception as e:
		print 'Error populating NOSQL layer with upcoming events for user {0}: {1}'.format(account_id, e)
		return False
	return True

@task
def populateEventComments(event_id):
	try:
		r = R.r
		r_event_comments_key = 'event.{0}.comments.set'.format(event_id)
		r.delete(r_event_comments_key)
		event_comments = EventComment.objects.filter(event=event_id)
		for event_comment in event_comments:
			event_comment_dict = json.dumps(model_to_dict(event_comment))
	        pushToNOSQLSet(r_event_comments_key, event_comment_dict, False, 0)
	except Exception as e:
		print 'Error populating NOSQL layer with invited friends for event {0}: {1}'.format(event_id, e)
		return False

	return True


@task
def populateEventInvitedFriends(event_id):
	try:
		r = R.r
		r_event_invited_friends_key = 'event.{0}.invited_friends.set'.format(event_id)
		r.delete(r_event_invited_friends_key)
		invited_friends = InvitedFriend.objects.filter(event=event_id)
		for invited_friend in invited_friends:
			invited_friend_dict = json.dumps({
	                                                'invited_friend_id': invited_friend.id,
	                                                'friend_id':invited_friend.user.id,
	                                                'pf_pic': invited_friend.user.profile_pic,
	                                                'name': invited_friend.user.display_name,
	                                                "attending": False})
	        pushToNOSQLSet(r_event_invited_friends_key, invited_friend_dict, False, 0)
	except Exception as e:
		print 'Error populating NOSQL layer with invited friends for event {0}: {1}'.format(event_id, e)
		return False

	return True