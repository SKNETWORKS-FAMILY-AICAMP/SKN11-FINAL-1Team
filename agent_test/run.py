from langgraph.graph import StateGraph
from alarm_agent import alarm_agent_node

# 1. 상태 스키마 정의
state_schema = dict

# 2. LangGraph 구성
graph = StateGraph(state_schema)
graph.add_node("alarm_agent", alarm_agent_node)
graph.set_entry_point("alarm_agent")
graph.set_finish_point("alarm_agent")

workflow = graph.compile()

# 3. 테스트 실행
test_state = {
    "mentee_id": 2,
    "report_url": "https://example.com/report/123"
}

print("🚀 LangGraph 실행 중...")
result = workflow.invoke(test_state)
print("✅ 완료\n결과:", result)
