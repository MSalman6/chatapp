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
    UpdateAPIView,
    UpdateAPIView
)
from chat.models import Chat, Contact, ChatCreator
from .serializers import ChatSerializer
from .consumers import ChatConsumer
from . import forms
from rest_framework.decorators import api_view
from django.http import HttpResponse, JsonResponse, HttpResponseRedirect
from django.shortcuts import redirect
import collections
from rest_framework.response import Response
from django.db.models import Q
from django.forms.models import model_to_dict
from .models import FriendRequest

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
    user = get_object_or_404(User, username=username)
    contact = get_object_or_404(Contact, user=user)
    return contact

def get_current_chat(chatId):
    return get_object_or_404(Chat, id=chatId)

def create_contact(username):
    user = User.objects.get(username=username)
    return Contact.objects.create(user=user)


#Add friend Views

def send_friend_request(request, pk):
    user = get_object_or_404(User, pk=pk)
    frequest, created = FriendRequest.objects.get_or_create(
      from_user=request.user,
      to_user=user)
    url = '/accounts/{}/profile/'.format(pk)
    return HttpResponseRedirect(url)

def cancel_friend_request(request, pk):
    user = get_object_or_404(User, id=pk)
    frequest = FriendRequest.objects.filter(
        from_user=request.user,
        to_user=user).first()
    frequest.delete()
    url = '/accounts/{}/profile/'.format(pk)
    return HttpResponseRedirect(url)

def accept_friend_request(request, pk):
    user1_contact = Contact.objects.filter(pk=request.user.pk).first()
    user2_contact = Contact.objects.filter(pk=pk).first()
    from_user = get_object_or_404(User, pk=pk)
    frequest = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()
    user1 = frequest.to_user
    user2 = from_user
    user1_contact.friends.add(user2_contact)
    frequest.delete()
    url = '/accounts/{}/profile/'.format(request.user.pk)
    return HttpResponseRedirect(url)

def delete_friend_request(request, pk):
    from_user = get_object_or_404(User, id=pk)
    frequest = FriendRequest.objects.filter(from_user=from_user, to_user=request.user).first()
    frequest.delete()
    url = '/accounts/{}/profile/'.format(request.user.pk)
    return HttpResponseRedirect(url)

def remove_friend(request, pk):
    user1 = Contact.objects.filter(pk=request.user.pk).first()
    user2 = User.objects.filter(pk=pk).first()
    user1.friends.remove(user2.pk)
    url = '/accounts/{}/profile/'.format(pk)
    return HttpResponseRedirect(url)

# Views
@api_view(['POST'])
def update(request):
    inp_participants = request.data['participants']
    inp_list = list(inp_participants.split(","))
    participants = []
    for i in range(len(inp_list)):
        user_id = User.objects.get(username=inp_list[i])
        participants.append(user_id.pk)
    chatId = request.data['id']
    print(participants)
    content = {
    'participants': participants
    }
    url = 'http://127.0.0.1:8000/chat/{}/update/'.format(chatId)
    result = requests.put(url, data=content)
    redirect_id = result.json()["id"]
    print(result.json())
    return redirect('/{}'.format(redirect_id))

def profile_view(request, pk):
    p = Contact.objects.filter(user_id=pk).first()
    u = p.user
    sent_friend_requests = FriendRequest.objects.filter(from_user=p.user)
    rec_friend_requests = FriendRequest.objects.filter(to_user=p.user)
    friends = p.friends.all()

    # is this user our friend
    button_status = 'friend'

    if p not in friends:
        button_status = 'not_friend'

        # if we have sent him a friend request
        if len(FriendRequest.objects.filter(
            from_user=request.user).filter(to_user=p.user)) == 1:
                button_status = 'friend_request_sent'

    context = {
        'u': u,
        'button_status': button_status,
        'friends_list': friends,
        'sent_friend_requests': sent_friend_requests,
        'rec_friend_requests': rec_friend_requests
    }

    return render(request, "chat/profile.html", context)


@api_view(['POST'])
def searching(request):
    dictionary = dict() 
    print(request.data)
    inp = request.data['search-input']
    data = User.objects.filter(Q(username__icontains=inp)).values('username', 'pk')
    for i in range(len(data)):
        dictionary[data[i]['pk']] = data[i]['username']
    print(dictionary)
    return JsonResponse(dictionary, safe=False)


