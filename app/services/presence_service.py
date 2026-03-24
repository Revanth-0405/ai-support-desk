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
        """Batch retrieves presence for a list of agent IDs """
        if not agent_ids:
            return []
            
        dynamodb = ChatService.get_db()
        keys = [{'user_id': str(aid)} for aid in agent_ids]
        
        response = dynamodb.meta.client.batch_get_item(
            RequestItems={
                'UserPresence': {
                    'Keys': keys
                }
            }
        )
        
        # Default to offline if no record exists
        presence_dict = {item['user_id']: item for item in response.get('Responses', {}).get('UserPresence', [])}
        
        results = []
        for aid in agent_ids:
            str_aid = str(aid)
            if str_aid in presence_dict:
                results.append(presence_dict[str_aid])
            else:
                results.append({"user_id": str_aid, "status": "offline", "last_seen": None})
                
        return results