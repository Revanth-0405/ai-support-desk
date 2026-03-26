import uuid
from datetime import datetime, timezone
import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from flask import current_app

class ChatService:
    @staticmethod
    def get_db():
        return boto3.resource(
            'dynamodb',
            endpoint_url=current_app.config.get('DYNAMODB_ENDPOINT_URL', 'http://localhost:8000'),
            region_name=current_app.config.get('AWS_REGION', 'us-east-1'),
            aws_access_key_id='dummy', # Required for local DynamoDB
            aws_secret_access_key='dummy'
        )

    @staticmethod
    def initialize_tables():
        """Creates DynamoDB tables if they don't exist."""
        dynamodb = ChatService.get_db()
        try:
            # Create ChatMessages Table [cite: 102, 103]
            dynamodb.create_table(
                TableName='ChatMessages',
                KeySchema=[
                    {'AttributeName': 'ticket_id', 'KeyType': 'HASH'},  # Partition key 
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}   # Sort key 
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'ticket_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
            
            # Create UserPresence Table 
            dynamodb.create_table(
                TableName='UserPresence',
                KeySchema=[
                    {'AttributeName': 'user_id', 'KeyType': 'HASH'} # Partition key 
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'user_id', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise e # Ignore if tables already exist
            
            # Create AIUsageLogs Table [cite: 153-154]
            dynamodb.create_table(
                TableName='AIUsageLogs',
                KeySchema=[
                    {'AttributeName': 'log_id', 'KeyType': 'HASH'},
                    {'AttributeName': 'timestamp', 'KeyType': 'RANGE'}
                ],
                AttributeDefinitions=[
                    {'AttributeName': 'log_id', 'AttributeType': 'S'},
                    {'AttributeName': 'timestamp', 'AttributeType': 'S'}
                ],
                BillingMode='PAY_PER_REQUEST'
            )
        except ClientError as e:
            if e.response['Error']['Code'] != 'ResourceInUseException':
                raise e

    @staticmethod
    def put_message(ticket_id, sender_id, sender_role, content, message_type='text'):
        """Stores a message in DynamoDB """
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('ChatMessages')
        
        now = datetime.now(timezone.utc).isoformat()
        message = {
            'ticket_id': str(ticket_id),
            'timestamp': now,
            'message_id': str(uuid.uuid4()),
            'sender_id': str(sender_id),
            'sender_role': sender_role,
            'content': content,
            'message_type': message_type,
            'created_at': now
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