import json
import asyncio
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import openai
from datetime import datetime
from dotenv import load_dotenv
import os


load_dotenv()
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

class EvaluationCriteria(Enum):
    ACCURACY = "accuracy"
    RELEVANCE = "relevance"
    COMPLETENESS = "completeness"
    CLARITY = "clarity"
    HELPFULNESS = "helpfulness"
    SAFETY = "safety"

@dataclass
class EvaluationResult:
    criteria: EvaluationCriteria
    score: float  # 1-10 scale
    reasoning: str
    timestamp: datetime

@dataclass
class JudgeResponse:
    overall_score: float
    criteria_scores: Dict[EvaluationCriteria, EvaluationResult]
    summary: str
    strengths: List[str]
    weaknesses: List[str]

class LLMJudge:
    def __init__(self, api_key: str, model: str = "gpt-4"):
        """
        LLM-as-a-Judge 평가자 초기화
        
        Args:
            api_key: OpenAI API 키
            model: 평가에 사용할 모델
        """
        self.client = openai.OpenAI(api_key=api_key)
        self.model = model
    
    def create_evaluation_prompt(
        self, 
        question: str, 
        answer: str, 
        criteria: List[EvaluationCriteria],
        reference_answer: Optional[str] = None
    ) -> str:
        """평가를 위한 프롬프트 생성"""
        
        criteria_descriptions = {
            EvaluationCriteria.ACCURACY: "정확성 - 답변이 사실적으로 정확한가?",
            EvaluationCriteria.RELEVANCE: "관련성 - 답변이 질문과 얼마나 관련이 있는가?",
            EvaluationCriteria.COMPLETENESS: "완전성 - 답변이 질문을 충분히 다루고 있는가?",
            EvaluationCriteria.CLARITY: "명확성 - 답변이 이해하기 쉽고 명확한가?",
            EvaluationCriteria.HELPFULNESS: "도움성 - 답변이 사용자에게 실질적으로 도움이 되는가?",
            EvaluationCriteria.SAFETY: "안전성 - 답변이 해롭거나 부적절한 내용을 포함하지 않는가?"
        }
        
        criteria_list = "\n".join([f"- {criteria_descriptions[c]}" for c in criteria])
        
        reference_section = ""
        if reference_answer:
            reference_section = f"\n참조 답변:\n{reference_answer}\n"
        
        prompt = f"""
당신은 AI 시스템의 답변을 평가하는 전문 평가자입니다. 다음 질문에 대한 AI의 답변을 평가해주세요.

질문:
{question}

AI 답변:
{answer}
{reference_section}
평가 기준:
{criteria_list}

각 기준에 대해 1-10점으로 평가하고, 다음 JSON 형식으로 응답해주세요:

{{
    "overall_score": <전체 점수 (1-10)>,
    "criteria_scores": {{
        "{criteria[0].value}": {{
            "score": <점수>,
            "reasoning": "<평가 이유>"
        }},
        ...
    }},
    "summary": "<전체 평가 요약>",
    "strengths": ["<강점1>", "<강점2>", ...],
    "weaknesses": ["<약점1>", "<약점2>", ...]
}}

평가 시 고려사항:
1. 객관적이고 공정한 평가
2. 구체적인 근거 제시
3. 건설적인 피드백 제공
4. 문맥과 의도 고려
"""
        return prompt
    
    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        criteria: List[EvaluationCriteria] = None,
        reference_answer: Optional[str] = None,
        temperature: float = 0.1
    ) -> JudgeResponse:
        """
        LLM 답변을 평가
        
        Args:
            question: 원본 질문
            answer: 평가할 답변
            criteria: 평가 기준 목록
            reference_answer: 참조 답변 (선택사항)
            temperature: 모델 온도 설정
            
        Returns:
            JudgeResponse: 평가 결과
        """
        if criteria is None:
            criteria = list(EvaluationCriteria)
        
        prompt = self.create_evaluation_prompt(question, answer, criteria, reference_answer)
        
        try:
            response = await asyncio.to_thread(
                self.client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=temperature,
                max_tokens=2000
            )
            
            result_text = response.choices[0].message.content
            result_json = json.loads(result_text)
            
            # 결과 파싱
            criteria_scores = {}
            for criterion_name, score_data in result_json["criteria_scores"].items():
                criterion = EvaluationCriteria(criterion_name)
                criteria_scores[criterion] = EvaluationResult(
                    criteria=criterion,
                    score=score_data["score"],
                    reasoning=score_data["reasoning"],
                    timestamp=datetime.now()
                )
            
            return JudgeResponse(
                overall_score=result_json["overall_score"],
                criteria_scores=criteria_scores,
                summary=result_json["summary"],
                strengths=result_json["strengths"],
                weaknesses=result_json["weaknesses"]
            )
            
        except Exception as e:
            raise Exception(f"평가 중 오류 발생: {str(e)}")
    
    async def batch_evaluate(
        self,
        evaluations: List[Tuple[str, str, Optional[str]]],  # (question, answer, reference)
        criteria: List[EvaluationCriteria] = None
    ) -> List[JudgeResponse]:
        """여러 답변을 일괄 평가"""
        tasks = []
        for question, answer, reference in evaluations:
            task = self.evaluate_answer(question, answer, criteria, reference)
            tasks.append(task)
        
        return await asyncio.gather(*tasks)
    
    def compare_answers(
        self,
        question: str,
        answer_a: str,
        answer_b: str,
        criteria: List[EvaluationCriteria] = None
    ) -> str:
        """두 답변을 비교하는 프롬프트 생성"""
        if criteria is None:
            criteria = list(EvaluationCriteria)
        
        criteria_list = "\n".join([f"- {c.value}" for c in criteria])
        
        prompt = f"""
다음 질문에 대한 두 개의 AI 답변을 비교하고 평가해주세요.

질문:
{question}

답변 A:
{answer_a}

답변 B:
{answer_b}

평가 기준:
{criteria_list}

다음 항목들을 포함하여 비교 분석해주세요:
1. 각 답변의 장단점
2. 어느 답변이 더 우수한지와 그 이유
3. 개선 제안사항
4. 전체적인 평가 점수 (A: X/10, B: Y/10)
"""
        return prompt

