import json
import logging
import ast
from celery import task
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.contrib.auth import authenticate, login
from django.core.serializers.json import DjangoJSONEncoder
from django.forms.models import model_to_dict
from accounts.models import Account, AccountLink, Group, AccountSetting, AccountSettings
from events.models import Event, InvitedFriend
from django.contrib.auth.hashers import make_password
from forms import RegisterForm
from rediscli import r as R

logger = logging.getLogger("django.request")


@task
def pushToNOSQLHash(key, push_item):
	r = R.r
	r.hmset(key, push_item)


@task
def pushToNOSQLSet(key, push_item, delete_item, score):
	r = R.r
	r.zadd(key, push_item, score)
	if delete_item:
		r.zrem(key, delete_item)


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
			account = Account(user=user)
			account.email = user.email
			account.user_name = user.username
			account.save()

			r = R.r
			user_key = 'account.{0}.hash'.format(account.id)
			r.hmset(user_key, model_to_dict(account))


			rtn_dict['success'] = True
			rtn_dict['msg'] = 'Successfully registered new user'
		except Exception as e:
			logger.info('Error registering new user: {0}'.format(e))
			rtn_dict['msg'] = 'Error registering new user: {0}'.format(e)
	else:
		rtn_dict['msg'] = 'Not POST'

	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#login_required
def updateUser(request):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
		try:
			user = User.objects.get(pk=request.user.id)
			account = Account.objects.get(user=user)
			r = R.r 
			redis_key = 'account.{0}.hash'.format(account.id)
			redis_account = r.hgetall(redis_key)

			try:
				account.user_name = request.POST['username']
			except:
				pass
			try:
				account.first_name = request.POST['first_name']
			except:
				pass
			try:
				account.last_name = request.POST['last_name']
			except:
				pass
			try:
				account.phone_number = request.POST['phone_number']
			except:
				pass
			try:
				account.profile_pic = request.POST['profile_pic']
			except:
				pass
			try:
				account.email = request.POST['email']
			except:
				pass
			try:
				account.gender = request.POST['gender']
			except:
				pass
			try:
				account.birthday = request.POST['birthday']
			except:
				pass
			try:
				account.home_town = request.POST['home_town']
			except:
				pass
			try:
				account.is_active = request.POST['is_active']
			except:
				pass
			account.save()

			pushToNOSQLHash(redis_key, model_to_dict(account))

			rtn_dict['success'] = True
			rtn_dict['msg'] = 'successfully updated user {0}'.format(account)
		except Exception as e:
			logger.info('Error registering new user: {0}'.format(e))
			rtn_dict['msg'] = 'Error registering new user: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#login_required
def searchUsersByEmail(request):
	rtn_dict = {'success': False, "msg": "", "users": []}
	if request.method == 'POST':
		try:
			r = R.r

			searched_users = []
			search_field = request.POST['search_field']
			users = Account.objects.filter(email__startswith=search_field, is_active=True)
			for user in users:
				searched_users.append(model_to_dict(user))
			rtn_dict['users'] = searched_users

		except Exception as e:
			logger.info('Error searching for useres: {0}'.format(e))
			rtn_dict['msg'] = 'Error searching for useres: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#login_required
def addFriend(request):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'POST':
		try:
			account = Account.objects.get(user=request.user, is_active=True)
			friend = Account.objects.get(pk=request.POST['friend_id'], is_active=True)
			if account.id != friend.id:
				link = AccountLink(account_user=account, friend=friend)
				link.save()

				redis_key = 'account.{0}.friends.set'.format(account.id)
				friend_dict = json.dumps({'id': friend.id, 'pf_pic': friend.profile_pic, 'name': friend.display_name})
				pushToNOSQLSet(redis_key, friend_dict, False,0)

				rtn_dict['success'] = True
				rtn_dict['msg'] = 'successfully added friend {0}'.format(friend.id)
			else:
				print 'Error adding friend: User and friend are the same person'
				logger.info('Error adding friend: User and friend are the same person')
				rtn_dict['msg'] = 'Error adding friend: User and friend are the same person'
		except Exception as e:
			print 'Error searching for useres: {0}'.format(e)
			logger.info('Error searching for useres: {0}'.format(e))
			rtn_dict['msg'] = 'Error adding friend: {0}'.format(e)
	else:
		rtn_dict['msg'] = 'Not POST'
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#login_required
def getFriends(request, user_id):
	rtn_dict = {'success': False, "msg": "", "friends": []}

	try:
		r = R.r
		redis_key = 'account.{0}.friends.set'.format(user_id)
		friends_list = r.zrange(redis_key, 0, 10)

		if not friends_list:
			friends_list = []
			friend_links = AccountLink.objects.select_related('friend').filter(account_user=request.user).order_by('invited_count')
			for link in friend_links:
				if link.friend.is_active:
					friends_list.append(model_to_dict(link.friend))
			rtn_dict['success'] = True
			rtn_dict['msg'] = 'successfully retrieved friend list'
			rtn_dict['friends'] = friends_list

		rtn_dict['friends'] = friends_list
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'successfully retrieved friend list'
	except Exception as e:
		logger.info('Error getting friend list: {0}'.format(e))
		rtn_dict['msg'] = 'Error getting friend list: {0}'.format(e)

	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#login_required
