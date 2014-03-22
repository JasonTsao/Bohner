from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("events.api",
                        url(r"^events", "UpcomingEvents"),
                        url(r"^create", "createEvent"),
                        url(r"^update/(\d+)", "updateEvent"),
                        url(r"^select_attending", "selectAttending")
                        )

urlpatterns += patterns("events.views",
                        # manual refreshing/updating of campaign backend data
                        url(r"^view/create", "createEvent"),
                        )