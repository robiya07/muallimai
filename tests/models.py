from django.db import models


class Subject(models.Model):
    name = models.CharField(max_length=255)
    image = models.ImageField(upload_to='subjects/')
    grade = models.PositiveSmallIntegerField()

    def __str__(self):
        return self.name


class Topic(models.Model):
    subject = models.ForeignKey(Subject, related_name='topics', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    content = models.TextField()

    def __str__(self):
        return self.name


class Test(models.Model):
    TOPIC_CHOICES = [
        ('multiple_choice', 'Multiple choice'),
        ('true_false', 'True false'),
        ('short_answer', 'Short answer'),
    ]
    DIFFICULTY_CHOICES = [
        ('easy', 'Easy'),
        ('medium', 'Medium'),
        ('hard', 'Hard'),
    ]
    topic = models.ForeignKey(Topic, related_name='tests', on_delete=models.CASCADE)
    type = models.CharField(max_length=20, choices=TOPIC_CHOICES)
    number_of_questions = models.PositiveIntegerField()
    difficulty = models.CharField(max_length=10, choices=DIFFICULTY_CHOICES)

    def __str__(self):
        return f"{self.topic.name} - {self.type} - {self.difficulty}"
