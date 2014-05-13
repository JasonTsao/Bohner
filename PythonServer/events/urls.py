from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("events.api",
						url(r"^(\d+)", "getEvent"),
                        url(r"^upcoming", "upcomingEvents"),
                        url(r"^owned_upcoming", "ownedUpcomingEvents"),
                        url(r"^group/(\d+)/upcoming", "groupUpcomingEvents"),
                        url(r"^new", "createEvent"),
                        url(r"^update/(\d+)", "updateEvent"),
                        url(r"^remove_self/(\d+)", "removeSelfFromEvent"),
                        url(r"^attending/(\d+)", "selectAttending"),
                        url(r"^invited_friends/(\d+)", "getInvitedFriends"),
                        url(r"^add_remove_friends/(\d+)", "addRemoveFriends"),
                        url(r"^comments/new/(\d+)", "createEventComment"),
                        url(r"^comments/(\d+)", "getEventComments"),
                        url(r"^creator_location/update/(\d+)", "updateEventCreatorLocation"),
                        url(r"^creator_location/(\d+)", "getEventCreatorLocation"),
                        url(r"^invited_friend_location/update/(\d+)", "updateInvitedFriendLocation"),
                        url(r"^invited_friend_location/(\d+)", "getInvitedFriendLocation"),
                        url(r"^request/invited_friend_location/(\d+)", "requestInvitedFriendLocation"),
                        url(r"^yelpConnect","yelpConnect"),
                        )

urlpatterns += patterns("events.views",
                        # manual refreshing/updating of campaign backend data
                        url(r"^view/create", "createEvent"),
                        url(r"^events/invite", "inviteFriends"),
                        url(r"^events/new_comment", "createEventComment"),
                        url(r"^events/update/(\d+)", "updateEvent"),
                        url(r"^events/select_attending/(\d+)", "selectAttending"),
                        url(r"^yelp_search", "yelpSearch"),
                        )