def createGroup(request):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'POST':
		try:
			account = Account.objects.get(user=request.user)
			group = Group(group_creator=account)
			group.name = request.POST['name']
			group.save()
			members = ast.literal_eval(request.POST['members'])
			for member_id in members:
				friend = Account.objects.get(pk=member_id, is_active=True)
				group.members.add(friend)
			group.members.add(account)
			r = R.r
			r_group_key = 'group.{0}.hash'.format(group.id)
			pushToNOSQLHash(r_group_key, model_to_dict(group))

			#add group to groups for members
			for member in group.members.all():
				r_groups_key = 'account.{0}.groups.set'.format(member.id)
				pushToNOSQLSet(r_groups_key, group.id, False, 0)
		except Exception as e:
			print 'Error creating group: {0}'.format(e)
			logger.info('Error creating group: {0}'.format(e))
			rtn_dict['msg'] = 'Error creating group: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#@login_required
def getGroup(request, group_id):
	rtn_dict = {'success': False, "msg": "", "group": ""}
	try:
		r = R.r
		r_group_key = 'group.{0}.hash'.format(group_id)
		group = r.hgetall(r_group_key)
		if not group:
			account = Account.objects.get(user=request.user, is_active=True)
			group = Group.objects.get(pk=group_id)
			group = model_to_dict(group)
		rtn_dict['group'] = group
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'successfully retrieved group {0}'.format(group_id)
	except Exception as e:
		logger.info('Error retrieving group: {0}'.format(e))
		rtn_dict['msg'] = 'Error retrieving group: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#@login_required
def getGroups(request):
	rtn_dict = {'success': False, "msg": "", "groups": []}
	try:
		group_list = []
		account = Account.objects.get(user=request.user)
		r = R.r
		r_groups_key = 'account.{0}.groups.set'.format(account.id)
		r_groups = r.zrange(r_groups_key, 0, 10)

		if not r_groups:
			account = Account.objects.get(user=request.user, is_active=True)
			groups = Group.objects.filter(members__id=account.id)
			for group in groups:
				group_list.append(model_to_dict(group))
		else:
			for group_id in r_groups:
				r_group_key = 'group.{0}.hash'.format(group_id)
				group_list.append(json.dumps(r.hgetall(r_group_key)))

		rtn_dict['groups'] = group_list
		rtn_dict['success'] = True
		rtn_dict['msg'] = 'successfully retrieved groups'
	except Exception as e:
		logger.info('Error retrieving groups: {0}'.format(e))
		rtn_dict['msg'] = 'Error retrieving groups: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#@login_required
def addUsersToGroup(request, group_id):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'POST':
		try:
			creator = Account.objects.get(user=request.user, is_active=True)
			group = Group.objects.get(pk=group_id)

			members_to_add = ast.literal_eval(json.loads(request.POST['new_members']))

			for member_id in members_to_add:
				new_member = Account.objects.get(pk=member_id)
				link = AccountLink.objects.get(account_user=creator, friend=new_member)
				group.members.add(new_member)

			r = R.r
			r_group_key = 'group.{0}.hash'.format(group.id)
			pushToNOSQLHash(r_group_key, model_to_dict(group))

			#add group to groups for members
			for member in group.members.all():
				r_groups_key = 'account.{0}.groups.set'.format(member.id)
				pushToNOSQLSet(r_groups_key, group.id, False, 0)

			rtn_dict['success'] = True
			rtn_dict['msg'] = 'successfully added users to group {0}'.format(group_id)
		except Exception as e:
			print 'Error adding users to group: {0}'.format(e)
			logger.info('Error adding users to group: {0}'.format(e))
			rtn_dict['msg'] = 'Error adding users to group: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def removeUsersFromGroup(request, group_id):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'POST':
		try:
			creator = Account.objects.get(user=request.user, is_active=True)
			group = Group.objects.get(pk=group_id, group_creator=creator)
			members_to_remove = request.POST['members_to_remove']
			for member_id in members_to_remove:
				member_to_remove = Account.objects.get(pk=member_id)
				group.members.remove(new_member)

			'''
				TODO: Write redis code for removing users from group
			'''
			rtn_dict['success'] = True
			rtn_dict['msg'] = 'successfully removed users from group {0}'.format(group_id)
		except Exception as e:
			logger.info('Error removing users from group: {0}'.format(e))
			rtn_dict['msg'] = 'Error removing users from group: {0}'.format(e)
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateGroup(request, group_id):
	rtn_dict = {'success': False, "msg": ""}
	if request.method == 'POST':
		try:
			creator = Account.objects.get(user=request.user, is_active=True)
			group = Group.objects.get(pk=group_id, group_creator=creator)
			group.name = request.POST['new_name']
			group.save()
			r = R.r
			r_group_key = 'group.{0}.hash'.format(group_id)
			group['name'] = request.POST['new_name']
			pushToNOSQLHash(r_group_key, model_to_dict(group))
			rtn_dict['success'] = True
			rtn_dict['msg'] = 'successfully edited group {0}'.format(group_id)
		except Exception as e:
			logger.info('Error retrieving groups: {0}'.format(e))
			rtn_dict['msg'] = 'Error retrieving groups: {0}'.format(e)
	else:
		rtn_dict['msg'] = 'Not POST'
	return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def updateAccount(request):
	pass


def syncUserFacebook(request):
    pass
