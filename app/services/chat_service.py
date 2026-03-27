import uuid
import boto3
from datetime import datetime, timezone
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from flask import current_app, request

class ChatService:
    _dynamodb_resource = None

    @staticmethod
    def get_db():
        if ChatService._dynamodb_resource is None:
            ChatService._dynamodb_resource = boto3.resource(
                'dynamodb',
                endpoint_url=current_app.config.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000'),
                region_name=current_app.config.get('AWS_REGION', 'us-east-1'),
                aws_access_key_id=current_app.config.get('AWS_ACCESS_KEY_ID', 'dummy'),
                aws_secret_access_key=current_app.config.get('AWS_SECRET_ACCESS_KEY', 'dummy')
            )
        return ChatService._dynamodb_resource

    @staticmethod
    def initialize_tables():
        dynamodb = ChatService.get_db()
        tables = [
            {'TableName': 'ChatMessages', 'KeySchema': [{'AttributeName': 'ticket_id', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}], 'AttributeDefinitions': [{'AttributeName': 'ticket_id', 'AttributeType': 'S'}, {'AttributeName': 'timestamp', 'AttributeType': 'S'}], 'BillingMode': 'PAY_PER_REQUEST'},
            {'TableName': 'UserPresence', 'KeySchema': [{'AttributeName': 'user_id', 'KeyType': 'HASH'}], 'AttributeDefinitions': [{'AttributeName': 'user_id', 'AttributeType': 'S'}], 'BillingMode': 'PAY_PER_REQUEST'},
            {'TableName': 'AIUsageLogs', 'KeySchema': [{'AttributeName': 'log_id', 'KeyType': 'HASH'}, {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}], 'AttributeDefinitions': [{'AttributeName': 'log_id', 'AttributeType': 'S'}, {'AttributeName': 'timestamp', 'AttributeType': 'S'}], 'BillingMode': 'PAY_PER_REQUEST'}
        ]
        
        for table_def in tables:
            try:
                dynamodb.create_table(**table_def)
            except ClientError as e:
                if e.response['Error']['Code'] != 'ResourceInUseException':
                    raise

    @staticmethod
    def put_message(ticket_id, sender_id, sender_role, content, message_type='text'):
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('ChatMessages')
        now = datetime.now(timezone.utc).isoformat()
        
        # FIX: Propagate request_id
        req_id = getattr(request, 'request_id', 'ws-event')
        
        message = {
            'ticket_id': str(ticket_id),
            'timestamp': now,
            'message_id': str(uuid.uuid4()),
            'sender_id': str(sender_id),
            'sender_role': sender_role,
            'content': content,
            'message_type': message_type,
            'created_at': now,
            'request_id': req_id
        }
        table.put_item(Item=message)
        return message

    @staticmethod
    def get_messages_by_ticket(ticket_id, limit=50):
        """Retrieves last N messages using efficient Query [cite: 104, 226]"""
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('ChatMessages')
        
        # Querying with Partition Key (efficient retrieval) 
        response = table.query(
            KeyConditionExpression=Key('ticket_id').eq(str(ticket_id)),
            ScanIndexForward=False, # Get newest first
            Limit=limit
        )
        
        items = response.get('Items', [])
        items.reverse() # Return chronological order
        return items

    @staticmethod
    def get_message_count(ticket_id):
        """Gets total message count for a ticket """
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('ChatMessages')
        
        response = table.query(
            KeyConditionExpression=Key('ticket_id').eq(str(ticket_id)),
            Select='COUNT'
        )
        return response.get('Count', 0)