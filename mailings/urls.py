from django.urls import path
from . import views

app_name = 'mailings'

urlpatterns = [
    # Главная страница списка рассылок
    path('', views.MailingListView.as_view(), name='mailing_list'),

    # Рассылки CRUD
    path('create/', views.MailingCreateView.as_view(), name='mailing_create'),
    path('<int:pk>/update/', views.MailingUpdateView.as_view(), name='mailing_update'),
    path('<int:pk>/delete/', views.MailingDeleteView.as_view(), name='mailing_delete'),
    path('<int:pk>/send/', views.MailingSendView.as_view(), name='mailing_send'),

    # Клиенты CRUD
    path('clients/', views.ClientListView.as_view(), name='client_list'),
    path('clients/create/', views.ClientCreateView.as_view(), name='client_create'),
    path('clients/<int:pk>/update/', views.ClientUpdateView.as_view(), name='client_update'),
    path('clients/<int:pk>/delete/', views.ClientDeleteView.as_view(), name='client_delete'),

    # Сообщения CRUD
    path('messages/', views.MessageListView.as_view(), name='message_list'),
    path('messages/create/', views.MessageCreateView.as_view(), name='message_create'),
    path('messages/<int:pk>/update/', views.MessageUpdateView.as_view(), name='message_update'),
    path('messages/<int:pk>/delete/', views.MessageDeleteView.as_view(), name='message_delete'),

    # Статистика
    path('stats/', views.UserStatsView.as_view(), name='stats'),
]
