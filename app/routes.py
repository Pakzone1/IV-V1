from flask import Blueprint, render_template, request, jsonify, session, redirect, url_for
from app.services.openai_service import OpenAIService
import os
import re

main = Blueprint('main', __name__)
openai_service = OpenAIService()

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
    session.clear()
    return redirect(url_for('main.login'))

@main.before_request
def check_auth():
    """Protect all routes except login"""
    if request.endpoint and 'static' not in request.endpoint:
        protected_endpoints = ['index', 'handle_message', 'handle_audio']
        if request.endpoint.split('.')[-1] in protected_endpoints and 'email' not in session:
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
            
        # Add message to thread
        openai_service.add_message(thread_id, message)
        
        # Get response
        response = openai_service.run_conversation(thread_id)
        
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
        
        # Process the transcribed text with the assistant
        thread_id = session.get('thread_id')
        openai_service.add_message(thread_id, text)
        response = openai_service.run_conversation(thread_id)
        
        # Include transcription in response
        response['transcription'] = text
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 