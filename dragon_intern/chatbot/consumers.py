# chatbot/consumers.py
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from django.conf import settings
from .views import (
    initialize_session, process_query_async, 
    load_config_from_json, get_or_create_event_loop
)

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        await self.accept()
        self.history = []  # 세션별 대화 히스토리 (메모리 기반)
        # MCP 초기화
        try:
            config = load_config_from_json()
            success = await initialize_session(config, 'claude-3-7-sonnet-latest')
            if success:
                await self.send(text_data=json.dumps({
                    'role': 'system',
                    'content': '✅ MCP 도구가 초기화되었습니다. 질문해주세요!'
                }))
            else:
                await self.send(text_data=json.dumps({
                    'role': 'system', 
                    'content': '❌ MCP 초기화에 실패했습니다.'
                }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                'role': 'system',
                'content': f'❌ 초기화 오류: {str(e)}'
            }))

    async def disconnect(self, close_code):
        pass

    async def receive(self, text_data):
        try:
            data = json.loads(text_data)
            message = data['message']

            # 사용자 메시지 먼저 표시
            await self.send(text_data=json.dumps({
                'role': 'user',
                'content': message
            }))

            # 이전 대화 히스토리에 추가 (질문)
            self.history.append({'role': 'user', 'content': message})

            # MCP 도구를 사용한 응답 생성 (스트리밍 콜백 사용)
            await self.process_with_mcp_streaming(message)

        except Exception as e:
            await self.send(text_data=json.dumps({
                'role': 'assistant',
                'content': f'❌ 오류가 발생했습니다: {str(e)}'
            }))

    async def process_with_mcp_streaming(self, message):
        """MCP 도구를 사용하여 스트리밍 응답 생성"""
        system_sent = False
        try:
            self.assistant_buffer = ""  # assistant 답변 누적 버퍼
            # 스트리밍 콜백 함수 정의
            async def streaming_callback(chunk_data):
                """실시간으로 응답을 웹소켓에 전송"""
                content = ""
                if 'content' in chunk_data:
                    chunk_msg = chunk_data['content']
                    # 표/리스트/딕셔너리/JSON 등은 마크다운 코드블록으로 감싸기
                    if isinstance(chunk_msg, (dict, list)):
                        import pprint
                        content = '\n```json\n' + json.dumps(chunk_msg, ensure_ascii=False, indent=2) + '\n```\n'
                    elif hasattr(chunk_msg, 'content'):
                        if isinstance(chunk_msg.content, list):
                            for item in chunk_msg.content:
                                if isinstance(item, dict) and "text" in item:
                                    content += item["text"]
                        elif isinstance(chunk_msg.content, str):
                            content += chunk_msg.content
                    else:
                        content = str(chunk_msg)
                if content:
                    # assistant 답변 누적
                    self.assistant_buffer += content
                    # 답변 구분선 추가 (assistant_stream 첫 청크에만 구분선)
                    if self.assistant_buffer == content:
                        content = '---\n' + content
                    await self.send(text_data=json.dumps({
                        'role': 'assistant_stream',
                        'content': content,
                        'node': chunk_data.get('node', 'unknown')
                    }))

            import uuid
            thread_id = str(uuid.uuid4())

            # views.py의 astream_graph를 콜백과 함께 사용, history도 전달
            await self.execute_with_streaming(message, streaming_callback, thread_id)

            # assistant 전체 답변을 history에 저장 (구분선 제거)
            if hasattr(self, 'assistant_buffer') and self.assistant_buffer:
                clean_content = self.assistant_buffer.lstrip('-\n').strip()
                self.history.append({'role': 'assistant', 'content': clean_content})
                self.assistant_buffer = ""

        except Exception as e:
            await self.send(text_data=json.dumps({
                'role': 'assistant',
                'content': f'❌ 처리 중 오류: {str(e)}'
            }))
        finally:
            # 답변이 끝난 뒤 반드시 system: '✅ 응답 완료' 메시지 전송 (예외 발생해도 무시)
            if not system_sent:
                try:
                    await self.send(text_data=json.dumps({
                        'role': 'system',
                        'content': '✅ 응답 완료'
                    }))
                except Exception:
                    pass

    async def execute_with_streaming(self, query, callback, thread_id):
        """스트리밍 콜백과 함께 에이전트 실행"""
        from .views import agent
        from utils import astream_graph
        from langchain_core.messages import HumanMessage
        from langchain_core.runnables import RunnableConfig

        # 이전 대화 히스토리도 함께 전달 (최신 10개만 예시)
        history_msgs = self.history[-10:] if hasattr(self, 'history') else []
        # messages: [history..., HumanMessage(content=query)]
        messages = []
        for h in history_msgs:
            if h['role'] == 'user':
                messages.append(HumanMessage(content=h['content']))
            else:
                # assistant/system 등은 assistant로 처리
                from langchain_core.messages import AIMessage
                messages.append(AIMessage(content=h['content']))
        messages.append(HumanMessage(content=query))

        if agent:
            await astream_graph(
                agent,
                {"messages": messages},
                config=RunnableConfig(
                    recursion_limit=100,
                    thread_id=thread_id,
                ),
                callback=callback,  # 콜백 함수 전달
                stream_mode="messages"
            )
        else:
            # agent가 None이면 바로 system 메시지 전송
            try:
                await self.send(text_data=json.dumps({
                    'role': 'system',
                    'content': '✅ 응답 완료'
                }))
            except Exception:
                pass
