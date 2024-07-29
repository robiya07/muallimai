import re
import logging
import sys
import requests
from groq import Groq
import json

client = Groq(
    api_key='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'
)

logging.basicConfig(stream=sys.stdout, level=logging.INFO,
                    format="[%(asctime)s] %(message)s", datefmt="%m/%d/%Y %I:%M:%S %p %Z")
logger = logging.getLogger(__name__)

# Configuration for text-to-speech
SUBSCRIPTION_KEY = '0e5dbb08dd6f40d194197035471737cc'
SERVICE_REGION = "westeurope"
NAME = "Muallimai"
DESCRIPTION = "Muallimai"

SERVICE_HOST = 'customvoice.api.speech.microsoft.com'


def generate_questions(text, question_type, question_count, question_difficulty):
    prompt = f"Generate {question_count} {question_type} questions about {text}, difficulty: {question_difficulty}."
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": """You are a questionnaire generator, and you need to generate questionnaires based on question type with the correct answer.
Each time you need to generate different questions since different users will use this program. Always include answers with questions. When you generate true or false questions, remove "True or False:" from the beginning and put the question with the correct answer in brackets (True or False). When you generate multiple-choice questions, format them as follows:
            1. What did Elon Musk say about Tesla and Bitcoin?
            a) Tesla will not accept payments in Bitcoin because of environmental concerns.
            b) Tesla will start accepting payments in Bitcoin from now on.
            c) Tesla will accept payments in Bitcoin, but only on weekends.
            Answer: a
When you generate short answer type questions, include the correct answer with the format correct_answer: and ensure the correct answer is no more than 3 words.
"""},
            {"role": "user", "content": prompt}
        ],
        temperature=0,
        max_tokens=2000,
    )
    print(response)
    generated_questions = response.choices[0].message.content.strip().split("\n")
    print(generated_questions)
    return [i for i in generated_questions if i]


def parse_generated_questions(generated_questions):
    questions = []
    current_question = {}
    answer_patterns = r'^(correct|Correct) (answer|Answer):|^answer:|^Answer:'

    for line in generated_questions:
        if re.match(r'^\d+\..+', line):
            if current_question:
                questions.append(current_question)
            question_parts = line.split('.', 1)
            current_question = {'question': question_parts[1].strip(), 'options': []}
        elif re.match(r'^[A-Za-z]\.|[A-Za-z]\)[\s]', line):  # Match both formats of options
            current_question['options'].append(line.strip())
        elif re.match(answer_patterns, line):
            current_question['answer'] = line.split(':', 1)[1].strip()
            questions.append(current_question)
            current_question = None

    return questions


def parse_true_false_questions(true_false_questions):
    questions = []

    for statement in true_false_questions:
        question_parts = statement.split('. (')
        question_text = question_parts[0].strip()
        answer_text = question_parts[1].strip(')')

        question_number, question_text = question_text.split('. ', 1)

        answer = answer_text.lower() == 'true'

        question = {
            'question': question_text,
            'answer': answer
        }

        questions.append(question)

    return questions


def parse_short_answer_questions(short_answer_questions):
    questions = []
    temp_question = {}

    for entry in short_answer_questions:
        if re.match(r'^\d+\.', entry):
            if temp_question.get('question') and temp_question.get('answer'):
                questions.append(temp_question)
                temp_question = {}

            first_dot_index = entry.find('.')
            question_text = entry[first_dot_index + 1:].strip()
            temp_question['question'] = question_text
            if "(correct answer:" in question_text:
                split_text = question_text.split("(correct answer:")
                temp_question['question'] = split_text[0].strip()
                temp_question['answer'] = split_text[1].strip(')').strip()
        elif re.match(r'^(Correct answer:|correct answer:)', entry):
            answer_text = entry.split(':', 1)[1].strip()
            temp_question['answer'] = answer_text

    if temp_question.get('question') and temp_question.get('answer'):
        questions.append(temp_question)

    return questions


def submit_synthesis(gptresponse):
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY,
        'Content-Type': 'application/json'
    }

    payload = {
        'displayName': NAME,
        'description': DESCRIPTION,
        "textType": "PlainText",
        'synthesisConfig': {
            "voice": "en-US-JennyNeural",
        },
        'customVoices': {
        },
        "inputs": [
            {
                "text": gptresponse,
            },
        ],
        "properties": {
            "customized": False,
            "talkingAvatarCharacter": "lisa",
            "talkingAvatarStyle": "graceful-sitting",
            "videoFormat": "webm",
            "videoCodec": "vp9",
            "subtitleType": "soft_embedded",
            "backgroundColor": "transparent",
        }
    }

    response = requests.post(url, json.dumps(payload), headers=header)
    if response.status_code < 400:
        logger.info('Batch avatar synthesis job submitted successfully')
        logger.info(f'Job ID: {response.json()["id"]}')
        return response.json()["id"]
    else:
        logger.error(f'Failed to submit batch avatar synthesis job: {response.text}')


def get_synthesis(job_id):
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar/{job_id}'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
    }
    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.debug('Get batch synthesis job successfully')
        logger.debug(response.json())
        return response.json()
    else:
        logger.error(f'Failed to get batch synthesis job: {response.text}')


def list_synthesis_jobs(skip: int = 0, top: int = 100):
    """List all batch synthesis jobs in the subscription"""
    url = f'https://{SERVICE_REGION}.{SERVICE_HOST}/api/texttospeech/3.1-preview1/batchsynthesis/talkingavatar?skip={skip}&top={top}'
    header = {
        'Ocp-Apim-Subscription-Key': SUBSCRIPTION_KEY
    }
    response = requests.get(url, headers=header)
    if response.status_code < 400:
        logger.info(f'List batch synthesis jobs successfully, got {len(response.json()["values"])} jobs')
        logger.info(response.json())
    else:
        logger.error(f'Failed to list batch synthesis jobs: {response.text}')
