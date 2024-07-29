from django.http import JsonResponse
from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_200_OK

from .models import Subject, Topic, Test
from .serializers import SubjectSerializer, TopicSerializer, GenerateTestSerializer

from .utils import client, generate_questions, parse_generated_questions, parse_true_false_questions, \
    parse_short_answer_questions, submit_synthesis, get_synthesis
import logging
import sys
import time

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import CheckAnswersSerializer, CheckAnswersResponseSerializer
from django.http import JsonResponse
from django.core.exceptions import ValidationError

DEPLOYMENT_NAME = 'llama3-8b-8192'


class SubjectsListView(generics.ListAPIView):
    serializer_class = SubjectSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Subject.objects.filter(grade=user.grade)


class TopicsListView(generics.ListAPIView):
    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        subject_id = self.kwargs['subject_id']
        return Topic.objects.filter(subject_id=subject_id)


class GenerateTestsView(generics.GenericAPIView):
    serializer_class = GenerateTestSerializer

    def post(self, request):
        serializer = GenerateTestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.data
        topic_id = data.get('topic_id')
        test_type = data.get('test_type')
        number_of_questions = data.get('number_of_questions')
        difficulty = data.get('difficulty')

        topic = Topic.objects.get(pk=topic_id).content

        if test_type not in ["multiple_choice", "true_false", "short_answer"]:
            return Response(status=400,
                            data="Invalid question type. Supported types: 'multiple_choice', 'true_false', 'short_answer'")

        generated_questions = generate_questions(topic, test_type, number_of_questions, difficulty)

        if test_type == "multiple_choice":
            parsed_questions = parse_generated_questions(generated_questions)
            format_value = 1
        elif test_type == "true_false":
            parsed_questions = parse_true_false_questions(generated_questions)
            format_value = 2
        elif test_type == "short_answer":
            parsed_questions = parse_short_answer_questions(generated_questions)
            format_value = 3

        response_data = {"questions": parsed_questions, "format": format_value}

        return Response(response_data, status=status.HTTP_200_OK)


class CheckAnswersView(generics.CreateAPIView):
    serializer_class = CheckAnswersSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        question = serializer.validated_data['question']
        correct = serializer.validated_data['correct']
        user = serializer.validated_data['user']

        questions_and_answers = [
            {"Question": question, "GivenAnswer": user, "CorrectAnswer": correct},
        ]
        questions_and_answers_string = str(questions_and_answers)

        response = client.chat.completions.create(
            model=DEPLOYMENT_NAME,
            temperature=0.7,
            max_tokens=400,
            messages=[
                {"role": "system",
                 "content": 'You are an assistant, that checks answers and based on wrong ones generates educating texts on easy to understand language. Not longer than 5 sentences.'},
                {"role": "user", "content": questions_and_answers_string}
            ]
        )

        logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                            format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
        logger = logging.getLogger(__name__)

        gptresponse = response.choices[0].message.content
        print("Response: " + gptresponse + "\n")

        logger.info("Response: " + gptresponse + "\n")

        job_id = submit_synthesis(gptresponse)
        if job_id is not None:
            while True:
                response = get_synthesis(job_id)
                status = response['status']
                if status == 'Succeeded':
                    logger.info('batch avatar synthesis job succeeded')
                    url = response["outputs"]["result"]
                    response_data = {"url": url}

                    response_serializer = CheckAnswersResponseSerializer(data=response_data)
                    response_serializer.is_valid(raise_exception=True)
                    return JsonResponse(response_serializer.data, status=HTTP_200_OK)

                elif status == 'Failed':
                    logger.error('batch avatar synthesis job failed')
                    return Response({"detail": "batch avatar synthesis job failed"},
                                    status=status.HTTP_500_INTERNAL_SERVER_ERROR)
                else:
                    logger.info(f'batch avatar synthesis job is still running, status [{status}]')
                    time.sleep(5)
        else:
            return Response({"detail": "Synthesis job submission failed"}, status=HTTP_500_INTERNAL_SERVER_ERROR)
