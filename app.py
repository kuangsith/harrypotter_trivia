from flask import Flask, render_template, request, session, redirect, url_for
import random
from google import genai
from google.genai import types
from config import apikey
import numpy as np
import json
import datetime
import pandas as pd
from google.oauth2 import service_account
from google.cloud import bigquery
from pandas_gbq import to_gbq

client_ai = genai.Client(api_key=apikey)

def get_embedding(text):
    return client_ai.models.embed_content(model="text-embedding-004",contents=text).embeddings[0].values

def cosine_similarity(vec1, vec2):
    return np.dot(vec1, vec2) / (np.linalg.norm(vec1) * np.linalg.norm(vec2))


def check_sim_words(word1,word2):
    vec1 = get_embedding(word1)
    vec2 = get_embedding(word2)
    similarity = cosine_similarity(vec1, vec2)
    return similarity

def check_answer(correct_answer, user_input, threshold=0.74):
    similarity = check_sim_words(correct_answer,user_input)
    return similarity >= threshold



app = Flask(__name__, static_folder='static')
app.secret_key = 'YMCA1234' 

# Define your project and dataset details
PROJECT_ID = "kuang-fun"
DATASET_ID = "harrypotter_trivia"
TABLE_ID = "high-score"

# Path to your service account key file
SERVICE_ACCOUNT_FILE = "key.json"

# Authenticate using service account
credentials = service_account.Credentials.from_service_account_file(SERVICE_ACCOUNT_FILE)

# Initialize BigQuery client
client_bgq = bigquery.Client(credentials=credentials, project=PROJECT_ID)

def insert_into_gbq(df: pd.DataFrame):
    to_gbq(df, f"{DATASET_ID}.{TABLE_ID}", project_id=PROJECT_ID, credentials=credentials, if_exists="append")



@app.route('/')
def start_game():
    session.clear()  # Reset game state
    session['score'] = 0
    session['question_count'] = 0
    # session['remaining_questions'] = random.sample(trivia_questions, 5)  # Select 5 random questions
    prompt = """Generate a Harry Potter quiz. 10 Questions. Based on only Book1 to Book4 of the series.

    Use this JSON schema:

    questions = {'question': str, 'answer': str}
    Return: list[questions]"""

    response = client_ai.models.generate_content(
        model='gemini-2.0-flash',
        contents=prompt,
    )

    raw_string = response.text
    session['remaining_questions'] = json.loads(raw_string.strip("```json\n"))
    return render_template('start.html')

@app.route('/trivia', methods=['GET', 'POST'])
def trivia():
    if 'question_count' not in session or session['question_count'] >= 10:
        return redirect(url_for('name_inquiry'))

    if request.method == 'POST':
        user_answer = request.form.get('answer', '').strip().lower()
        correct_answer = session.get('correct_answer', '').lower()

        if check_answer(correct_answer, user_answer):
            session['score'] += 1
            result = f"Correct! The answer is {correct_answer}"
        else:
            result = f"Wrong! The correct answer was: {session['correct_answer']}."

        session['question_count'] += 1

        return render_template(
            'question.html',
            question=session.get('current_question', ''),
            result=result,
            score=session['score'],
            next_question=session['question_count'] < 10
        )

    # Select next question
    if session['question_count'] < 10:
        trivia = session['remaining_questions'][session['question_count']]
        session['current_question'] = trivia['question']
        session['correct_answer'] = trivia['answer']
        return render_template('question.html', question=trivia['question'], score=session['score'])

    return redirect(url_for('name_inquiry'))

@app.route('/name_inquiry', methods=['GET', 'POST'])
def name_inquiry():
    if request.method == 'POST':
        name = request.form.get('name', 'Anonymous')  # Default to 'Anonymous' if empty
        score = session.get('score', 0)  # Retrieve the score from the session
        timestamp = datetime.datetime.utcnow()

        # Insert the result into BigQuery
        df_insert = pd.DataFrame({
            "name": [name],
            "score": [score],
            "datetime": [timestamp]
        })
        # df_insert['datetime'] = pd.to_datetime(df_insert['datetime'])

        insert_into_gbq(df_insert)

        return redirect(url_for('results'))  # Move to results page after submission

    # Show the score and ask for name input
    return render_template('name_inquiry.html', score=session.get('score', 0))

@app.route('/results')
def results():
    # Query BigQuery for the top 5 high scores today
    today = datetime.datetime.utcnow().strftime('%Y-%m-%d')
    query = f"""
    SELECT name, score 
    FROM `{PROJECT_ID}.{DATASET_ID}.{TABLE_ID}`
    WHERE DATE(datetime) = '{today}'
    ORDER BY score DESC, datetime ASC
    LIMIT 5
    """
    query_job = client_bgq.query(query)
    high_scores = query_job.result()

    return render_template('results.html', score=session.get('score', 0), high_scores=high_scores)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080)