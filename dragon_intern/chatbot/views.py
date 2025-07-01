# chatbot/views.py
import json
import os
import asyncio
import platform
import nest_asyncio
from django.conf import settings
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.views.generic import TemplateView

# Streamlit과 동일한 설정
nest_asyncio.apply()

if platform.system() == "Windows":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# 전역 변수 (한 곳에만 정의)
mcp_client = None
mcp_tools = []
agent = None  # ReAct 에이전트
memory_saver = None
event_loop = None

# Streamlit의 SYSTEM_PROMPT와 OUTPUT_TOKEN_INFO
SYSTEM_PROMPT = """<ROLE>
You are a smart agent with an ability to use tools. 
You will be given a question and you will use the tools to answer the question.
Pick the most relevant tool to answer the question. 
If you are failed to answer the question, try different tools to get context.
Your answer should be very polite and professional.
</ROLE>

----

<INSTRUCTIONS>
Step 1: Analyze the question
- Analyze user's question and final goal.
- If the user's question is consist of multiple sub-questions, split them into smaller sub-questions.

Step 2: Pick the most relevant tool
- Pick the most relevant tool to answer the question.
- If you are failed to answer the question, try different tools to get context.

Step 3: Answer the question
- Answer the question in the same language as the question.
- Your answer should be very polite and professional.

Step 4: Provide the source of the answer(if applicable)
- If you've used the tool, provide the source of the answer.
- Valid sources are either a website(URL) or a document(PDF, etc).

Guidelines:
- If you've used the tool, your answer should be based on the tool's output(tool's output is more important than your own knowledge).
- If you've used the tool, and the source is valid URL, provide the source(URL) of the answer.
- Skip providing the source if the source is not URL.
- Answer in the same language as the question.
- Answer should be concise and to the point.
- Avoid response your output with any other information than the answer and the source.  
</INSTRUCTIONS>

----

<OUTPUT_FORMAT>
(concise answer to the question)

**Source**(if applicable)
- (source1: valid URL)
- (source2: valid URL)
- ...
</OUTPUT_FORMAT>
"""

OUTPUT_TOKEN_INFO = {
    "claude-3-5-sonnet-latest": {"max_tokens": 8192},
    "claude-3-5-haiku-latest": {"max_tokens": 8192},
    "claude-3-7-sonnet-latest": {"max_tokens": 64000},
    "gpt-4o": {"max_tokens": 16000},
    "gpt-4o-mini": {"max_tokens": 16000},
}

def get_config_file_path():
    return os.path.join(settings.BASE_DIR, "config.json")

def get_or_create_event_loop():
    """전역 이벤트 루프 생성 및 재사용"""
    global event_loop
    if event_loop is None:
        event_loop = asyncio.new_event_loop()
        asyncio.set_event_loop(event_loop)
    return event_loop

def init_session_state(request):
    """Django 세션 초기화"""
    if 'session_initialized' not in request.session:
        request.session['session_initialized'] = False
        request.session['selected_model'] = 'claude-3-7-sonnet-latest'
        request.session['timeout_seconds'] = 120
        request.session['recursion_limit'] = 100
        request.session['tool_count'] = 0
        request.session['mcp_initialized'] = False
        request.session.save()

def load_config_from_json():
    """config.json 파일에서 설정을 로드합니다."""
    default_config = {
        "get_current_time": {
            "command": "python",
            "args": ["./mcp_server_time.py"],
            "transport": "stdio"
        }
    }
    
    try:
        if os.path.exists(get_config_file_path()):
            with open(get_config_file_path(), "r", encoding="utf-8") as f:
                config = json.load(f)
                print(f"✅ Config loaded: {config}")
                return config
        else:
            print(f"❌ Config file not found at: {get_config_file_path()}")
            save_config_to_json(default_config)
            return default_config
    except Exception as e:
        print(f"❌ 설정 파일 로드 중 오류 발생: {str(e)}")
        return default_config

def save_config_to_json(config):
    """설정을 config.json 파일에 저장합니다."""
    try:
        with open(get_config_file_path(), "w", encoding="utf-8") as f:
            json.dump(config, f, indent=2, ensure_ascii=False)
        print(f"✅ Config saved to {get_config_file_path()}")
        return True
    except Exception as e:
        print(f"❌ 설정 파일 저장 중 오류 발생: {str(e)}")
        return False

