import json
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from accounts.models import Account
from models import Event, InvitedFriend

logger = logging.getLogger("django.request")


@login_required
def checkIfAuthorized(event, account):
    is_authorized = False
    # Make sure user is authorized to leave a comment on this event
    if event.creator == account:
        is_authorized = True

    if not is_authorized:
        try:
            invited_friend = InvitedFriend.objects.get(event=event, user=account)
            is_authorized = True
        except:
            pass
    return is_authorized


@login_required
def getEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    try:
        account = Account.objects.get(user=request.user)
        event = Event.objects.get(pk=event_id)
        is_authorized = checkIfAuthorized(event, account)
        if is_authorized:
            rtn_dict['event'] = model_to_dict(event)
            rtn_dict['success'] = True
            rtn_dict['msg'] = 'successfully got event'
    except Exception as e:
        logger.info('Error grabbing events {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error grabbing events {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def upcomingEvents(request):
    rtn_dict = {'success': False, "msg": ""}
    try:
        rtn_dict['upcoming_events'] = []
        account = Account.objects.filter(user=request.user)

        owned_events = Event.objects.filter(creator=account).order_by('start_time')
        for event in owned_events:
            if not event.event_over and not event.cancelled:
                rtn_dict['upcoming_events'].append(model_to_dict(event)) 

        invited_users = InvitedFriend.objects.select_related('event').filter(user=account)
        for invited_user in invited_users:
            if not invited_user.event.event_over and not invited_user.event.cancelled:
                if invited_user.event.creator != account:
                    rtn_dict['upcoming_events'].append(model_to_dict(invited_user.event))

        rtn_dict['success'] = True
        rtn_dict['message'] = 'Successfully retrieved upcoming events'
    except Exception as e:
        print 'Error grabbing upcoming events: {0}'.format(e)
        logger.info('Error grabbing upcoming events: {0}'.format(e))
        rtn_dict['msg'] = 'Error grabbing upcoming events: {0}'.format(e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def createEvent(request):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            user = Account.objects.get(user=request.user)
            event = Event(creator=user)
            event.name = request.POST['name']
            event.start_time = request.POST['start_time']
            event.end_time = request.POST['end_time']
            event.description = request.POST['description']
            event.location_name = request.POST['location_name']
            event.location_address = request.POST['location_address']
            event.location_coordinates = request.POST['location_coordinates']
            event.friends_can_invite = reqest.POST['friends_can_invite']
            event.save()

            try:
                invited_friends = request.POST['invited_friends']
                for user_dict in invited_friends:
                    try:
                        user_id = user_dict['user_id']
                        can_invite_friends = user_dict['can_invite_friends']
                        account = Account.objects.get(pk=user_id)
                        invited_friend = InvitedFriend(event=event, user=account, can_invite_friends=can_invite_friends)
                        invited_friend.save()
                    except Exception as e:
                        logger.info('Error adding user {0}: {1}'.format(user,e))
            except:
                logger.info('Error inviting friends: {0}'.format(e))

            rtn_dict['success'] = True
            rtn_dict['msg'] = 'Successfully created new user event!'

        except Exception as e:
            logger.info('Error creating new event: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating new event: {0}'.format(e)

    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def inviteFriends(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    is_authorized = False
    if request.method == 'POST':
        try:
            invited_friends = request.POST['invited_friends']
            event = Event.objects.get(pk=event_id)

            # check to see if this use is allowed to invite more friends to event
            try:
                account = Account.objects.get(user=request.user)
                if event.creator == account:
                    is_authorized = True
            except:
                pass

            try:
                invited_friend = InvitedFriend.objects.get(event=Event, user=account)
                if inivited_friend.can_invite_friends:
                    is_authorized = True
            except:
                pass

            if is_authorized:
                for user_dict in invited_friends:
                    try:
                        user_id = user_dict['user_id']
                        can_invite_friends = user_dict['can_invite_friends']
                        account = Account.objects.get(pk=user_id)
                        invited_friend = InvitedFriend(event=event, user=account, can_invite_friends=can_invite_friends)
                        invited_friend.save()
                        rtn_dict['success'] = True
                        rtn_dict['msg'] = 'Successfully added users'
                    except Exception as e:
                        logger.info('Error adding user {0}: {1}'.format(user,e))
                        rtn_dict['msg'] = 'Error adding user {0}: {1}'.format(user,e)
                
            else:
                rtn_dict['msg'] = 'user if not authorized to invite other friends: {0}'.format(e)
        except Exception as e:
            logger.info('Error inviting friends: {0}'.format(e))
            rtn_dict['msg'] = 'Error inviting friends: {0}'.format(e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def updateEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        event = Event.objects.get(pk=event_id)
        try:
            event.name = request.POST['name']
        except:
            pass
        try:
            event.start_time = request.POST['start_time']
        except:
            pass
        try:
            event.end_time = request.POST['end_time']
        except:
            pass
        try:
            event.description = request.POST['description']
        except:
            pass
        try:
            event.location_name = request.POST['location_name']
        except:
            pass
        try:
            event.location_address = request.POST['location_address']
        except:
            pass
        try:
            event.location_coordinates = request.POST['location_coordinates']
        except:
            pass
        try:
            event.friends_can_invite = request.POST['friends_can_invite']
        except:
            pass

        event.save()
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'Successfully updated {0} to {1}!'.format(field, value)
    except Exception as e:
        logger.info('Error updating event {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error updating event {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def selectAttending(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
        try:
            user = Account.objects.get(user=request.user)
            event = Event.objects.get(pk=event_id)
            invited_friend = InvitedFriend.objects.get(event=event, user=user)
            if request.POST['attending']:
                invited_friend.attending = True
            else:
                invited_friend.attending = False
            invited_friend.save()
        except Exception as e:
            logger.info('Error selected attending for event {0}: user {1}'.format(event.id, user.id , e))
            rtn_dict['msg'] = 'Error selected attending for event {0}: user {1}'.format(event.id, user.id , e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def createEventComment(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            account = Account.objects.get(user=request.user)
            event = Event.objects.get(pk=event_id)

            is_authorized = checkIfAuthorized(account, event)

            if is_authorized:
                new_comment = EventComment(event=event,user=account)
                new_comment.description = request.POST['description']
                new_comment.save()
            else:
                logger.info('user not authorized to create event comments')
                rtn_dict['msg'] = 'user not authorized to create event comments'
        except Exception as e:
            logger.info('Error creating event comment: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating event comment: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def getEventComments(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    try:
        comments = []
        account = Account.objects.get(user=request.user)
        event = Event.objects.get(pk=event_id)
        is_authorized = checkIfAuthorized(account, event)

        event_comments = EventComment.objects.filter(event=event)

        for event_comment in event_comments:
            comments.append(model_to_dict(event_comment))
        rtn_dict['comments'] = comments
    except Exception as e:
        logger.info('Error retrieving event comments: {0}'.format(e))
        rtn_dict['msg'] = 'Error retrieving event comments: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")