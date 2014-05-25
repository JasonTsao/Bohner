import json
import logging
import pickle
import simplejson
import ast
import datetime
import time
import oauth2
import urllib
import urllib2
from PythonServer.settings import RETURN_LIST_SIZE
from django.http import HttpResponse, HttpResponseRedirect
from django.template import loader, Context, RequestContext
from django.contrib.auth.decorators import login_required
from django.db.models import Max
from django.forms.models import model_to_dict
from django.core.serializers.json import DjangoJSONEncoder
from django.contrib.auth.models import User
from ios_notifications.models import APNService, Notification, Device
from accounts.models import Account, AccountLink, Group, UserLocation, FacebookProfile
from accounts.api import pushToNOSQLSet, pushToNOSQLHash
from notifications.api import sendNotification, createNotification
from models import Event, EventComment, EventNotification, InvitedFriend
from django.views.decorators.csrf import csrf_exempt
from rediscli import r as R

logger = logging.getLogger("django.request")

consumer_key =                  'wsO2jmBIAYgsv1eRvVADng'
consumer_secret =               'tfBAJVkvHgfGM-A6wvuJiTZFCQc'
TOKEN =                         'DaaEHcwUsuO_vQuokMk8f6mm1RInbd52'
token_secret =                  '1RhTKjKP7sta5B_bP8CdCpOCPcI'


def yelpRequest(host, path, url_params, consumer_key, consumer_secret, token, token_secret):
    """Returns response for API request."""
     # Unsigned URL
    encoded_params = ''
    if url_params:
        encoded_params = urllib.urlencode(url_params)

    url = 'http://%s%s?%s' % (host, path, encoded_params)

    # Sign the URL
    consumer = oauth2.Consumer(consumer_key, consumer_secret)
    oauth_request = oauth2.Request('GET', url, {})
    oauth_request.update({'oauth_nonce': oauth2.generate_nonce(),
                            'oauth_timestamp': oauth2.generate_timestamp(),
                            'oauth_token': token,
                            'oauth_consumer_key': consumer_key})

    token = oauth2.Token(token, token_secret)
    oauth_request.sign_request(oauth2.SignatureMethod_HMAC_SHA1(), consumer, token)
    signed_url = oauth_request.to_url()
    # Connect
    try:
        conn = urllib2.urlopen(signed_url, None)
        try:
            response = json.loads(conn.read())
        finally:
            conn.close()
    except urllib2.HTTPError, error:
        response = {"error": error}
        return response

    json_response = json.dumps(response, sort_keys=True, indent=2)
    return json_response


#YELP API STUFF
def yelpSearch(term,location,user):
    rtn_dict = {'success': False, "msg": ""}
    country_code = 'US'
    lang = 'en'
    location_array = location.split(',')
    host = 'api.yelp.com'
    path = '/v2/search'
    url_params = {}
    url_params['term'] = term
    url_params['limit'] = 5
    location = ""
    if location != "":
        url_params['location'] = location
    try:
        user_location = UserLocation.objects.filter(account__user=user).order_by("-created")
        last_location = user_location[0]
        coordinates = "{0},{1}".format(last_location.latitude, last_location.longitude)
        if location == "":
            url_params['ll'] = coordinates
        else:
            url_params['cll'] = coordinates
    except Exception, e:
        print e

    # run yelp search
    search_results = json.loads(yelpRequest(host, path,url_params, consumer_key, consumer_secret, TOKEN, token_secret))
    #print 'search results'
    #print search_results['businesses']
    loc_address = ""
    try:
        for address_segment in search_results['businesses'][0]['location']['display_address']:
            loc_address += str(address_segment) + " "
    except Exception as e:
        print e
    list_results = []
    result_dict = {}
    business_id = ''
    first_loop = True

    for business in search_results['businesses']:
        if first_loop:
            business_id = business['id']
            first_loop = False
        if business['location']['address'][0] == location_array[0]:
            business_id = business['id']
            break

    path = '/v2/business/{0}'.format(business_id)
    url_params = {}
    url_params['cc'] = country_code
    url_params['lang'] = lang
    business_results = json.loads(yelpRequest(host, path,url_params, consumer_key, consumer_secret, TOKEN, token_secret))
    rtn_dict['yelp_object'] = business_results
    rtn_dict['success'] = True
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def searchYelp(term,user,location=""):
    rtn_dict = {'success': False, "msg": ""}
    country_code = 'US'
    lang = 'en'
    location_array = location.split(',')
    host = 'api.yelp.com'
    path = '/v2/search'
    url_params = {}
    url_params['term'] = term
    url_params['limit'] = 1
    location = ""
    if location != "":
        url_params['location'] = location
    try:
        user_location = UserLocation.objects.filter(account__user=user).order_by("-created")
        last_location = user_location[0]
        coordinates = "{0},{1}".format(last_location.latitude, last_location.longitude)
        if location == "":
            url_params['ll'] = coordinates
        else:
            url_params['cll'] = coordinates
    except Exception, e:
        print e
    search_results = json.loads(yelpRequest(host, path,url_params, consumer_key, consumer_secret, TOKEN, token_secret))
    loc_address = ""
    yelp_mobile_url = None
    yelp_img_url = None
    try:
        yelp_mobile_url = search_results["businesses"][0]["mobile_url"]
        for address_segment in search_results['businesses'][0]['location']['display_address']:
            loc_address += str(address_segment) + " "
        yelp_img_url = search_results["businesses"][0]["image_url"]
    except Exception as e:
        print e
    return loc_address, yelp_mobile_url, yelp_img_url



