from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("accounts.views",
                        url(r"^create_user", "createUser"),
                        url(r"^update_user", "updateUser"),
                        )