from flask import Blueprint, render_template, request, jsonify, session
from app.services.openai_service import OpenAIService
import os

main = Blueprint('main', __name__)
openai_service = OpenAIService()

@main.route('/')
def index():
    if 'thread_id' not in session:
        session['thread_id'] = openai_service.create_thread()
    return render_template('index.html')

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
        
        return jsonify(response)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500 