from rest_framework import serializers
from .models import Subject, Topic, Test


class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'grade', 'image']


class TopicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Topic
        fields = ['id', 'subject', 'name', 'content']


class TestSerializer(serializers.ModelSerializer):
    class Meta:
        model = Test
        fields = ['id', 'topic', 'type', 'number_of_questions', 'difficulty']


class GenerateTestSerializer(serializers.Serializer):
    number_of_questions = serializers.IntegerField()
    test_type = serializers.ChoiceField(choices=Test.TOPIC_CHOICES)
    difficulty = serializers.ChoiceField(choices=Test.DIFFICULTY_CHOICES)
    topic_id = serializers.IntegerField()


class CheckAnswersSerializer(serializers.Serializer):
    question = serializers.CharField()
    correct = serializers.CharField()
    user = serializers.CharField()


class CheckAnswersResponseSerializer(serializers.Serializer):
    url = serializers.URLField()
