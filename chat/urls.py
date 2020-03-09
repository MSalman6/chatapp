from django.urls import path, re_path

from .views import (
    ChatListView,
    ChatDetailView,
    ChatCreateView,
    ChatUpdateView,
    ChatDeleteView,
    create_chat_view,
    update,
    searching
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
    path('<pk>/delete/', ChatDeleteView.as_view(), name='delete')
]
