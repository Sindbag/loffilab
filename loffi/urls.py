from django.conf.urls import url
from loffi import views
from django.contrib.auth.views import login, logout

urlpatterns = [
    url(r'^$', views.index, name='main'),

    url(r'^news/$', views.news, name='news'),
    url(r'^news/(?P<article>[0-9a-zA-Z_-]*)/$', views.show_article, name='article'),

    url(r'^accounts/login/$', login, name='login'),
    url(r'^accounts/logout/$', logout, name='logout'),
    url(r'^accounts/register/', views.register, name='register'),
    url(r'^accounts/profile/$', views.account, name='account'),
    url(r'^accounts/', views.account, name='account'),

    url(r'^about/contacts/$', views.contacts, name='contacts'),
    url(r'^about/$', views.about, name='about'),

    url(r'^all/$', views.all_items, name='all_items'),
    url(r'^add_to_cart/$', views.add_to_cart, name='add_to_cart'),
    url(r'^remove_from_cart/$', views.remove_from_cart, name='delete_item'),
    url(r'^add_question/$', views.add_question, name='add_question'),

    url(r'^(?P<link>[0-9a-zA-Z_-]*)/$', views.section, name='section'),
    url(r'^(?P<link>[0-9a-zA-Z_-]*)/(?P<subsection_link>[0-9a-zA-Z_-]*)/$', views.subsection, name='subsection'),
    url(r'^(?P<link>[0-9a-zA-Z_-]*)/(?P<subsection_link>[0-9a-zA-Z_-]*)/(?P<item_link>[0-9a-zA-Z_-]*)/$',
        views.show_item, name='item'),

]
