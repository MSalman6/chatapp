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
from chat.models import Chat, Contact, ChatCreator
from .serializers import ChatSerializer
from .consumers import ChatConsumer
from . import forms
from rest_framework.decorators import api_view
from django.http import HttpResponse
from django.shortcuts import redirect
import collections

User = get_user_model()


# Query functions
def get_last_10_messages(chatId, username):
    user = username
    chat = Chat.objects.get(id=chatId)
    participants = chat.participants.order_by('user')
    if user in str(participants):
        chat = get_object_or_404(Chat, id=chatId)
        return chat.messages.order_by('-timestamp').all()[:10]
    else:
        return HttpResponse("You are not allowed to view this conversation.")

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
    #check if a chat with same participants already exists
    # if it exists redirect to that chat

    user_name = request.user.username
    print(request.data)
    inp_participants = request.data['participants']
    all_chats = Chat.objects.all()
    chat_names = []
    for i in range(len(all_chats)):
        chat_obj = all_chats[i]
        get_chat_obj = Chat.objects.get(id=str(chat_obj))
        chat_names.append(get_chat_obj.participants.order_by('user'))
    list1 = list(inp_participants.split(","))
    for j in range(len(chat_names)):
        temp_list = []
        for i, c in enumerate(chat_names[j]):
            temp_list.append(str(c))
        if collections.Counter(list1) == collections.Counter(temp_list):
            return redirect('/{}'.format(all_chats[j]))

    # if it does not exist create a new chat
    if type(inp_participants) == str:
        inp_participants = list(inp_participants.split(","))
    contacts = Contact.objects.all()
    for i in range(len(inp_participants)):
        if inp_participants[i] not in str(contacts):
            create_contact(username=inp_participants[i])
    participants = []
    for x in range(len(inp_participants)):
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
    user_object = User.objects.filter(username=user_name)
    creators = ChatCreator.objects.all()

    if request.user.username in str(creators):
        get_related_chats_object = ChatCreator.objects.get(creator_id=user_object[0].id)
        chat_object = Chat.objects.filter(id=result.json()["id"])
        get_related_chats_object.related_chats.add(chat_object[0].id)
    else:
        ChatCreator.objects.create(creator=user_object[0])
        get_related_chats_object = ChatCreator.objects.get(creator_id=user_object[0].id)
        chat_object = Chat.objects.filter(id=result.json()["id"])
        get_related_chats_object.related_chats.add(chat_object[0].id)
    return redirect('/{}'.format(redirect_id))

@login_required
def index(request):
    # for displaying stuff from backend to frontend
    user_name = request.user.username
    user_object = User.objects.filter(username=user_name)
    creators = ChatCreator.objects.all()
    contact_id = Contact.objects.get(user=user_object[0].id)
    #Return Chats in which User is a participant as 
    chat = Chat.objects.all()
    user_chats = []
    chat_name = []
    new_list = []
    old_list = []
    for i in range(len(chat)):
        chat_obj = chat[i]
        get_chat_obj = Chat.objects.get(id=str(chat_obj))
        participants = get_chat_obj.participants.order_by('user')
        if user_name in str(participants):
            item = Chat.objects.get(id=str(get_chat_obj))
            user_chats.append(item)
            names = item.participants.order_by('user')
            if len(names) == 1:
                chat_name.append(Contact.objects.get(user=user_object[0]))
            elif len(names) == 2:
                for g in range(len(names)):
                    if user_name != str(names[g]):
                        chat_name_list = []
                        chat_name_list.append(names[g])
                        chat_name.append(chat_name_list[0])
            elif len(names) > 2:
                for m in range(len(names)):
                    new_list.append(names[m])
    for k in range(len(new_list)):
        t = new_list[k]
        old_list.append(str(t))
    chat_name.append(old_list)
    ###############################################
    form = forms.CreateContactForm()
    return render(request, 'chat/room.html', {
        'username': mark_safe(json.dumps(request.user.username)),
        'users': User.objects.all(),
        'contacts': Contact.objects.all(),
        'form': form,
        'chats' : zip(chat_name,user_chats)
        })


# TODO: Return Chats in which User is a participant
@login_required
def room(request, chatId):
    # for displaying stuff from backend to frontend
    user_name = request.user.username
    user_object = User.objects.filter(username=user_name)
    creators = ChatCreator.objects.all()
    contact_id = Contact.objects.get(user=user_object[0].id)
    #Return Chats in which User is a participant as 
    chat = Chat.objects.all()
    user_chats = []
    chat_name = []
    new_list = []
    old_list = []
    for i in range(len(chat)):
        chat_obj = chat[i]
        get_chat_obj = Chat.objects.get(id=str(chat_obj))
        participants = get_chat_obj.participants.order_by('user')
        if user_name in str(participants):
            item = Chat.objects.get(id=str(get_chat_obj))
            user_chats.append(item)
            names = item.participants.order_by('user')
            if len(names) == 1:
                chat_name.append(Contact.objects.get(user=user_object[0]))
            elif len(names) == 2:
                for g in range(len(names)):
                    if user_name != str(names[g]):
                        chat_name_list = []
                        chat_name_list.append(names[g])
                        chat_name.append(chat_name_list[0])
            elif len(names) > 2:
                for m in range(len(names)):
                    new_list.append(names[m])
    for k in range(len(new_list)):
        t = new_list[k]
        old_list.append(str(t))
    chat_name.append(old_list)
    ###############################################
    form = forms.CreateContactForm()
    return render(request, 'chat/room.html', {
        'chatId': mark_safe(json.dumps(chatId)),
        'username': mark_safe(json.dumps(request.user.username)),
        'users': User.objects.all(),
        'contacts': Contact.objects.all(),
        'form': form,
        'chats' : zip(chat_name,user_chats)
        })


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