def yelpConnect(request):
    term = 'White House'
    location = '901 S Vermont Ave, Los Angeles, CA 90006'
    user = request.user
    if request.method == 'POST':
        term = request.POST['term']
        location = request.POST['location']
    return yelpSearch(term, location, user)


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


#login_required
@csrf_exempt
def getEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    try:
        if not request.user.id:
            user_id = request.POST['user']
        else:
            user_id = request.user.id
        account = Account.objects.get(user__id=user_id)
        event = Event.objects.get(pk=event_id)
        is_authorized = checkIfAuthorized(event, account)
        if is_authorized:
            r = R.r
            redis_event_key = 'event.{0}.hash'.format(event_id)
            redis_event = r.hgetall(redis_event_key)
            redis_invited_friends_key = 'event.{0}.invited_friends.set'.format(event_id)
            redis_invited_friends = r.zrange(redis_invited_friends_key, 0, 10)
            redis_event = False
            redis_invited_friends = False
            if not redis_event and not redis_invited_friends:
                invited_friends_list = []
                invited_friends = InvitedFriend.objects.filter(event=event)
                for invited_friend in invited_friends:
                    invited_friends_list.append(model_to_dict(invited_friend))
                rtn_dict['invited_friends'] = invited_friends_list
                rtn_dict['event'] = model_to_dict(event)
            else:
                rtn_dict['invited_friends'] = redis_invited_friends
                rtn_dict['event'] = redis_event
            rtn_dict['success'] = True
            rtn_dict['msg'] = 'successfully got event'
    except Exception as e:
        print e
        logger.info('Error grabbing events {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error grabbing events {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def userInGroup(account_id, group_id):
    user_authorized = None

    group = Group.objects.get(pk=group_id)
    for member in group.members.all():
        if member.id == account_id:
            user_authorized = group
    return user_authorized


@login_required
@csrf_exempt
def groupUpcomingEvents(request, group_id):
    rtn_dict = {'success': False, "msg": ""}


    try:
        upcoming_events = []
        '''
        r = R.r
        event_range_start = int(request.GET.get('range_start', 0))
        upcoming_events_key = 'account.{0}.events.set'.format(account_id)
        upcoming_events = r.zrange(upcoming_events_key, event_range_start, event_range_start + RETURN_LIST_SIZE)
        owned_upcoming_events_key = 'account.{0}.owned_events.set'.format(account_id)
        owned_upcoming_events = r.zrange(owned_upcoming_events_key, event_range_start, event_range_start + RETURN_LIST_SIZE)
        '''
        account_id = Account.objects.values('id').get(user=request.user)['id']

        group = userInGroup(account_id, group_id)
        if group != None:
        #upcoming_events = False
            if not upcoming_events or True:

                events = Event.objects.filter(group=group, cancelled=False)
                for event in events:
                    event_dict = model_to_dict(event)
                    if event.start_time:
                        started = time.mktime(event.start_time.timetuple())
                        event_dict['start_time'] = started
                    if event.end_time:
                        ended = time.mktime(event.end_time.timetuple())
                        event_dict['end_time'] = ended
                    upcoming_events.append(event_dict)
                    created = time.mktime(event.created.timetuple())
                    event_dict['created'] = created

            sorted_upcoming_events = sorted(upcoming_events, key=lambda k: k['created']) 
            rtn_dict['upcoming_events'] = sorted_upcoming_events
            #rtn_dict['owned_upcoming_events'] = owned_upcoming_events
            rtn_dict['success'] = True
            rtn_dict['message'] = 'Successfully retrieved upcoming events'
        else:
            rtn_dict['msg'] = 'User is not authorized to view groups upcoming events'
    except Exception as e:
        print 'Error grabbing group upcoming events: {0}'.format(e)
        logger.info('Error grabbing group upcoming events: {0}'.format(e))
        rtn_dict['msg'] = 'Error grabbing group upcoming events: {0}'.format(e)


    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def upcomingEvents(request):
    rtn_dict = {'success': False, "msg": ""}
    try:
        upcoming_events = []
        '''
        r = R.r
        event_range_start = int(request.GET.get('range_start', 0))
        upcoming_events_key = 'account.{0}.events.set'.format(account_id)
        upcoming_events = r.zrange(upcoming_events_key, event_range_start, event_range_start + RETURN_LIST_SIZE)
        owned_upcoming_events_key = 'account.{0}.owned_events.set'.format(account_id)
        owned_upcoming_events = r.zrange(owned_upcoming_events_key, event_range_start, event_range_start + RETURN_LIST_SIZE)
        '''

        account_id = Account.objects.values('id').get(user=request.user)['id']

        owned_upcoming_events = False
        if not owned_upcoming_events:
            #owned_upcoming_events = []
            owned_events = Event.objects.filter(creator=account_id, event_over=False, cancelled=False).order_by('start_time')
            for event in owned_events:
                #owned_upcoming_events.append(model_to_dict(event))
                event_dict = model_to_dict(event)
                if event.start_time:
                    started = time.mktime(event.start_time.timetuple())
                    event_dict['start_time'] = started
                if event.end_time:
                    ended = time.mktime(event.end_time.timetuple())
                    event_dict['end_time'] = ended
                created = time.mktime(event.created.timetuple())
                event_dict['created'] = created
                upcoming_events.append(event_dict)
                #upcoming_events.append(model_to_dict(event))

        #upcoming_events = False

        if not upcoming_events or True:
            invited_users = InvitedFriend.objects.select_related('event').filter(user=account_id)
            for invited_user in invited_users:
                if not invited_user.event.event_over and not invited_user.event.cancelled:
                    if invited_user.event.creator != account_id:
                        event_dict = model_to_dict(invited_user.event)
                        if invited_user.event.start_time:
                            started = time.mktime(invited_user.event.start_time.timetuple())
                            event_dict['start_time'] = started
                        if invited_user.event.end_time:
                            ended = time.mktime(invited_user.event.end_time.timetuple())
                            event_dict['end_time'] = ended
                        created = time.mktime(invited_user.event.created.timetuple())
                        event_dict['created'] = created
                        upcoming_events.append(event_dict)
                        #upcoming_events.append(model_to_dict(invited_user.event))


        sorted_upcoming_events = sorted(upcoming_events, key=lambda k: k['created']) 


        rtn_dict['upcoming_events'] = sorted_upcoming_events
        try:
            last_location = UserLocation.objects.filter(account__user=request.user)
            rtn_dict["lat"] = last_location[0].latitude
            rtn_dict["lng"] = last_location[0].longitude
        except Exception, e:
            raise e
        #rtn_dict['owned_upcoming_events'] = owned_upcoming_events
        rtn_dict['success'] = True
        rtn_dict['message'] = 'Successfully retrieved upcoming events'
    except Exception as e:
        print 'Error grabbing upcoming events: {0}'.format(e)
        logger.info('Error grabbing upcoming events: {0}'.format(e))
        rtn_dict['msg'] = 'Error grabbing upcoming events: {0}'.format(e)


    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def ownedUpcomingEvents(request):
    rtn_dict = {'success': False, "msg": ""}
    try:
        owned_upcoming_events = []
        '''
        r = R.r
        event_range_start = int(request.GET.get('range_start', 0))
        owned_upcoming_events_key = 'account.{0}.owned_events.set'.format(account_id)
        owned_upcoming_events = r.zrange(owned_upcoming_events_key, event_range_start, event_range_start + RETURN_LIST_SIZE)
        '''
        account_id = Account.objects.values('id').get(user=request.user)['id']
        #owned_upcoming_events = False
        if not owned_upcoming_events or True:
            #owned_upcoming_events = []
            owned_events = Event.objects.filter(creator=account_id, event_over=False, cancelled=False).order_by('start_time')
            for event in owned_events:
                #owned_upcoming_events.append(model_to_dict(event)) 
                owned_upcoming_events.append(model_to_dict(event))

        rtn_dict['owned_upcoming_events'] = owned_upcoming_events
        rtn_dict['success'] = True
        rtn_dict['message'] = 'Successfully retrieved upcoming events'
    except Exception as e:
        print 'Error grabbing owned upcoming events: {0}'.format(e)
        logger.info('Error grabbing owned upcoming events: {0}'.format(e))
        rtn_dict['msg'] = 'Error grabbing owned upcoming events: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def createEvent(request):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            logger.info('POST DATA')
            logger.info(request.POST)
            #rtn_dict['post_data'] = request.POST
            '''
            if not request.user.id:
                user_id = request.POST['user']
            else:
                user_id = request.user.id
            user = Account.objects.get(user__id=user_id)
            '''
            user = Account.objects.get(user=request.user)
            event = Event(creator=user)
            event.name = request.POST.get('name', "")
            start_time = request.POST.get('start_time', None)
            group_id = request.POST.get('group_id', None)
            if start_time:
                event.start_time = start_time
            end_time = request.POST.get('end_time', None)
            if end_time:
                event.end_time = end_time
            if group_id:
                group = Group.objects.get(pk=group_id)
                event.group = group

            event.description = request.POST.get('description', None)
            event.meetup_spot = request.POST.get('meetup_spot','In Front')
            event.location_name = request.POST.get('location_name', None)
            event.location_address = request.POST.get('location_address', None)
            # event.location_coordinates = request.POST.get('location_coordinates', None)
            event.friends_can_invite = request.POST.get('friends_can_invite', False) # not saving nullboolean fields correctly 
            event.private = request.POST.get('private', False)
            event.save()

            rtn_dict["location_name"] = event.location_name
            address = ""
            yelp_url = None
            if event.location_name is not None:
                address, yelp_url, yelp_image_url = searchYelp(event.location_name,request.user)
                if address != "" and yelp_url is not None:
                    event.location_address = address
                    event.yelp_url = yelp_url
                    if yelp_image_url is not None:
                        event.yelp_img_url = yelp_image_url
                    addrss, lat, lng = reconcileAddressToCoordinates(address)
                    if addrss is not None and lat is not None and lng is not None:
                        event.location_address = str(addrss)
                        event.location_latitude = float(lat)
                        event.location_longitude = float(lng)
                        event.save()


            event_dict = model_to_dict(event)
            event_dict['start_time'] = str(event.start_time)
            event_dict['end_time'] = str(event.end_time)
            rtn_dict['event'] = event_dict

            rtn_dict['success'] = True
            rtn_dict['msg'] = 'Successfully created new user event!'
            '''
            r = R.r
            redis_key = 'event.{0}.hash'.format(event.id)
            r.hmset(redis_key, model_to_dict(event))

            created_events_key = 'account.{0}.owned_events.set'.format(user.id)
            event_dict = {'event_id': event.id, 'event_name': event.name, 'event_description': event.description, 'start_time': str(event.start_time)}
            event_dict = json.dumps(event_dict)
            # will probably have to change when we decide how time data will come int
            #score = int(time.mktime(time.strptime(event.start_time, "%Y-%m-%d"))) if event.start_time else int(event.created.strftime("%s"))
            score = int(time.mktime(time.strptime(event.start_time, "%Y-%m-%d"))) if event.start_time else int(event.created.strftime("%s"))
            pushToNOSQLSet(created_events_key, event_dict, False,score)
            '''
            # Created Invited Friend object for the host, set is_creator field to true
            try:
                host_invite = InvitedFriend(event=event, user=user, can_invite_friends=True, is_host=True)
                host_invite.attending = True
                host_invite.save()
            except Exception, e:
                print e
            try:
                invited_friends = request.POST['invited_friends']
                invited_friends = json.loads(invited_friends)
                return_invited_friends = []
                for user_dict in invited_friends:
                    try:
                        # save user link to event
                        user_id = user_dict['user_id']
                        try:
                            can_invite_friends = json.loads(user_dict['can_invite_friends']);
                        except:
                            can_invite_friends = user_dict['can_invite_friends']
                        friend = Account.objects.get(pk=user_id)

                        #check to see if the invited_friend is a real friend
                        account_link = AccountLink.objects.get(account_user=user, friend=friend) 
                        invited_friend = InvitedFriend(event=event, user=friend, can_invite_friends=can_invite_friends)
                        invited_friend.save()

                        invited_friend_dict = {}
                        return_invited_friends.append(model_to_dict(invited_friend))

                        account_link.invited_count += 1
                        account_link.save()
                        '''
                        redis_friend_key = 'event.{0}.invited_friends.set'.format(event.id)
                        invited_friend_dict = json.dumps({
                                                'invited_friend_id': invited_friend.id,
                                                'friend_id':friend.id,
                                                'pf_pic': friend.profile_pic,
                                                'name': friend.display_name,
                                                "attending": False})
                        pushToNOSQLSet(redis_friend_key, invited_friend_dict, False, account_link.invited_count)
                        redis_user_events_key = 'account.{0}.events.set'.format(friend.id)
                        event_dict = json.dumps({'event_id': event.id, 
                                        'event_desription': event.description,
                                        'event_name': event.name,
                                        'start_time': str(event.start_time)})
                        pushToNOSQLSet(redis_user_events_key, event_dict, False, score)
                        '''
                        rtn_dict['success'] = True
                        rtn_dict['msg'] = 'Successfully created new user event!'
                    except Exception as e:
                        logger.info('Error adding user {0}: {1}'.format(user,e))
                        rtn_dict['success'] = False
                        rtn_dict['msg'] = e

                rtn_dict['invited_friends'] = return_invited_friends       

            except Exception as e:
                logger.info('Error inviting friends: {0}'.format(e))
                rtn_dict['msg'] = e
                rtn_dict['success'] = False

        except Exception as e:
            print 'Error creating new event: {0}'.format(e)
            logger.info('Error creating new event: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating new event: {0}'.format(e)
            #rtn_dict['post'] = request.POST

    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def getInvitedFriends(request, event_id):
    '''
        NEEDS AUTHENTICATION TO CHECK REQUEST USER IS ALLOWED TO GET ACCESSTO THIS INFORMATION
    '''
    rtn_dict = {'success': False, "msg": "", "invited_friends": []}
    try:
        friend_range_start = int(request.GET.get('range_start', 0))
        '''
        r = R.r
        r_invited_friends_key = 'event.{0}.invited_friends.set'.format(event_id)
        invited_friends = r.zrange(r_invited_friends_key, friend_range_start, friend_range_start + RETURN_LIST_SIZE)
        '''
        invited_friends = False;
        if not invited_friends:
            invited_friends = []
            invited_friends_list = InvitedFriend.objects.select_related('user').filter(event=event_id)
            for invited_friend in invited_friends_list:
                facebook_pf_pic_url = ''
                try:
                    facebook_profile = FacebookProfile.objects.get(user=invited_friend.user)
                    facebook_pf_pic_url = facebook_profile.image_url
                except:
                    pass
                invited_friend_dict = json.dumps({
                            'invited_friend_id': invited_friend.id,
                            'friend_id':invited_friend.user.id,
                            'pf_pic': str(invited_friend.user.profile_pic),
                            'name': invited_friend.user.user_name,
                            "attending": invited_friend.attending,
                            'has_viewed_event': invited_friend.has_viewed_event,
                            'fb_profile_pic': facebook_pf_pic_url})
                invited_friends.append(invited_friend_dict)
        rtn_dict['success'] = True
        rtn_dict['msg'] = "successfully got list of invited friends for event {0}".format(event_id)
        rtn_dict['invited_friends'] = invited_friends
    except Exception as e:
        print 'Error getting invited friends for event {0}: {1}'.format(event_id, e)
        logger.info('Error getting invited friends for event {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error getting invited friends for event {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def getInvitedFriendsWithLocation(request, event_id):
    rtn_dict = {"success": False, "msg": "", "invited":[]}
    try:
        invited_friends = InvitedFriend.objects.filter(event=event_id)
        people = []
        for invitee in invited_friends:
            try:
                invitee_data = {}
                try:
                    facebook_profile = FacebookProfile.objects.get(user=invitee.user)
                except Exception as e:
                    facebook_profile = None
                last_location = UserLocation.objects.filter(account=invitee.user).order_by("-created")
                if last_location.count() > 0:
                    invitee_data["lng"] = last_location[0].longitude
                    invitee_data["lat"] = last_location[0].latitude
                invitee_data["name"] = invitee.user.user_name
                if facebook_profile is not None:
                    invitee_data["picture"] = facebook_profile.image_url
                people.append(invitee_data)
            except Exception, e:
                print e
        rtn_dict["invited"] = people
        rtn_dict["success"] = True
    except Exception, e:
        print e
        rtn_dict["msg"] = "Error getting friend list with location :: {}".format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def addRemoveFriends(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    is_authorized = False
    if request.method == 'POST':
        try:
            #invited_friends = ast.literal_eval(json.loads(request.POST['invited_friends']))
            #removed_friends = ast.literal_eval(json.loads(request.POST['removed_friends']))
            invited_friends = json.loads(request.POST['invited_friends'])
            removed_friends = json.loads(request.POST['removed_friends'])
            event = Event.objects.get(pk=event_id)

            '''
            if not request.user.id:
                user_id = request.POST['user']
            else:
                user_id = request.user.id
            '''
            # check to see if this use is allowed to invite more friends to event
            try:
                #account = Account.objects.get(user__id=user_id)
                account = Account.objects.get(user=request.user)
                if event.creator == account:
                    is_authorized = True

                if not is_authorized:
                    try:
                        invited_friend = InvitedFriend.objects.get(event=Event, user=account)
                        if inivited_friend.can_invite_friends:
                            is_authorized = True
                    except:
                        pass
            except:
                pass


            if is_authorized:
                r = R.r
                for user_dict in invited_friends:
                    try:
                        #print user_dict
                        user_id = user_dict['user_id']
                        can_invite_friends = user_dict['can_invite_friends']
                        friend = Account.objects.get(pk=user_id)
                        account_link = AccountLink.objects.get(account_user=account, friend=friend)
                        invited_friend = InvitedFriend(event=event, user=friend, can_invite_friends=can_invite_friends)
                        invited_friend.save()

                        
                        account_link.invited_count += 1
                        account_link.save()
                        #Save to Redis
                        '''
                        redis_key = 'event.{0}.invited_friends.set'.format(event_id)
                        invited_friend_dict = json.dumps({
                                                'invited_friend_id': invited_friend.id,
                                                'friend_id':friend.id,
                                                'pf_pic': friend.profile_pic,
                                                'name': friend.display_name,
                                                "attending": False})
                        pushToNOSQLSet(redis_key, invited_friend_dict, False, account_link.invited_count)
                        redis_user_events_key = 'account.{0}.events.set'.format(friend.id)
                        event_dict = json.dumps({
                                        'event_id': event.id,
                                        'event_description': event.description,
                                        'event_name': event.name,
                                        'start_time': str(event.start_time)})
                        pushToNOSQLSet(redis_user_events_key, event_dict, False, 0)
                        '''
                        rtn_dict['success'] = True
                        rtn_dict['msg'] = 'Successfully added users'
                    except Exception as e:
                        #print 'Error adding user {0}'.format(e)
                        logger.info('Error adding user {0}'.format(e))
                        rtn_dict['msg'] = 'Error adding user {0}'.format(e)

                for user_dict in removed_friends:
                    try: 
                        user_id = user_dict['user_id']
                        friend = Account.objects.get(pk=user_id)

                        invited_friend = InvitedFriend.objects.get(event=event, user=friend)
                        #invited_friend.save()
                        invited_friend.delete()

                        rtn_dict['success'] = True
                        rtn_dict['msg'] = 'Successfully added users'
                    except Exception as e:
                        #print 'Error adding user {0}'.format(e)
                        logger.info('Error removing user {0}'.format(e))
                        rtn_dict['msg'] = 'Error removing user {0}'.format(e)
                
            else:
                rtn_dict['msg'] = 'user is not authorized to invite other friends'
        except Exception as e:
            print 'Error inviting friends: {0}'.format(e)
            logger.info('Error inviting friends: {0}'.format(e))
            rtn_dict['msg'] = 'Error inviting friends: {0}'.format(e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def removeSelfFromEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        account = Account.objects.get(user=request.user)
        event = Event.objects.get(pk=event_id)
        invited_friend = InvitedFriend.objects.get(event=event, user=account)
        invited_friend.delete()
    except Exception as e:
        logger.info('Error updating event {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error updating event {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")



@login_required
@csrf_exempt
def updateEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        event = Event.objects.get(pk=event_id)
        '''
        r = R.r
        redis_key = 'event.{0}.hash'.format(event_id)
        '''
        try:
            event.name = request.POST['name']
        except:
            pass
        try:
            event.start_time = request.POST['start_time']
        except:
            rtn_dict['saving_start_time'] = 'start time saving failed'
        try:
            event.end_time = request.POST['end_time']
        except:
            pass
        try:
            event.description = request.POST['description']
        except:
            pass
        try:
            event.location_name = request.POST['meetup_spot']
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
        """
        try:
            event.location_coordinates = request.POST['location_coordinates']
        except:
            pass
        """
        try:
            event.friends_can_invite = request.POST['friends_can_invite']
        except:
            pass

        '''
        try:
            invited_friends = InvitedFriend.objects.filter(event=event)
            event.save(invited_friends=invited_friends)
        except:
            event.save()
        '''
        event.save()
        #pushToNOSQLHash(redis_key, model_to_dict(event))
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'Successfully updated event!'
    except Exception as e:
        logger.info('Error updating event {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error updating event {0}: {1}'.format(event_id, e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@csrf_exempt
def updateEventCreatorLocation(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
        try:
            event = Event.objects.get(pk=event_id)
            location = EventCreatorLocation(event=event)
            location.latitude = request.POST['latitude']
            location.longitude = request.POST['longitude']
            location.coordinates = request.POST['coordinates']
            location.save()
        except Exception as e:
            logger.info('Error updating event creator location for event {0}: {1}'.format(event_id, e))
            rtn_dict['msg'] = 'Error updating event creator location for event {0}: {1}'.format(event_id, e)
    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def getEventCreatorLocation(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        location = EventCreatorLocation.objects.get(event=event_id).latest('id')
        rtn_dict['location'] = location.coordinates
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'successfully pulled event creator location'
    except Exception as e:
        logger.info('Error getting event creator location for event {0}: {1}'.format(event_id, e))
        rtn_dict['msg'] = 'Error getting event creator location for event {0}: {1}'.format(event_id, e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


# TODO
def requestInvitedFriendLocation(request, invited_friend_id):
    rtn_dict = {'success': False, "msg": ""}
    #send notification to invited friend ti request their location 
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@csrf_exempt
def updateInvitedFriendLocation(request, invited_friend_id):
    rtn_dict = {'success': False, "msg": ""}

    if request.method == 'POST':
        try:
            invited_friend = InvitedFriend.objects.get(pk=invited_friend_id)

            invited_friend.latitude = request.POST['latitude']
            invited_friend.longitude = request.POST['longitude']
            invited_friend.coordinates = request.POST['coordinates']
            invited_friend.save()
        except Exception as e:
            logger.info('Error updating invited friend {0} location: {1}'.format(invited_friend_id, e))
            rtn_dict['msg'] = 'Error updating invited friend {0} location: {1}'.format(invited_friend_id, e)
    else:
        rtn_dict['msg'] = 'Not POST'
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def getInvitedFriendLocation(request, invited_friend_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        invited_friend = InvitedFriend.objects.get(pk=invited_friend_id)
        rtn_dict['location'] = invited_friend.coordinates
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'successfully pulled invited friend location'
    except Exception as e:
        logger.info('Error getting event invited friend {0} location: {1}'.format(invited_friend_id, e))
        rtn_dict['msg'] = 'Error getting event invited friend {0} location: {1}'.format(invited_friend_id, e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#@login_required
@csrf_exempt
def selectAttending(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            attending = False
            if not request.user.id:
                user_id = request.POST['user']
            else:
                user_id = request.user.id
            user = Account.objects.get(user__id=user_id)
            event = Event.objects.get(pk=event_id)
            invited_friend = InvitedFriend.objects.get(event=event, user=user)

            if request.POST['attending'] == "true":
                attending = True
                invited_friend.attending = True
            elif request.POST['attending'] == "false":
                attending = False
                invited_friend.attending = False
            invited_friend.save()
            
            r = R.r
            r_key = 'event.{0}.invited_friends.set'.format(event_id)
            r_invited_friends = r.zrange(r_key, 0, 10)
            for r_invited_friend in r_invited_friends:
                invited_friend_dict = json.loads(r_invited_friend)
                #update method has hole in that something breaks while removing old member there will be duplicates
                if invited_friend_dict['friend_id'] == user.id:
                    invited_friend_dict['attending'] = attending
                    invited_friend_dict = json.dumps(invited_friend_dict)
                    pushToNOSQLSet(r_key, invited_friend_dict, r_invited_friend, 0)

        except Exception as e:
            print 'Error selected attending for event {0}: user {1}: {2}'.format(event.id, user.id , e)
            logger.info('Error selected attending for event {0}: user {1}: {2}'.format(event.id, user.id , e))
            rtn_dict['msg'] = 'Error selected attending for event {0}: user {1}: {2}'.format(event.id, user.id , e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def invitedFriendHasViewedEvent(request, event_id):
    rtn_dict = {'success': False, "msg": ""}

    try:
        account = Account.objects.get(user=request.user)
        event = Event.objects.get(pk=event_id)
        invited_friend = InvitedFriend.objects.get(user=account, event=event)
        invited_friend.has_viewed_event = True
        invited_friend.save()
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'Successfully updated invited friend has viewed event to True'
    except Exception as e:
        rtn_dict['msg'] = 'Error marking invited viewer as has viewed event: {0}'.format(e)

    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def createEventChatMessage(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    if request.method == 'POST':
        try:
            account = Account.objects.get(user=request.user)
            event = Event.objects.get(pk=event_id)
            is_authorized = checkIfAuthorized(event, account)
            if is_authorized:
                #creating event in SQL DB
                new_comment = EventComment(event=event,user=account)
                new_comment.description = request.POST['message']
                new_comment.save()
                # creating comment in redis
                '''
                r = R.r
                redis_key = 'event.{0}.comments.set'.format(event_id)
                new_comment_dict = model_to_dict(new_comment)
                comment_dict = json.dumps(new_comment_dict)
                score = int(new_comment.created.strftime("%s"))
                pushToNOSQLSet(redis_key, comment_dict, False, score)
                '''

                try:
                    message = "{0} said: {1}".format(account.user_name, new_comment.description)
                    print 'about to try to push message: {0}'.format(message)
                    custom_payload = None
                    notification = createNotification(message, custom_payload)
                    invited_friends = InvitedFriend.objects.select_related('user').filter(event=event)
                    device_tokens = []
                    for invited_friend in invited_friends:
                        try:
                            friend_account = invited_friend.user
                            device = Device.objects.get(users__pk=friend_account.user.id)
                            device_tokens.append(device.token)
                        except:
                            pass
                    sendNotification(notification, device_tokens)
                except Exception as e:
                    print 'Error sending push notification: {0}'.format(e)

                rtn_dict['success'] = True
                rtn_dict['chat_created'] = True
                rtn_dict['msg'] = 'successfully created comment for event {0}'.format(event_id)
            else:
                logger.info('user not authorized to create event comments')
                rtn_dict['msg'] = 'user not authorized to create event comments'
                rtn_dict['chat_created'] = False
        except Exception as e:
            logger.info('Error creating event comment: {0}'.format(e))
            rtn_dict['msg'] = 'Error creating event comment: {0}'.format(e)
            rtn_dict['chat_created'] = False
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


@login_required
@csrf_exempt
def createTestEventChatMessage(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        account = Account.objects.get(user=request.user)
        event = Event.objects.get(pk=event_id)
        try:
            message = "{0} said: {1}".format(account.user_name, "This is a test chat messagee")
            custom_payload = None
            notification = createNotification(message, custom_payload)
            invited_friends = InvitedFriend.objects.select_related('user').filter(event=event)
            device_tokens = []
            for invited_friend in invited_friends:
                try:
                    friend_account = invited_friend.user
                    device = Device.objects.get(users__pk=friend_account.user.id)
                    device_tokens.append(device.token)
                except:
                    pass
            sendNotification(notification, device_tokens)
        except Exception as e:
            print 'Error sending push notification: {0}'.format(e)

        rtn_dict['success'] = True
        rtn_dict['chat_created'] = True
        rtn_dict['msg'] = 'successfully created comment for event {0}'.format(event_id)

    except Exception as e:
        logger.info('Error creating event comment: {0}'.format(e))
        rtn_dict['msg'] = 'Error creating event comment: {0}'.format(e)
        rtn_dict['chat_created'] = False
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


#@login_required
@login_required
@csrf_exempt
def getEventChatMessages(request, event_id):
    rtn_dict = {'success': False, "msg": ""}
    try:
        '''
        comment_range_start = int(request.GET.get('range_start', 0))
        r = R.r
        redis_key = 'event.{0}.comments.set'.format(event_id)
        comments = r.zrange(redis_key, comment_range_start, comment_range_start + RETURN_LIST_SIZE)
        '''
        comments = False
        if not comments:
            comments = []
            account = Account.objects.get(user=request.user)
            event = Event.objects.get(pk=event_id)
            is_authorized = checkIfAuthorized(event, account)

            event_comments = EventComment.objects.filter(event=event).order_by('created')

            for event_comment in event_comments:
                message_dict = {}
                message_dict['created'] = event_comment.created
                message_dict['creator_name'] = event_comment.user.user_name
                message_dict['creator_id'] = event_comment.user.id
                message_dict['message'] = event_comment.description
                comments.append(message_dict)

        rtn_dict['comments'] = comments
        rtn_dict['success'] = True
        rtn_dict['msg'] = 'successfully retrieved comments for event {0}'.format(event_id)
    except Exception as e:
        logger.info('Error retrieving event comments: {0}'.format(e))
        rtn_dict['msg'] = 'Error retrieving event comments: {0}'.format(e)
    return HttpResponse(json.dumps(rtn_dict, cls=DjangoJSONEncoder), content_type="application/json")


def reconcileAddressToCoordinates(address_string):
    """
        queries google for corresponding coordinates for given address (if address is valid)
    """
    params = {"address":address_string, "sensor":False}
    google_url = "http://maps.google.com/maps/api/geocode/json?%s" % (urllib.urlencode(params))
    logger.info(google_url)
    address = None
    latitude = None
    longitude = None
    try:
        conn = urllib2.urlopen(google_url, None)
        response = json.loads(conn.read())
        address = response["results"][0]["formatted_address"]
        latitude = response["results"][0]["geometry"]["location"]["lat"]
        longitude = response["results"][0]["geometry"]["location"]["lng"]
        print response
    except Exception as e:
        print e
    return address, latitude, longitude