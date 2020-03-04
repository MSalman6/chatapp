from rest_framework import serializers
from chat.models import Chat
from chat import views
from django.contrib.auth import get_user_model


User = get_user_model()


class ContactSerializer(serializers.StringRelatedField):
	def to_inter_value_method(self, value):
		return value


class ChatSerializer(serializers.ModelSerializer):

	class Meta:
		model = Chat
		fields = ('id', 'messages', 'participants', 'chat_name')

	def create(self, validated_data):
		participants = validated_data.pop('participants')
		chat = Chat()
		chat.save()
		for username in participants:
			contact = views.get_user_contact(username)
			chat.participants.add(contact)
		chat.save()
		return chat

	def update(self, instance, validated_data):
		inp_participants = validated_data['participants']
		chat_participants = instance.participants.order_by('user')
		for i in range(len(inp_participants)):
			if inp_participants[i] not in chat_participants:
				instance.participants.add(inp_participants[i])
		return instance