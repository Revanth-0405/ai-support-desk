import os
import json
import time
import uuid
import logging
from datetime import datetime, timezone
import google.generativeai as genai
from google.generativeai.types import GenerationConfig
from app.services.chat_service import ChatService
from flask import request

logger = logging.getLogger(__name__)

class AIService:
    @staticmethod
    def _get_model():
        api_key = os.environ.get('GEMINI_API_KEY')
        if not api_key:
            raise ValueError("GEMINI_API_KEY is not set.")
        genai.configure(api_key=api_key)
        return genai.GenerativeModel('gemini-2.0-flash')

    @staticmethod
    def log_usage(feature, ticket_id, prompt_tokens, completion_tokens, latency_ms, success, error=None):
        try:
            dynamodb = ChatService.get_db()
            table = dynamodb.Table('AIUsageLogs')
            req_id = getattr(request, 'request_id', 'ws-event')
            
            table.put_item(Item={
                'log_id': str(uuid.uuid4()),
                'timestamp': datetime.now(timezone.utc).isoformat(),
                'feature': feature,
                'ticket_id': str(ticket_id),
                'request_id': req_id,
                'model_used': 'gemini-2.0-flash',
                'prompt_tokens': prompt_tokens or 0,
                'completion_tokens': completion_tokens or 0,
                'latency_ms': int(latency_ms),
                'success': success,
                'error': str(error) if error else None
            })
        except Exception as e:
            logger.error(f"Failed to log AI usage: {str(e)}")

    @staticmethod
    def _call_with_retry(prompt, feature_name, ticket_id, generation_config=None):
        model = AIService._get_model()
        max_retries = 3
        base_delay = 2
        
        for attempt in range(max_retries):
            start_time = time.time()
            try:
                response = model.generate_content(prompt, generation_config=generation_config)
                latency = (time.time() - start_time) * 1000
                p_tokens = response.usage_metadata.prompt_token_count if hasattr(response, 'usage_metadata') else 0
                c_tokens = response.usage_metadata.candidates_token_count if hasattr(response, 'usage_metadata') else 0
                AIService.log_usage(feature_name, ticket_id, p_tokens, c_tokens, latency, True)
                return response.text
                
            except Exception as e:
                if '429' in str(e) and attempt < max_retries - 1:
                    # FIX: Meaningful exponential backoff
                    time.sleep(base_delay * (2 ** attempt)) 
                    continue
                    
                latency = (time.time() - start_time) * 1000
                AIService.log_usage(feature_name, ticket_id, 0, 0, latency, False, error=str(e))
                return None
        return None

    @staticmethod
    def categorise_ticket(ticket_id, subject, description):
        # FIX: JSON dump input to prevent injection breaking the prompt
        safe_subject = json.dumps(subject)
        safe_desc = json.dumps(description)
        
        prompt = f"""
        Analyze the following support ticket and assign it a category and priority.
        Valid Categories: billing, technical, account, feature_request, bug_report, general.
        Valid Priorities: low, medium, high, urgent.
        
        Examples:
        Subject: "Can't access my dashboard" | Description: "I get a 500 error on login." -> {{"category": "technical", "priority": "high"}}
        
        Now categorize this ticket:
        Subject: {safe_subject}
        Description: {safe_desc}
        """
        config = GenerationConfig(response_mime_type="application/json")
        result = AIService._call_with_retry(prompt, 'categorise', ticket_id, generation_config=config)
        
        if result:
            try:
                parsed = json.loads(result)
                # FIX: Validate output against allowed ENUMs
                VALID_CATEGORIES = {'billing', 'technical', 'account', 'feature_request', 'bug_report', 'general'}
                VALID_PRIORITIES = {'low', 'medium', 'high', 'urgent'}
                
                if parsed.get('category') not in VALID_CATEGORIES:
                    parsed['category'] = None
                if parsed.get('priority') not in VALID_PRIORITIES:
                    parsed.pop('priority', None)
                return parsed
            except json.JSONDecodeError:
                return None
        return None

    @staticmethod
    def generate_suggestion(ticket_id, context_messages, kb_articles):
        """Generates a professional draft response [cite: 136-141]"""
        kb_context = "\n".join([f"Title: {kb.title}\nContent: {kb.content}" for kb in kb_articles])
        chat_context = "\n".join([f"{msg['sender_role']}: {msg['content']}" for msg in context_messages])
        
        prompt = f"""
        Draft a helpful, professional response from an agent to a customer based on the chat history and knowledge base.
        
        Knowledge Base Articles:
        {kb_context if kb_articles else 'None available.'}
        
        Recent Chat History:
        {chat_context}
        
        Provide ONLY the exact text the agent should send to the customer. Do not include introductory phrases.
        """
        return AIService._call_with_retry(prompt, 'suggest', ticket_id)

    @staticmethod
    def summarise_conversation(ticket_id, messages):
        """Generates a 3-5 sentence summary on resolution [cite: 146-149]"""
        chat_context = "\n".join([f"{msg['sender_role']}: {msg['content']}" for msg in messages])
        
        prompt = f"""
        Summarize the following support conversation in exactly 3 to 5 sentences.
        You MUST cover:
        1. What the customer's issue was.
        2. What solution was provided.
        3. The final outcome.
        
        Conversation:
        {chat_context}
        """
        return AIService._call_with_retry(prompt, 'summarise', ticket_id)