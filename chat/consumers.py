from django.contrib.auth import get_user_model
from asgiref.sync import async_to_sync
from channels.generic.websocket import WebsocketConsumer
import json
from .models import Message, Chat, Contact
import requests
from django.shortcuts import get_object_or_404
from .serializers import ChatSerializer
import chat.views
from django.contrib.auth.models import User
from django.template.loader import render_to_string

User = get_user_model()


class ChatConsumer(WebsocketConsumer):

    def update_user_status(self, user,status):
        return Contact.objects.filter(user_id=user.pk).update(status=status)
    
    def connect(self):
        self.room_name = self.scope['url_route']['kwargs']['room_name']
        self.room_group_name = 'chat_%s' % self.room_name
        async_to_sync(self.channel_layer.group_add)(
            self.room_group_name,
            self.channel_name
        )
        self.accept()
        user = self.scope['user']
        if user.is_authenticated:
            self.update_user_status(user,True)
            self.send_status()  

    def disconnect(self, close_code):
        async_to_sync(self.channel_layer.group_discard)(
            self.room_group_name,
            self.channel_name
        )
        user = self.scope['user']
        self.update_user_status(user,False)
        self.send_status()  

    def receive(self, text_data):
        data = json.loads(text_data)
        self.commands[data['command']](self, data)

    # Custom functions
    def fetch_messages(self, data):
        messages = chat.views.get_last_10_messages(chatId=data['chatId'], username=data['username'])
        content = {
            'command': 'messages',
            'messages': self.messages_to_json(messages),
        }
        self.send_message(content)

    def new_message(self, data):
        user_contact = chat.views.get_user_contact(data['from'])
        message = Message.objects.create(
            contact=user_contact, 
            content=data['message'])
        current_chat = chat.views.get_current_chat(data['chatId'])
        current_chat.messages.add(message)
        current_chat.save()
        content = {
            'command': 'new_message',
            'message': self.message_to_json(message),
        }
        return self.send_chat_message(content)

    def messages_to_json(self, messages):
        result = []
        for message in messages:
            result.append(self.message_to_json(message))
        result.reverse()
        return result

    def message_to_json(self, message):
        return {
            'id': message.id,
            'author': message.contact.user.username,
            'content': message.content,
            'timestamp': str(message.timestamp)
        }

    commands = {
        'fetch_messages': fetch_messages,
        'new_message': new_message,
    }

    def send_chat_message(self, message):    
        async_to_sync(self.channel_layer.group_send)(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message
            }
        )

    def send_message(self, message):
        self.send(text_data=json.dumps(message))

    def chat_message(self, event):
        message = event['message']
        self.send(text_data=json.dumps(message))

    def send_status(self):
        users = User.objects.all()
        users1 = render_to_string("chat/profile.html",{'users':users})
        async_to_sync(self.channel_layer.group_send)(
            'users',
            {
                "type": "user_update",
                "event": "Change Status",
                "user": users1
            }
        )

    def user_update(self,event):
        self.send_json(event)