class EvaluationReport:
    """평가 결과 리포트 생성"""
    
    @staticmethod
    def generate_report(results: List[JudgeResponse], questions: List[str]) -> str:
        """평가 결과 종합 리포트 생성"""
        total_questions = len(results)
        avg_score = sum(r.overall_score for r in results) / total_questions
        
        # 기준별 평균 점수 계산
        criteria_averages = {}
        for criterion in EvaluationCriteria:
            scores = []
            for result in results:
                if criterion in result.criteria_scores:
                    scores.append(result.criteria_scores[criterion].score)
            if scores:
                criteria_averages[criterion] = sum(scores) / len(scores)
        
        # 공통 강점/약점 분석
        all_strengths = []
        all_weaknesses = []
        for result in results:
            all_strengths.extend(result.strengths)
            all_weaknesses.extend(result.weaknesses)
        
        report = f"""
# LLM 답변 평가 종합 리포트

## 전체 통계
- 평가된 질문 수: {total_questions}
- 전체 평균 점수: {avg_score:.2f}/10

## 기준별 평균 점수
"""
        for criterion, avg in criteria_averages.items():
            report += f"- {criterion.value}: {avg:.2f}/10\n"
        
        report += f"""
## 주요 강점 (빈도순)
"""
        from collections import Counter
        strength_counts = Counter(all_strengths)
        for strength, count in strength_counts.most_common(5):
            report += f"- {strength} ({count}회 언급)\n"
        
        report += f"""
## 개선 필요 영역 (빈도순)
"""
        weakness_counts = Counter(all_weaknesses)
        for weakness, count in weakness_counts.most_common(5):
            report += f"- {weakness} ({count}회 언급)\n"
        
        report += """
## 개별 질문 평가 결과
"""
        for i, (question, result) in enumerate(zip(questions, results), 1):
            report += f"""
### 질문 {i}: {question[:50]}...
- 점수: {result.overall_score}/10
- 요약: {result.summary}
"""
        
        return report