@api_view(['POST'])
def create_chat_view(request):
    #check if a chat with same participants already exists
    # if it exists redirect to that chat

    user_name = request.user.username
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
    user_contact = Contact.objects.filter(user_id=request.user.pk).first()
    friends = user_contact.friends.all()
    # for displaying stuff from backend to frontend
    user_name = request.user.username
    user_object = User.objects.filter(username=user_name)

    #Return Chats in which User is a participant as 
    chat = Chat.objects.all()
    user_chats = []
    chat_name = []
    new_list = []
    old_list = []
    names_list = []
    ok_list = []
    for i in range(len(chat)):
        chat_obj = chat[i]
        get_chat_obj = Chat.objects.get(id=str(chat_obj))
        participants = get_chat_obj.participants.order_by('user')
        if user_name in str(participants):
            item = Chat.objects.get(id=str(get_chat_obj))
            user_chats.append(item)
            names = item.participants.order_by('user')
            names_list.append(names)
    for i in range(len(names_list)):
        if len(names_list[i]) == 1:
            chat_name.append(Contact.objects.get(user=user_object[0]))
        elif len(names_list[i]) == 2:
            for j in range(len(names_list[i])):
                if user_name != str(names_list[i][j]):
                    chat_name_list = []
                    chat_name_list.append(names_list[i][j])
                    chat_name.append(chat_name_list[0])
        elif len(names_list[i]) > 2:
            new_list.append([])  
            for k in range(len(names_list[i])):
                new_list[len(new_list)-1].append(names_list[i][k])
                
    for l in range(len(new_list)):
        str1 = ""
        t = new_list[l]
        for i in range(len(new_list[l])):
            str1+=(str(new_list[l][i])+",")
        
        chat_name.append(str1[:-1])
    ###############################################
    form = forms.CreateContactForm()
    return render(request, 'chat/index.html', {
        'friends': friends,
        'username': mark_safe(json.dumps(request.user.username)),
        'users': User.objects.all(),
        'contacts': Contact.objects.all(),
        'form': form,
        'chats' : zip(chat_name,user_chats)
        })

@login_required
def room(request, chatId):
    user_contact = Contact.objects.filter(user_id=request.user.pk).first()
    friends = user_contact.friends.all()
    # for displaying stuff from backend to frontend
    user_name = request.user.username
    user_object = User.objects.filter(username=user_name)

    #Return Chats in which User is a participant as 
    chat = Chat.objects.all()
    user_chats = []
    chat_name = []
    new_list = []
    old_list = []
    names_list = []
    ok_list = []
    for i in range(len(chat)):
        chat_obj = chat[i]
        get_chat_obj = Chat.objects.get(id=str(chat_obj))
        participants = get_chat_obj.participants.order_by('user')
        if user_name in str(participants):
            item = Chat.objects.get(id=str(get_chat_obj))
            user_chats.append(item)
            names = item.participants.order_by('user')
            names_list.append(names)
    for i in range(len(names_list)):
        if len(names_list[i]) == 1:
            chat_name.append(Contact.objects.get(user=user_object[0]))
        elif len(names_list[i]) == 2:
            for j in range(len(names_list[i])):
                if user_name != str(names_list[i][j]):
                    chat_name_list = []
                    chat_name_list.append(names_list[i][j])
                    chat_name.append(chat_name_list[0])
        elif len(names_list[i]) > 2:
            new_list.append([])  
            for k in range(len(names_list[i])):
                new_list[len(new_list)-1].append(names_list[i][k])

    for l in range(len(new_list)):
        str1 = ""
        t = new_list[l]
        for i in range(len(new_list[l])):
            str1+=(str(new_list[l][i])+",")
        
        chat_name.append(str1[:-1])
    ###############################################
    form = forms.CreateContactForm()
    return render(request, 'chat/room.html', {
        'friends': friends,
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
    permission_classes = (permissions.AllowAny, )


class ChatDeleteView(DestroyAPIView):
    queryset = Chat.objects.all()
    serializer_class = ChatSerializer
    permission_classes = (permissions.IsAuthenticated, )