async def cleanup_mcp_client():
    """기존 MCP 클라이언트를 안전하게 종료합니다."""
    global mcp_client, mcp_tools, agent, memory_saver
    
    if mcp_client is not None:
        try:
            await mcp_client.__aexit__(None, None, None)
            print("✅ 기존 MCP 클라이언트 정리 완료")
        except Exception as e:
            print(f"⚠️ MCP 클라이언트 종료 중 오류: {str(e)}")
        finally:
            mcp_client = None
            mcp_tools = []
            agent = None
            memory_saver = None

async def initialize_session(mcp_config=None, selected_model=None):
    """
    MCP 세션과 에이전트를 초기화합니다. (Streamlit initialize_session 완전 구현)
    중요: 에이전트 생성 로직 포함 - 중복 제거된 유일한 버전
    """
    global mcp_client, mcp_tools, agent, memory_saver
    
    try:
        print("🔄 MCP 서버 및 에이전트 초기화 중...")
        
        # 먼저 기존 클라이언트를 안전하게 정리
        await cleanup_mcp_client()

        if mcp_config is None:
            mcp_config = load_config_from_json()

        if selected_model:
            print(f"🎯 사용자 선택 모델: {selected_model}")

        # langchain-mcp-adapters 패키지 임포트
        from langchain_mcp_adapters.client import MultiServerMCPClient
        from langgraph.prebuilt import create_react_agent
        from langchain_anthropic import ChatAnthropic
        from langchain_openai import ChatOpenAI
        from langgraph.checkpoint.memory import MemorySaver
        
        # MultiServerMCPClient 생성
        print(f"🔧 MultiServerMCPClient 생성 중...")
        mcp_client = MultiServerMCPClient(mcp_config)
        
        # 도구 목록 가져오기
        print(f"🛠️ 도구 목록 가져오는 중...")
        mcp_tools = await mcp_client.get_tools()
        
        # 선택된 모델에 따라 적절한 모델 초기화 (Streamlit과 동일)
        selected_model = selected_model or 'claude-3-7-sonnet-latest'
        if selected_model in [
            "claude-3-7-sonnet-latest",
            "claude-3-5-sonnet-latest",
            "claude-3-5-haiku-latest",
        ]:
            model = ChatAnthropic(
                model=selected_model,
                temperature=0.1,
                max_tokens=OUTPUT_TOKEN_INFO[selected_model]["max_tokens"],
            )
        else:  # OpenAI 모델 사용
            model = ChatOpenAI(
                model=selected_model,
                temperature=0.1,
                max_tokens=OUTPUT_TOKEN_INFO[selected_model]["max_tokens"],
            )
        
        # ReAct 에이전트 생성 (Streamlit과 동일) - 중요!
        print(f"🤖 ReAct 에이전트 생성 중...")
        memory_saver = MemorySaver()
        agent = create_react_agent(
            model,
            mcp_tools,
            checkpointer=memory_saver,
            prompt=SYSTEM_PROMPT,
        )
        
        tool_count = len(mcp_tools)
        
        print(f"✅ MCP 클라이언트 및 에이전트 초기화 완료: {tool_count}개 도구")
        print(f"✅ 에이전트 생성 완료 - 모델: {selected_model}")
        return True
        
    except ImportError as import_error:
        error_msg = f"필수 패키지 임포트 실패: {str(import_error)}"
        print(f"❌ {error_msg}")
        return False
        
    except Exception as e:
        error_msg = f"에이전트 초기화 오류: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return False