# 사용 예시
async def main():
    # LLM Judge 초기화
    judge = LLMJudge(api_key=OPENAI_API_KEY)
    
    # 단일 답변 평가
    question = "**Role & Context:**\n당신은 10년 이상의 경험을 보유한 조직 개발 전문가이자 멘토링 프로그램 매니저입니다. 귀하는 신입 직원 온보딩 프로그램 설계/운영, 객관적 성과 평가, 인재 개발 전략 수립에 전문성을 가지고 있습니다. 현재 멘티의 온보딩 과정 완료 시점에서 멘토에게 제공할 종합 평가 보고서 작성을 담당하고 있습니다.\n\n**Task:**\n멘티의 온보딩 기간 중 수행한 태스크 기록을 바탕으로 체계적이고 객관적인 평가 보고서를 작성하세요."
    answer = """
    멘티의 온보딩 기간 중 수행한 태스크 기록을 바탕으로 체계적이고 객관적인 평가 보고서를 작성하세요.", "1. **전반적인 온보딩 진행 상황 평가**: 박정호 멘티는 5개의 작업 중 2개를 완료하였으며, 현재 3개 작업이 진행 중입니다. 전반적으로 온보딩 과정에서의 참여도는 높으며, 각 작업의 목표를 명확히 이해하고 있습니다. 특히 모바일 앱 개발 작업에 서 성과를 잘 나타내고 있습니다.\n2. **작업 수행 능력 및 성장 패턴 분석**: 멘티는 상급 난이도의 모바일 앱 개발 작업을 성공적으로 완료하며 180 경험치를 획득했습니다. 이는 멘티의 기술적 역량과 문제 해결 능력이 뛰어남을 보여줍니다. 현재 진행 중인 작업에서도 적극적으로 기술 조사를 진행하고 있으며, 코드 리뷰를 통해 지속적으로 개선하고 있습니다.\n3. **메모를 통해 나타나는 학습 태도 및 문제 해결 능력**: 박정호 멘티는 각 작업의 진행 상황을 상세히 기록하며, 문제 발생 시 즉각적으로 대응하고 있습니다. 예를 들어, 코드 리뷰에서 발견된 이슈를 신속하게 수정하는 모습을 보였으며, 이는 그의 학습 태도가 적극적임을 나타냅니다.\n4. **강점과 개선이 필요한 영역**: 강점으로는 기술적 역량, 문제 해결 능력, 그리고 적극적인 커뮤니케이션이 있습니다. 반면, 개선이 필요한 영역은 시간 관리 및 작업 우선순위 설정입니다. 현재 진행 중인 작업이 많아 일정 관리에 어려움을 겪고 있는 것으로 보입니다.\n5. **향후 발전 방향 및 권장사항**: 박정호 멘티는 기술적 역량을 더욱 발전시키기 위해 다양한 프로젝트에 참여하는 것이 좋습니다. 또한, 멘토와의 정기적인 피드백 세션을 통해 시간 관리 및 우선순위 설정에 대한 조언을 받는 것을 권장합니다. 이를 통해 멘티는 더욱 효과적으로 온보딩 과정을 마무리하고, 조직 내에서의 성과를 극대화할 수 있을 것입니다.."
    """
    
    # 평가 실행
    result = await judge.evaluate_answer(
        question=question,
        answer=answer,
        criteria=[
            EvaluationCriteria.ACCURACY,
            EvaluationCriteria.COMPLETENESS,
            EvaluationCriteria.CLARITY
        ]
    )
    
    print(f"전체 점수: {result.overall_score}/10")
    print(f"요약: {result.summary}")
    
    # 기준별 점수 출력
    for criterion, eval_result in result.criteria_scores.items():
        print(f"{criterion.value}: {eval_result.score}/10 - {eval_result.reasoning}")
    
    # 일괄 평가 예시
    evaluations = [
        ("멘티의 온보딩 기간 중 수행한 태스크 기록을 바탕으로 체계적이고 객관적인 평가 보고서를 작성하세요.", "1. **전반적인 온보딩 진행 상황 평가**: 박정호 멘티는 5개의 작업 중 2개를 완료하였으며, 현재 3개 작업이 진행 중입니다. 전반적으로 온보딩 과정에서의 참여도는 높으며, 각 작업의 목표를 명확히 이해하고 있습니다. 특히 모바일 앱 개발 작업에 서 성과를 잘 나타내고 있습니다.\n2. **작업 수행 능력 및 성장 패턴 분석**: 멘티는 상급 난이도의 모바일 앱 개발 작업을 성공적으로 완료하며 180 경험치를 획득했습니다. 이는 멘티의 기술적 역량과 문제 해결 능력이 뛰어남을 보여줍니다. 현재 진행 중인 작업에서도 적극적으로 기술 조사를 진행하고 있으며, 코드 리뷰를 통해 지속적으로 개선하고 있습니다.\n3. **메모를 통해 나타나는 학습 태도 및 문제 해결 능력**: 박정호 멘티는 각 작업의 진행 상황을 상세히 기록하며, 문제 발생 시 즉각적으로 대응하고 있습니다. 예를 들어, 코드 리뷰에서 발견된 이슈를 신속하게 수정하는 모습을 보였으며, 이는 그의 학습 태도가 적극적임을 나타냅니다.\n4. **강점과 개선이 필요한 영역**: 강점으로는 기술적 역량, 문제 해결 능력, 그리고 적극적인 커뮤니케이션이 있습니다. 반면, 개선이 필요한 영역은 시간 관리 및 작업 우선순위 설정입니다. 현재 진행 중인 작업이 많아 일정 관리에 어려움을 겪고 있는 것으로 보입니다.\n5. **향후 발전 방향 및 권장사항**: 박정호 멘티는 기술적 역량을 더욱 발전시키기 위해 다양한 프로젝트에 참여하는 것이 좋습니다. 또한, 멘토와의 정기적인 피드백 세션을 통해 시간 관리 및 우선순위 설정에 대한 조언을 받는 것을 권장합니다. 이를 통해 멘티는 더욱 효과적으로 온보딩 과정을 마무리하고, 조직 내에서의 성과를 극대화할 수 있을 것입니다..", None),
        ("머신러닝이란?", "머신러닝은 AI의 한 분야로 데이터로부터 학습하는 기술입니다.", None)
    ]
    
    batch_results = await judge.batch_evaluate(evaluations)
    
    # 리포트 생성
    questions = [eval[0] for eval in evaluations]
    report = EvaluationReport.generate_report(batch_results, questions)
    print(report)

if __name__ == "__main__":
    asyncio.run(main())