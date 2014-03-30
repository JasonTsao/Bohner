from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("events.api",
						url(r"^(\d+)", "getEvent"),
                        url(r"^upcoming/(\d+)", "upcomingEvents"),
                        url(r"^new", "createEvent"),
                        url(r"^update/(\d+)", "updateEvent"),
                        url(r"^attending/(\d+)", "selectAttending"),
                        url(r"^invited_friends/(\d+)", "getInvitedFriends"),
                        url(r"^invite_friends/(\d+)", "inviteFriends"),
                        url(r"^comments/new/(\d+)", "createEventComment"),
                        url(r"^comments/(\d+)", "getEventComments"),
                        
                        )

urlpatterns += patterns("events.views",
                        # manual refreshing/updating of campaign backend data
                        url(r"^view/create", "createEvent"),
                        url(r"^events/invite", "inviteFriends"),
                        url(r"^events/new_comment", "createEventComment"),
                        url(r"^events/update/(\d+)", "updateEvent"),
                        url(r"^events/select_attending/(\d+)", "selectAttending"),
                        )