async def process_query_async(query, timeout_seconds=120, recursion_limit=100, thread_id=None):
    """사용자 질문을 처리하고 응답을 생성합니다."""
    global agent
    
    try:
        if agent:
            from utils import astream_graph
            from langchain_core.messages import HumanMessage
            from langchain_core.runnables import RunnableConfig
            
            if thread_id is None:
                import uuid
                thread_id = str(uuid.uuid4())
            
            # Streamlit과 동일한 방식으로 에이전트 실행
            response = await asyncio.wait_for(
                astream_graph(
                    agent,
                    {"messages": [HumanMessage(content=query)]},
                    config=RunnableConfig(
                        recursion_limit=recursion_limit,
                        thread_id=thread_id,
                    ),
                ),
                timeout=timeout_seconds,
            )
            
            return {"success": True, "response": response}
        else:
            return {"success": False, "error": "에이전트가 초기화되지 않았습니다."}
    except asyncio.TimeoutError:
        error_msg = f"⏱️ 요청 시간이 {timeout_seconds}초를 초과했습니다."
        return {"success": False, "error": error_msg}
    except Exception as e:
        error_msg = f"❌ 쿼리 처리 중 오류 발생: {str(e)}"
        print(error_msg)
        import traceback
        traceback.print_exc()
        return {"success": False, "error": error_msg}

class ChatbotView(TemplateView):
    template_name = 'chatbot/chat.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        init_session_state(self.request)
        
        mcp_config = load_config_from_json()
        
        context['mcp_tools'] = [
            {'name': name, 'config': config} 
            for name, config in mcp_config.items()
        ]
        context['available_models'] = [
            'claude-3-7-sonnet-latest',
            'claude-3-5-sonnet-latest',
            'claude-3-5-haiku-latest',
            'gpt-4o',
            'gpt-4o-mini'
        ]
        context['tool_count'] = len(mcp_config)
        context['user_settings'] = {
            'selected_model': self.request.session.get('selected_model', 'claude-3-7-sonnet-latest'),
            'timeout_seconds': self.request.session.get('timeout_seconds', 120),
            'recursion_limit': self.request.session.get('recursion_limit', 100),
            'tool_count': self.request.session.get('tool_count', 0),
        }
        
        return context

@csrf_exempt
@require_http_methods(["POST"])
def apply_settings(request):
    """설정 적용하기 엔드포인트 - 에이전트 생성 포함"""
    try:
        print("🔄 설정 적용 요청 받음...")
        
        init_session_state(request)
        
        request_data = {}
        if request.body:
            try:
                request_data = json.loads(request.body)
            except json.JSONDecodeError:
                pass
        
        selected_model = request_data.get('selected_model')
        timeout_seconds = request_data.get('timeout_seconds')
        recursion_limit = request_data.get('recursion_limit')
        
        if selected_model:
            request.session['selected_model'] = selected_model
            print(f"🎯 세션에 모델 선택 저장: {selected_model}")
        if timeout_seconds:
            request.session['timeout_seconds'] = timeout_seconds
        if recursion_limit:
            request.session['recursion_limit'] = recursion_limit
        
        request.session.save()
        
        current_config = load_config_from_json()
        
        if not current_config:
            return JsonResponse({
                'success': False,
                'error': 'config.json 파일을 로드할 수 없습니다.'
            })
        
        try:
            print(f"🔧 MCP 설정 처리 중: {list(current_config.keys())}")
            
            loop = get_or_create_event_loop()
            current_selected_model = request.session.get('selected_model', 'claude-3-7-sonnet-latest')
            
            # 에이전트 생성이 포함된 initialize_session 호출
            success = loop.run_until_complete(
                initialize_session(current_config, current_selected_model)
            )
            
            if success:
                global mcp_tools, agent
                
                # 에이전트 초기화 확인
                if agent is None:
                    print("❌ 에이전트가 여전히 None입니다!")
                    return JsonResponse({
                        'success': False,
                        'error': '에이전트 생성에 실패했습니다.'
                    })
                else:
                    print("✅ 에이전트 생성 확인됨!")
                
                tool_names = []
                if mcp_tools and len(mcp_tools) > 0:
                    for tool in mcp_tools:
                        try:
                            if hasattr(tool, 'name'):
                                tool_names.append(tool.name)
                            elif hasattr(tool, 'get_name'):
                                tool_names.append(tool.get_name())
                            elif isinstance(tool, dict) and 'name' in tool:
                                tool_names.append(tool['name'])
                            else:
                                tool_names.append(str(tool))
                        except Exception as tool_error:
                            print(f"⚠️ 도구 이름 추출 오류: {str(tool_error)}")
                            continue
                
                if not tool_names:
                    tool_names = list(current_config.keys())
                
                tool_count = len(tool_names)
                
                request.session['tool_count'] = tool_count
                request.session['mcp_initialized'] = True
                request.session['session_initialized'] = True
                request.session.save()
                
                print(f"✅ {tool_count}개 도구 설정 완료: {tool_names}")
                print(f"✅ 현재 선택된 모델: {request.session.get('selected_model')}")
                
                session_info = {
                    'selected_model': request.session.get('selected_model'),
                    'timeout_seconds': request.session.get('timeout_seconds'),
                    'recursion_limit': request.session.get('recursion_limit'),
                    'tool_count': tool_count,
                    'mcp_initialized': True,
                    'session_initialized': True,
                }
                
                return JsonResponse({
                    'success': True,
                    'message': '설정 및 에이전트가 성공적으로 초기화되었습니다.',
                    'tool_count': tool_count,
                    'tools': tool_names,
                    'config': current_config,
                    'user_settings': session_info
                })
            else:
                return JsonResponse({
                    'success': False,
                    'error': 'MCP 클라이언트 및 에이전트 초기화에 실패했습니다.'
                })
            
        except Exception as mcp_error:
            error_msg = f"MCP 설정 적용 실패: {str(mcp_error)}"
            print(f"❌ {error_msg}")
            import traceback
            traceback.print_exc()
            return JsonResponse({
                'success': False,
                'error': error_msg
            })
            
    except Exception as e:
        error_msg = f"설정 적용 중 오류 발생: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        })

