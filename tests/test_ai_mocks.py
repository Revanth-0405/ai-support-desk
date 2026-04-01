import pytest
from unittest.mock import patch, MagicMock
from app.services.ai_service import AIService

@patch('app.services.ai_service.genai.GenerativeModel')
def test_ai_categorise_mock(mock_model, app):
    """Test AI categorisation with a mocked Gemini response"""
    mock_response = MagicMock()
    mock_response.text = '{"category": "technical", "priority": "high"}'
    
    # Setup the mock model instance
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = mock_response
    mock_model.return_value = mock_instance
    
    # Bypass DynamoDB logging for the test
    with patch('app.services.ai_service.AIService.log_usage'):
        result = AIService.categorise_ticket("ticket-123", "Login broken", "500 error")
        assert result['category'] == 'technical'
        assert result['priority'] == 'high'

@patch('app.services.ai_service.genai.GenerativeModel')
def test_ai_graceful_failure(mock_model, app):
    """Test AI handling invalid JSON response"""
    mock_response = MagicMock()
    mock_response.text = 'Invalid JSON output from AI'
    
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = mock_response
    mock_model.return_value = mock_instance
    
    with patch('app.services.ai_service.AIService.log_usage'):
        result = AIService.categorise_ticket("ticket-123", "Test", "Test")
        assert result is None  # Should degrade gracefully

@patch('app.services.ai_service.genai.GenerativeModel')
def test_ai_suggest_mock(mock_model, app):
    """Test AI response suggestion mock"""
    mock_response = MagicMock()
    mock_response.text = 'Please try resetting your router.'
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = mock_response
    mock_model.return_value = mock_instance
    
    with patch('app.services.ai_service.AIService.log_usage'):
        result = AIService.generate_suggestion("ticket-123", [], [])
        assert "router" in result

@patch('app.services.ai_service.genai.GenerativeModel')
def test_ai_summarise_mock(mock_model, app):
    """Test AI conversation summarisation mock"""
    mock_response = MagicMock()
    mock_response.text = 'The issue is resolved.'
    mock_instance = MagicMock()
    mock_instance.generate_content.return_value = mock_response
    mock_model.return_value = mock_instance

    with patch('app.services.ai_service.AIService.log_usage'):
        result = AIService.summarise_conversation("ticket-123", [{"sender_role": "customer", "content": "fixed"}])
        assert "resolved" in result