from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.services.openai_service import OpenAIService
from app.services.transcript_service import TranscriptService
import os
import re

main = Blueprint('main', __name__)
openai_service = OpenAIService()
transcript_service = TranscriptService()

def is_valid_email(email):
    """Basic email validation"""
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

@main.route('/')
def index():
    if 'email' not in session:
        return redirect(url_for('main.login'))
    
    if 'thread_id' not in session:
        session['thread_id'] = openai_service.create_thread()
    return render_template('index.html', email=session['email'])

@main.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        if email and is_valid_email(email):
            session['email'] = email
            return redirect(url_for('main.index'))
        return render_template('login.html', error="Please enter a valid email address")
    return render_template('login.html')

@main.route('/logout')
def logout():
    if 'email' in session:
        try:
            # Score the interview before clearing the session
            result = transcript_service.score_interview(session['email'])
            if 'error' in result:
                print(f"Error scoring interview: {result['error']}")
        except Exception as e:
            print(f"Error during interview scoring: {str(e)}")
    
    session.clear()
    return redirect(url_for('main.login'))

@main.route('/message', methods=['POST'])
def handle_message():
    try:
        data = request.get_json()
        message = data.get('message')
        thread_id = session.get('thread_id')
        
        if not thread_id:
            thread_id = openai_service.create_thread()
            session['thread_id'] = thread_id
            
        # Save user message to transcript
        transcript_service.save_transcript(session['email'], 'user', message)
            
        # Add message to thread
        openai_service.add_message(thread_id, message)
        
        # Get response
        response = openai_service.run_conversation(thread_id)
        
        # Save assistant response to transcript
        transcript_service.save_transcript(session['email'], 'assistant', response['content'])
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/audio', methods=['POST'])
def handle_audio():
    try:
        audio_file = request.files.get('audio')
        if not audio_file:
            return jsonify({'error': 'No audio file provided'}), 400
            
        # Transcribe audio
        text = openai_service.handle_audio(audio_file)
        
        # Save user's transcribed message
        transcript_service.save_transcript(session['email'], 'user', text)
        
        # Process the transcribed text with the assistant
        thread_id = session.get('thread_id')
        openai_service.add_message(thread_id, text)
        response = openai_service.run_conversation(thread_id)
        
        # Save assistant's response
        transcript_service.save_transcript(session['email'], 'assistant', response['content'])
        
        # Include transcription in response
        response['transcription'] = text
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@main.route('/get-score', methods=['GET'])
def get_score():
    """Get the interview score and feedback"""
    if 'email' not in session:
        return jsonify({'error': 'Not logged in'}), 401
        
    try:
        transcripts = transcript_service.get_user_transcripts(session['email'])
        if not transcripts:
            return jsonify({'error': 'No transcripts found'}), 404
            
        return jsonify({
            'score': transcripts.get('score'),
            'feedback': transcripts.get('feedback')
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 