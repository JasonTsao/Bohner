from django.conf.urls import url, patterns
from django.contrib.auth.decorators import login_required

urlpatterns = patterns("accounts.views",
                        url(r"^create_user", "createUser"),
                        url(r"^update_user", "updateUser"),
                        url(r"^search_by_email", "searchByEmail"),
                        url(r"^add_friend", "addFriend"),
                        url(r"^create_group", "createGroup"),
                        url(r"^update_group/(\d+)", "updateGroup"),
                        url(r"^group_add_users/(\d+)", "addUsersToGroup"),
                        )

urlpatterns += patterns("accounts.api",
                        # manual refreshing/updating of campaign backend data
                        url(r"^register$", "registerUser"),
                        url(r"^update$", "updateUser"),
                        url(r"^search/email", "searchUsersByEmail"),
                        url(r"^friends/new", "addFriend"),
                        url(r"^friends/list/(\d+)", "getFriends"),
                        url(r"^group/new", "createGroup"),
                        url(r"^group/list", "getGroups"),
                        url(r"^group/(\d+)/members/add", "addUsersToGroup"),
                        url(r"^group/(\d+)/members/remove", "removeUsersFromGroup"),
                        url(r"^group/(\d+)/update", "updateGroup"),
                        url(r"^group/(\d+)", "getGroup"),
                        )