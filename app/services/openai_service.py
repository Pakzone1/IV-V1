import openai
from typing import Dict, Optional
import json
from pathlib import Path
import base64
import io
import os
import uuid
import time

class OpenAIService:
    def __init__(self):
        self.client = openai.OpenAI(api_key='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')
        self.assistant_id = 'asst_6pLqZw9jSY05df0MsoLfnLHl'
        self.temp_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'temp')
        
    def create_thread(self) -> str:
        """Create a new thread and return its ID"""
        thread = self.client.beta.threads.create()
        return thread.id
        
    def add_message(self, thread_id: str, content: str, file_ids: Optional[list] = None) -> None:
        """Add a message to the thread"""
        message_params = {
            "role": "user",
            "content": content
        }
        if file_ids:
            message_params["file_ids"] = file_ids
            
        self.client.beta.threads.messages.create(
            thread_id=thread_id,
            **message_params
        )
        
    def run_conversation(self, thread_id: str) -> Dict:
        """Run the assistant on the thread and return the response with audio"""
        run = self.client.beta.threads.runs.create(
            thread_id=thread_id,
            assistant_id=self.assistant_id
        )
        
        # Wait for completion
        while True:
            run_status = self.client.beta.threads.runs.retrieve(
                thread_id=thread_id,
                run_id=run.id
            )
            if run_status.status == 'completed':
                break
            elif run_status.status in ['failed', 'cancelled', 'expired']:
                raise Exception(f"Run ended with status: {run_status.status}")
                
        # Get messages
        messages = self.client.beta.threads.messages.list(thread_id=thread_id)
        latest_message = messages.data[0]
        text_content = latest_message.content[0].text.value
        
        # Generate speech from text
        speech_response = self.client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text_content
        )
        
        # Convert audio to base64 for sending over HTTP
        audio_data = speech_response.content
        audio_base64 = base64.b64encode(audio_data).decode('utf-8')
        
        return {
            'role': latest_message.role,
            'content': text_content,
            'audio': audio_base64
        }

    def handle_audio(self, audio_file) -> str:
        """Transcribe audio file and return text"""
        try:
            # Generate a unique filename
            temp_filename = f"{uuid.uuid4()}"
            temp_path = os.path.join(self.temp_dir, f"{temp_filename}.webm")

            # Save the uploaded file
            audio_file.save(temp_path)
            print(f"Transcribing file: {temp_path}")

            try:
                # Direct transcription using Whisper API
                with open(temp_path, 'rb') as audio:
                    transcript = self.client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio
                    )
                return transcript.text

            finally:
                # Clean up temporary file
                try:
                    if os.path.exists(temp_path):
                        os.remove(temp_path)
                except Exception as e:
                    print(f"Error cleaning up temporary file: {str(e)}")

        except Exception as e:
            print(f"Error processing audio: {str(e)}")
            raise 