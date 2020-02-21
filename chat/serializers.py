from rest_framework import serializers
from chat.models import Chat
from chat import views


class ContactSerializer(serializers.StringRelatedField):
	def to_inter_value_method(self, value):
		return value


class ChatSerializer(serializers.ModelSerializer):

	class Meta:
		model = Chat
		fields = ('id', 'messages', 'participants')

	def create(self, validated_data):
		participants = validated_data.pop('participants')
		chat = Chat()
		chat.save()
		for username in participants:
			contact = views.get_user_contact(username)
			chat.participants.add(contact)
		chat.save()
		return chat