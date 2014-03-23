from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("events.api",
                        url(r"^events", "upcomingEvents"),
                        url(r"^create", "createEvent"),
                        url(r"^update/(\d+)", "updateEvent"),
                        url(r"^attending/(\d+)", "selectAttending"),
                        url(r"^invite_friends/(\d+)", "inviteFriends"),
                        )

urlpatterns += patterns("events.views",
                        # manual refreshing/updating of campaign backend data
                        url(r"^view/create", "createEvent"),
                        )