from django.contrib.auth.decorators import login_required
from django.shortcuts import render
from django.utils.safestring import mark_safe
import json
import requests
from django.contrib.auth import get_user_model
from django.shortcuts import get_object_or_404
from rest_framework import permissions
from rest_framework.generics import (
    ListAPIView,
    RetrieveAPIView,
    CreateAPIView,
    DestroyAPIView,
    UpdateAPIView
)
from chat.models import Chat, Contact
from .serializers import ChatSerializer
from .consumers import ChatConsumer
from . import forms
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.shortcuts import redirect

User = get_user_model()


# Query functions
def get_last_10_messages(chatId):
    chat = get_object_or_404(Chat, id=chatId)
    return chat.messages.order_by('-timestamp').all()[:10]

def get_user_contact(username):
    user = get_object_or_404(username=username)
    return get_object_or_404(Contact, user=user)

def get_current_chat(chatId):
    return get_object_or_404(Chat, id=chatId)

def create_contact(username):
    user = User.objects.get(username=username)
    return Contact.objects.create(user=user)

# Views
@api_view(['POST'])
def create_chat_view(request):
    inp_participants = request.data['participants']
    if type(inp_participants) == str:
        inp_participants = list(inp_participants.split(","))
    contacts = Contact.objects.all()
    for i in range(len(inp_participants)):
        if inp_participants[i] in str(contacts):
            pass
        else:
            create_contact(username=inp_participants[i])
    participants = []
    for x in range(len(inp_participants)):
        print(inp_participants[x])
        user_id = User.objects.get(username=inp_participants[x])
        participant = Contact.objects.get(user_id=user_id.pk)
        participants.append(participant.id)
    content = {
    'messages':[],
    'participants':participants
    }
    url = 'http://127.0.0.1:8000/chat/create/'
    result = requests.post(url, data=content)
    redirect_id = result.json()["id"]
    return redirect('/{}'.format(redirect_id))


@login_required
def index(request):
    return render(request, 'chat/index.html', {})

@login_required
def room(request, chatId):
    form = forms.CreateContactForm()
    return render(request, 'chat/room.html', {
        'chatId': mark_safe(json.dumps(chatId)),
        'username': mark_safe(json.dumps(request.user.username)),
        'users': User.objects.all(),
        'contacts': Contact.objects.all(),
        'chats': Chat.objects.all(),
        'form': form
    }) 
    

def get_user_contact(username):
    user = get_object_or_404(User, username=username)
    contact = get_object_or_404(Contact, user=user)
    return contact


class ChatListView(ListAPIView):
    serializer_class = ChatSerializer
    permission_classes = (permissions.AllowAny, )

    def get_queryset(self):
        queryset = Chat.objects.all()
        username = self.request.query_params.get('username', None)
        if username is not None:
            contact = get_user_contact(username)
            queryset = contact.chats.all()
        return queryset


class ChatDetailView(RetrieveAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (permissions.AllowAny, )


class ChatCreateView(CreateAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (permissions.AllowAny, )


class ChatUpdateView(UpdateAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated, )


class ChatDeleteView(DestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated, )