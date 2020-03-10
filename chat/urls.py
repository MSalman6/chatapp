from django.urls import path, re_path

from .views import (
    ChatListView,
    ChatDetailView,
    ChatCreateView,
    ChatUpdateView,
    ChatDeleteView,
    create_chat_view,
    update,
    searching,
    send_friend_request,
    cancel_friend_request,
    accept_friend_request,
    delete_friend_request
)

app_name = 'chat'

urlpatterns = [
    path('', ChatListView.as_view()),
    path('update', update),
    path('searching', searching),
    path('create/', ChatCreateView.as_view(), name='create'),
    path('create_chat_view/', create_chat_view, name='create_chat'),
    path('<pk>', ChatDetailView.as_view()),
    path('<pk>/update/', ChatUpdateView.as_view(), name='update'),
    path('<pk>/delete/', ChatDeleteView.as_view(), name='delete'),
    path('friend-request/send/<int:pk>/', send_friend_request),
    path('friend-request/cancel/<int:pk>/', cancel_friend_request),
    path('friend-request/accept/<int:pk>/', accept_friend_request),
    path('friend-request/delete/<int:pk>/', delete_friend_request),
]
