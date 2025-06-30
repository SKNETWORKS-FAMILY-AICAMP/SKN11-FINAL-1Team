# chatbot/consumers.py
import json
from channels.generic.websocket import AsyncWebsocketConsumer

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
    
    async def disconnect(self, close_code):
        pass
    
    async def receive(self, text_data):
        data = json.loads(text_data)
        message = data['message']
        
        # MCP 도구를 사용한 응답 생성 로직
        response = await self.process_with_mcp_tools(message)
        
        await self.send(text_data=json.dumps({
            'role': 'assistant',
            'content': response
        }))
