from django.urls import path
from . import views

app_name = 'mailings'

urlpatterns = [
    path('', views.MailingListView.as_view(), name='mailing_list'),
    path('create/', views.MailingCreateView.as_view(), name='mailing_create'),
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('<int:pk>/send/', views.MailingSendView.as_view(), name='mailing_send'),
    path('stats/', views.UserStatsView.as_view(), name='stats'),
]