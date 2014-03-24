import json
import logging
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from django.shortcuts import render_to_response
from accounts.models import Account
from models import Event, InvitedFriend
from forms import EventForm

logger = logging.getLogger("django.request")


def createEvent(request):
    account = Account.objects.get(user=request.user)
    form = EventForm()
    #form.creator = account
    return render_to_response("events/create_event.html", {'form': form}, context_instance=RequestContext(request))


def inviteFriends(request):
    return render_to_response("events/invite_friend.html", {}, context_instance=RequestContext(request))


'''
def UpcomingEvents(request):
    pass

def updateEvent(request):
    pass


def selectAttending(request):
    pass
'''