@csrf_exempt
@require_http_methods(["POST"])
def chat_message(request):
    """채팅 메시지 처리 엔드포인트"""
    try:
        init_session_state(request)
        
        data = json.loads(request.body)
        user_message = data.get('message', '').strip()
        
        if not user_message:
            return JsonResponse({
                'success': False,
                'error': '메시지를 입력해주세요.'
            })
        
        timeout_seconds = request.session.get('timeout_seconds', 120)
        recursion_limit = request.session.get('recursion_limit', 100)
        
        if 'thread_id' not in request.session:
            import uuid
            request.session['thread_id'] = str(uuid.uuid4())
            request.session.save()
        
        thread_id = request.session['thread_id']
        
        # 에이전트 상태 확인
        global agent
        if agent is None:
            print("❌ 에이전트가 None입니다!")
            return JsonResponse({
                'success': False,
                'error': '에이전트가 초기화되지 않았습니다. "설정 적용하기" 버튼을 먼저 눌러주세요.'
            })
        
        print(f"✅ 에이전트 확인됨. 질문 처리 시작: {user_message}")
        
        loop = get_or_create_event_loop()
        result = loop.run_until_complete(
            process_query_async(user_message, timeout_seconds, recursion_limit, thread_id)
        )
        
        if result['success']:
            response_content = ""
            if 'response' in result and 'content' in result['response']:
                response_content = str(result['response']['content'])
            elif 'response' in result:
                response_content = str(result['response'])
            
            return JsonResponse({
                'success': True,
                'response': response_content,
                'message': result.get('message', '응답이 생성되었습니다.')
            })
        else:
            return JsonResponse({
                'success': False,
                'error': result['error']
            })
            
    except Exception as e:
        error_msg = f"채팅 처리 중 오류 발생: {str(e)}"
        print(f"❌ {error_msg}")
        import traceback
        traceback.print_exc()
        return JsonResponse({
            'success': False,
            'error': error_msg
        })

