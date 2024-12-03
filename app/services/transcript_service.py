import os
import json
from datetime import datetime
from pathlib import Path
from typing import List, Dict
import openai

class TranscriptService:
    def __init__(self):
        self.transcript_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'transcripts')
        self.client = openai.OpenAI(api_key='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')
        os.makedirs(self.transcript_dir, exist_ok=True)

    def get_user_transcript_path(self, email: str) -> str:
        """Get the path to a user's transcript file"""
        safe_email = email.replace('@', '_at_').replace('.', '_dot_')
        return os.path.join(self.transcript_dir, f"{safe_email}_transcript.json")

    def save_transcript(self, email: str, role: str, content: str) -> None:
        """Save a new transcript entry for a user"""
        transcript_path = self.get_user_transcript_path(email)
        
        # Load existing transcripts or create new
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r') as f:
                data = json.load(f)
        else:
            data = {
                'email': email,
                'messages': [],
                'score': None,
                'feedback': None
            }
        
        # Add new message
        data['messages'].append({
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        })
        
        # Save updated transcripts
        with open(transcript_path, 'w') as f:
            json.dump(data, f, indent=2)

    def get_user_transcripts(self, email: str) -> Dict:
        """Get all transcripts for a user"""
        transcript_path = self.get_user_transcript_path(email)
        if os.path.exists(transcript_path):
            with open(transcript_path, 'r') as f:
                return json.load(f)
        return None

    def score_interview(self, email: str) -> Dict:
        """Score the interview using OpenAI"""
        transcripts = self.get_user_transcripts(email)
        if not transcripts or not transcripts['messages']:
            return {'error': 'No transcripts found'}

        # Prepare the conversation for analysis
        conversation = ""
        for msg in transcripts['messages']:
            conversation += f"{msg['role'].upper()}: {msg['content']}\n\n"

        # Create the scoring prompt
        prompt = f"""Please analyze this interview conversation and provide a detailed evaluation with scores:

{conversation}

Please evaluate the following aspects:
1. Communication Skills (0-10)
2. Technical Knowledge (0-10)
3. Problem-Solving Ability (0-10)
4. Overall Interview Performance (0-10)

Provide a brief explanation for each score and general feedback for improvement.
Format your response as JSON with the following structure:
{{
    "scores": {{
        "communication": X,
        "technical": X,
        "problem_solving": X,
        "overall": X
    }},
    "feedback": {{
        "communication": "explanation...",
        "technical": "explanation...",
        "problem_solving": "explanation...",
        "overall": "explanation..."
    }},
    "improvement_suggestions": ["suggestion1", "suggestion2", ...]
}}"""

        try:
            # Get evaluation from OpenAI
            response = self.client.chat.completions.create(
                model="gpt-4",
                messages=[
                    {"role": "system", "content": "You are an expert interview evaluator. Provide detailed, constructive feedback."},
                    {"role": "user", "content": prompt}
                ],
                response_format={ "type": "json_object" }
            )
            
            # Parse the response
            evaluation = json.loads(response.choices[0].message.content)
            
            # Update the transcript file with scores and feedback
            transcripts['score'] = evaluation['scores']
            transcripts['feedback'] = {
                'detailed_feedback': evaluation['feedback'],
                'improvements': evaluation['improvement_suggestions']
            }
            
            # Save updated transcripts
            transcript_path = self.get_user_transcript_path(email)
            with open(transcript_path, 'w') as f:
                json.dump(transcripts, f, indent=2)
            
            return evaluation
            
        except Exception as e:
            print(f"Error scoring interview: {str(e)}")
            return {'error': str(e)} 