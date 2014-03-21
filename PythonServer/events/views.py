import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from accounts.models import MeepUser
from models import Event, InvitedFriend

logger = logging.getLogger("django.request")

def UpcomingEvents(request):
    pass


def createEvent(request):
    rtn_dict = {'Success': False, "msg": ""}
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

            invited_friends = request.POST['invited_friends']
            for user_name in invited_friends:
                try:
                    meep_user = MeepUser.objects.get(user_name=user_name)
                    invited_friend = InvitedFriend(event=event, user=meep_user)
                    invited_friend.save()
                except Exception as e:
                    logger.info('Error adding user {0}: {1}'.format(user,e))

            rtn_dict['Success'] = True
            rtn_dict['msg'] = 'Successfully created new user event!'

        except Exception as e:
            logger.info('Error creating new event: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating new event: {0}'.format(e)

    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateEvent(request):
    pass


def selectAttending(request):
    pass