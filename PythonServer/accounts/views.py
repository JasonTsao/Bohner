import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.forms.models import model_to_dict
from accounts.models import Account
from django.shortcuts import render_to_response
from events.models import Event, InvitedFriend
from forms import RegisterForm


def createUser(request):
    form = RegisterForm()
    return render_to_response("accounts/register.html", {}, context_instance=RequestContext(request))


def updateUser(request):
    pass


def syncUserFacebook(request):
    pass

