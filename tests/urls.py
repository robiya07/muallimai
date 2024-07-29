from django.urls import path
from .views import GenerateTestsView, SubjectsListView, TopicsListView, CheckAnswersView

app_name = "tests"

urlpatterns = [
    path('subjects/', SubjectsListView.as_view(), name='subjects-list'),
    path('subjects/<int:subject_id>/topics/', TopicsListView.as_view(), name='topics-list'),
    path('generate-tests/', GenerateTestsView.as_view(), name='generate_tests'),
    path('check-answers/', CheckAnswersView.as_view(), name='check_answers'),
]
