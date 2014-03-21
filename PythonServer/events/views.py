import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.forms.models import model_to_dict
from accounts.models import MeepUser
from models import Event, InvitedFriend


def UpcomingEvents(request):
    pass


def createEvent(request):
    pass


def updateEvent(request):
    pass