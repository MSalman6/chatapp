from django.contrib import admin
from .models import Message, Chat, Contact, ChatCreator

admin.site.register(Message)
admin.site.register(Chat)
admin.site.register(Contact)
admin.site.register(ChatCreator)