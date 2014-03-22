import json
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from accounts.models import MeepUser
from models import Event, EventLocation, InvitedFriend

logger = logging.getLogger("django.request")


@login_required
def UpcomingEvents(request):
    rtn_dict = {'success': False, "msg": ""}
    try:
        rtn_dict['upcoming_events'] = []
        meep_user = MeepUser.objects.filter(user=request.user)

        owned_events = Event.objects.filter(creator=meep_user).order_by('time')
        for event in owned_events:
            if not event.event_over and not event.cancelled:
                rtn_dict['upcoming_events'].append(model_to_dict(event)) 

        invited_users = InvitedFriend.objects.select_related('event').filter(user=meep_user).order_by('time')
        for invited_user in invited_users:
            if not invited_user.event.event_over and not invited_user.event.cancelled:
                if invited_user.event.creator != meep_user:
                    rtn_dict['upcoming_events'].append(model_to_dict(invited_user.event))
    except Exception as e:
        logger.info('Error grabbing upcoming events: {0}'.format(e))

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def createEvent(request):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            user = MeepUser.objects.get(user=request.user)
            event = Event(creator=user)
            event.name = request.POST['name']
            event.time = request.POST['time']
            event.description = request.POST['description']
            event.location_name = request.POST['location_name']
            event.location_address = request.POST['location_address']
            event.location_coordinates = request.POST['location_coordinates']
            event.save()

            event_location = EventLocation(event=event)
            event_location.location_name = event.location_name
            event_location.location_address = event.location_address
            event_location.location_coordinates = event.location_coordinates
            event_location.save()

            try:
                invited_friends = request.POST['invited_friends']
                for user_name in invited_friends:
                    try:
                        meep_user = MeepUser.objects.get(user_name=user_name)
                        invited_friend = InvitedFriend(event=event, user=meep_user)
                        invited_friend.save()
                    except Exception as e:
                        logger.info('Error adding user {0}: {1}'.format(user,e))
            except:
                pass

            rtn_dict['success'] = True
            rtn_dict['msg'] = 'Successfully created new user event!'

        except Exception as e:
            logger.info('Error creating new event: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating new event: {0}'.format(e)

    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def updateEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        event = Event.objects.get(pk=event_id)
        if request.POST['name']:
            event.name = request.POST['name']
        if request.POST['time']:
            event.time = request.POST['time']
        if request.POST['description']:
            event.description = request.POST['description']
        if request.POST['location_name']:
            event.location_name = request.POST['location_name']
        if request.POST['location_address']:
            event.location_address = request.POST['location_address']
        if request.POST['location_coordinates']:
            event.location_coordinates = request.POST['location_coordinates']
        event.save()
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'Successfully updated {0} to {1}!'.format(field, value)
    except Exception as e:
        logger.info('Error updating event {0}: {1}'.format(event_id, e))
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
def selectAttending(request):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
        try:
            user = MeepUser.objects.get(pk=request.POST['user_id'])
            event = Event.objects.get(pk=request.POST['event_id'])
            invited_friend = InvitedFriend.objects.get(event=event, user=user)
            if request.POST['attending']:
                invited_friend.attending = True
            else:
                invited_friend.attending = False
            invited_friend.save()
        except Exception as e:
            logger.info('Error selected attending for event {0}: user {1}'.format(event.id, user.id , e))

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")