@csrf_exempt
@require_http_methods(["POST"])
def clear_chat(request):
    """대화 초기화 엔드포인트"""
    try:
        import uuid
        request.session['thread_id'] = str(uuid.uuid4())
        request.session.save()
        
        return JsonResponse({
            'success': True,
            'message': '대화가 초기화되었습니다.'
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["GET", "POST"])
def get_user_settings(request):
    """사용자 설정 정보 조회/업데이트 엔드포인트"""
    init_session_state(request)
    
    if request.method == 'GET':
        user_settings = {
            'selected_model': request.session.get('selected_model', 'claude-3-7-sonnet-latest'),
            'timeout_seconds': request.session.get('timeout_seconds', 120),
            'recursion_limit': request.session.get('recursion_limit', 100),
            'tool_count': request.session.get('tool_count', 0),
            'mcp_initialized': request.session.get('mcp_initialized', False),
            'session_initialized': request.session.get('session_initialized', False),
        }
        
        return JsonResponse({
            'success': True,
            'user_settings': user_settings
        })
    
    elif request.method == 'POST':
        try:
            data = json.loads(request.body)
            
            if 'selected_model' in data:
                request.session['selected_model'] = data['selected_model']
            if 'timeout_seconds' in data:
                request.session['timeout_seconds'] = data['timeout_seconds']
            if 'recursion_limit' in data:
                request.session['recursion_limit'] = data['recursion_limit']
            
            request.session.save()
            
            return JsonResponse({
                'success': True,
                'message': '사용자 설정이 업데이트되었습니다.',
                'user_settings': {
                    'selected_model': request.session.get('selected_model'),
                    'timeout_seconds': request.session.get('timeout_seconds'),
                    'recursion_limit': request.session.get('recursion_limit'),
                }
            })
            
        except Exception as e:
            return JsonResponse({
                'success': False,
                'error': str(e)
            })

@csrf_exempt
@require_http_methods(["POST"])
def save_mcp_config(request):
    """MCP 도구 설정 저장"""
    try:
        data = json.loads(request.body)
        current_config = load_config_from_json()
        
        if isinstance(data, dict):
            if "mcpServers" in data:
                data = data["mcpServers"]
            
            for tool_name, tool_config in data.items():
                if "url" in tool_config:
                    tool_config["transport"] = "sse"
                elif "transport" not in tool_config:
                    tool_config["transport"] = "stdio"
                
                if "command" not in tool_config and "url" not in tool_config:
                    return JsonResponse({
                        'success': False,
                        'error': f"'{tool_name}' 도구 설정에는 'command' 또는 'url' 필드가 필요합니다."
                    })
                elif "command" in tool_config and "args" not in tool_config:
                    return JsonResponse({
                        'success': False,
                        'error': f"'{tool_name}' 도구 설정에는 'args' 필드가 필요합니다."
                    })
                elif "command" in tool_config and not isinstance(tool_config["args"], list):
                    return JsonResponse({
                        'success': False,
                        'error': f"'{tool_name}' 도구의 'args' 필드는 반드시 배열([]) 형식이어야 합니다."
                    })
            
            current_config.update(data)
            
        success = save_config_to_json(current_config)
        
        return JsonResponse({
            'success': success,
            'message': '설정이 저장되었습니다.' if success else '설정 저장에 실패했습니다.',
            'tool_count': len(current_config)
        })
        
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })

@csrf_exempt
@require_http_methods(["POST"])
def initialize_mcp(request):
    """MCP 초기화 엔드포인트"""
    try:
        init_session_state(request)
        
        loop = get_or_create_event_loop()
        config = load_config_from_json()
        success = loop.run_until_complete(initialize_session(config))
        
        tool_names = []
        if success and mcp_tools and len(mcp_tools) > 0:
            for tool in mcp_tools:
                try:
                    if hasattr(tool, 'name'):
                        tool_names.append(tool.name)
                    elif hasattr(tool, 'get_name'):
                        tool_names.append(tool.get_name())
                    elif isinstance(tool, dict) and 'name' in tool:
                        tool_names.append(tool['name'])
                    else:
                        tool_names.append(str(tool))
                except:
                    continue
        
        user_settings = {
            'selected_model': request.session.get('selected_model', 'claude-3-7-sonnet-latest'),
            'timeout_seconds': request.session.get('timeout_seconds', 120),
            'recursion_limit': request.session.get('recursion_limit', 100),
            'tool_count': len(tool_names),
            'mcp_initialized': success,
            'session_initialized': request.session.get('session_initialized', False),
        }
        
        return JsonResponse({
            'success': success,
            'tool_count': len(tool_names),
            'tools': tool_names,
            'user_settings': user_settings
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        })
