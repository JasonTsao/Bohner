from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("accounts.views",
                        url(r"^create_user", "createUser"),
                        url(r"^update_user", "updateUser"),
                        )

urlpatterns += patterns("accounts.api",
                        # manual refreshing/updating of campaign backend data
                        url(r"^register$", "registerUser"),
                        url(r"^update$", "updateUser"),
                        url(r"^search/email", "searchUsersByEmail"),
                        url(r"^friends/new", "addFriend"),
                        url(r"^friends/list", "getFriends"),
                        )