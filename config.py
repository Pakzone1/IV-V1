import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = 'your-secret-key-here'
    OPENAI_API_KEY = 'asdfghjhfdfgjfdfgjkjdsdfghjhfdfjfdrtyuytrertyu'
    ASSISTANT_ID = 'dfghu654rtyu654ertyujhgre456yuyg'
    SESSION_PERMANENT = False
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes session timeout