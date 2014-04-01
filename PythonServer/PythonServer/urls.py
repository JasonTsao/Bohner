import settings
from django.conf.urls import patterns, include, url

from django.contrib import admin
admin.autodiscover()
# Uncomment the next two lines to enable the admin:
# from django.contrib import admin
# admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^acct/', include('accounts.urls')),
    url(r'^events/', include('events.urls')),
    url(r'^ios-notifications/', include('ios_notifications.urls')),
    (r'^static/(?P<path>.*)$', 'django.views.static.serve', 
    {'document_root': settings.STATIC_ROOT, 'show_indexes':True}), 
    # Examples:
    # url(r'^$', 'PythonServer.views.home', name='home'),
    # url(r'^PythonServer/', include('PythonServer.foo.urls')),

    # Uncomment the admin/doc line below to enable admin documentation:
    # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    # url(r'^admin/', include(admin.site.urls)),
)
