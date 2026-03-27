from datetime import datetime, timezone
from app.services.chat_service import ChatService
from boto3.dynamodb.conditions import Attr

class PresenceService:
    @staticmethod
    def update_presence(user_id, status, socket_id=None, active_ticket_id=None):
        """Updates user presence state [cite: 106, 108]"""
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('UserPresence')
        
        now = datetime.now(timezone.utc).isoformat()
        
        update_expr = "SET #st = :status, last_seen = :ls"
        expr_attr_names = {"#st": "status"}
        expr_attr_values = {":status": status, ":ls": now}
        
        if socket_id is not None:
            update_expr += ", socket_id = :sid"
            expr_attr_values[":sid"] = socket_id
            
        if active_ticket_id is not None:
            update_expr += ", active_ticket_id = :tid"
            expr_attr_values[":tid"] = active_ticket_id

        table.update_item(
            Key={'user_id': str(user_id)},
            UpdateExpression=update_expr,
            ExpressionAttributeNames=expr_attr_names,
            ExpressionAttributeValues=expr_attr_values
        )

    @staticmethod
    def get_user_presence(user_id):
        dynamodb = ChatService.get_db()
        table = dynamodb.Table('UserPresence')
        response = table.get_item(Key={'user_id': str(user_id)})
        return response.get('Item')

    @staticmethod
    def get_agents_presence(agent_ids):
        if not agent_ids:
            return []
            
        dynamodb = ChatService.get_db()
        results = []
        
        for i in range(0, len(agent_ids), 100):
            chunk = agent_ids[i:i+100]
            # FIX: Correct low-level key format for batch_get_item
            keys = [{'user_id': {'S': str(aid)}} for aid in chunk]
            
            response = dynamodb.meta.client.batch_get_item(
                RequestItems={'UserPresence': {'Keys': keys}}
            )
            
            # Map low-level responses back to dicts
            presence_dict = {}
            for item in response.get('Responses', {}).get('UserPresence', []):
                user_id = item.get('user_id', {}).get('S')
                if user_id:
                    presence_dict[user_id] = {
                        'user_id': user_id,
                        'status': item.get('status', {}).get('S', 'offline'),
                        'last_seen': item.get('last_seen', {}).get('S')
                    }
            
            for aid in chunk:
                str_aid = str(aid)
                results.append(presence_dict.get(str_aid, {"user_id": str_aid, "status": "offline", "last_seen": None}))
                    
        return results