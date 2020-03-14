from django.contrib.auth import get_user_model
from django.db import models
from django.conf import settings


User = get_user_model()


class Contact(models.Model):
    user = models.ForeignKey(User, related_name='friends', on_delete=models.CASCADE)
    friends = models.ManyToManyField('self', blank=True)
    status = models.BooleanField(default=False)

    def __str__(self):
        return self.user.username


class Message(models.Model):
    contact = models.ForeignKey(Contact, related_name='messages', on_delete=models.CASCADE)
    content = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.contact.user.username


class Chat(models.Model):
    participants = models.ManyToManyField(Contact, related_name='chats')
    messages = models.ManyToManyField(Message, blank=True)
    chat_name = models.CharField(max_length=30, blank=True)

    def __str__(self):
        return "{}".format(self.pk)


class ChatCreator(models.Model):
    creator = models.ForeignKey(User, related_name='creator', on_delete=models.CASCADE, blank=True, null=True)
    related_chats = models.ManyToManyField(Chat, blank=True)

    def __str__(self):
        return self.creator.username


class FriendRequest(models.Model):
    from_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='from_user', on_delete=models.CASCADE)
    to_user = models.ForeignKey(settings.AUTH_USER_MODEL, related_name='to_user', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True) # set when created 

    def __str__(self):
        return "From {}, to {}".format(self.from_user.username, self.to_user.username)