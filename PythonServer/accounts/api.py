import json
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.forms.models import model_to_dict
from accounts.models import MeepUser
from events.models import Event, InvitedFriend
from django.contrib.auth.hashers import make_password


def registerUser(request):
	rtn_dict = {'success': False, "msg": ""}

	if request.method == 'POST':
		try:
			new_user = User(username=request.POST.get("username"))
			new_user.is_active = True
			new_user.password = make_password(request.POST.get('password1'))
			new_user.email = request.POST.get('email')
			new_user.save()
			user = authenticate(username=request.POST.get("username"), password=request.POST.get("password1"))
			login(request, user)
			rtn_dict['success'] = True
			rtn_dict['msg'] = 'Successfully registered new user'
		except Exception as e:
			logger.info('Error registering new user: {0}'.format(e))
			rtn_dict['msg'] = 'Error registering new user: {0}'.format(e)

	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateUser(request):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
		try:
			user = User.objects.get(pk=user.id)

			'''
				Update fields that need to be updated
			'''
		except Exception as e:
			logger.info('Error registering new user: {0}'.format(e))
			rtn_dict['msg'] = 'Error registering new user: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateMeepUser(request):
	pass


def syncUserFacebook(request):
    pass
