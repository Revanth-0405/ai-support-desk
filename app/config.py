import os
from datetime import timedelta
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'dev-secret-key')
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL', 'postgresql://user:password@localhost:5432/support_db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # JWT Config
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY', 'jwt-secret-key')
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # DynamoDB Config
    DYNAMODB_ENDPOINT_URL = os.environ.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000')
    AWS_REGION = os.environ.get('AWS_REGION', 'us-east-1')
    
    # Gemini AI Config
    GEMINI_API_KEY = os.environ.get('GEMINI_API_KEY')

class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    DYNAMODB_ENDPOINT_URL = 'http://localhost:8000'