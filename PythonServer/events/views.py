import json
import logging
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
    pass


def updateEvent(request):
    pass


def selectAttending(request):
    pass