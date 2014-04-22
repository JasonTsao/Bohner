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


def searchByEmail(request):
	return render_to_response("accounts/search_by_email.html", {}, context_instance=RequestContext(request))


def addFriend(request):
	return render_to_response("accounts/add_friend.html", {}, context_instance=RequestContext(request))


def updateUser(request):
	return render_to_response("accounts/account_update_field.html", {}, context_instance=RequestContext(request))
    #return render_to_response("accounts/update_user.html", {}, context_instance=RequestContext(request))


def createGroup(request):
	return render_to_response("accounts/create_group.html", {}, context_instance=RequestContext(request))


def addUsersToGroup(request, group_id):
	return render_to_response("accounts/group_add_users.html", {"group_id": group_id}, context_instance=RequestContext(request))


def removeUsersFromGroup(request):
	return render_to_response("accounts/remove_users_from_group.html", {}, context_instance=RequestContext(request))


def updateGroup(request, group_id):
	return render_to_response("accounts/update_group.html", {"group_id": group_id}, context_instance=RequestContext(request))

def updateSettingField(request):
	return render_to_response("accounts/account_setting_field_update.html", {}, context_instance=RequestContext(request))

def syncUserFacebook(request):
    pass

