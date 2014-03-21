from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("events.views",
                        url(r"^events", "UpcomingEvents"),
                        url(r"^create", "createEvent"),
                        url(r"^update/(\d+)", "updateEvent"),
                        )