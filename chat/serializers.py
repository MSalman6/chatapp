from rest_framework import serializers
from chat.models import Chat
import chat.views


class ContactSerializer(serializers.StringRelatedField):
	def to_inter_value_method(self, value):
		return value


class ChatSerializer(serializers.ModelSerializer):

	class Meta:
		model = Chat
		fields = ('id', 'messages', 'participants')

	def create(self, validated_data):
		print(validated_data)
		participants = validated_data.pop('participants')
		chat = Chat()
		chat.save
		for username in participants:
			contact = chat.views.get_user_contact(username)
			chat.participants.add(contact)
		chat.save()
		return chat