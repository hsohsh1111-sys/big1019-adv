"""도구(Tool)를 쓰는 에이전트 - 에이전트 루프를 직접 구현해 원리를 이해한다.

실행:
  uvicorn web:app --reload                                   # 브라우저 → http://127.0.0.1:8000
  python agent.py "오늘 날짜와 12345 * 678 의 결과를 알려줘"     # 터미널
키가 없으면 ScriptedLLM(규칙으로 도구를 고르는 가짜 LLM)이 같은 루프를 따라 동작한다.
"""
import ast
import operator
import re
import sys
from datetime import date

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, ToolMessage
from langchain_core.tools import tool

from llm import gemini_or_none

MAX_STEPS = 5


@tool
def calculator(expression: str) -> str:
    """사칙연산 수식을 정확히 계산한다. 예: '12345 * 678', '(3 + 4) / 2'"""
    ops = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul,
           ast.Div: operator.truediv, ast.Pow: operator.pow, ast.USub: operator.neg}

    def ev(node):  # eval() 대신 숫자와 연산자만 허용하는 안전한 계산
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in ops:
            return ops[type(node.op)](ev(node.operand))
        raise ValueError("허용되지 않은 수식")

    try:
        return str(ev(ast.parse(expression, mode="eval").body))
    except (SyntaxError, ValueError, ZeroDivisionError) as e:
        return f"계산 오류: {e}"  # 도구는 예외 대신 오류 메시지를 돌려줘야 LLM이 다시 시도할 수 있다


@tool
def get_today() -> str:
    """오늘 날짜와 요일을 알려준다."""
    d = date.today()
    return f"{d.isoformat()} ({'월화수목금토일'[d.weekday()]}요일)"


TOOLS = {t.name: t for t in (calculator, get_today)}


class ScriptedLLM:
    """키가 없을 때 쓰는 가짜 LLM. 실제 LLM처럼 tool_calls 를 담은 AIMessage를 돌려준다."""

    def invoke(self, messages):
        results = [m.content for m in messages if isinstance(m, ToolMessage)]
        if results:
            return AIMessage(content="도구 실행 결과를 정리하면: " + " / ".join(results))
        question = messages[-1].content
        calls = []
        if any(w in question for w in ("날짜", "오늘", "요일")):
            calls.append({"name": "get_today", "args": {}, "id": "call_1"})
        exprs = re.findall(r"[\d.()]+(?:\s*(?:\*\*|[-+*/])\s*[\d.()]+)+", question)
        if exprs:
            calls.append({"name": "calculator", "args": {"expression": max(exprs, key=len)}, "id": "call_2"})
        return AIMessage(content="" if calls else "도구 없이 답할 수 있는 질문입니다.", tool_calls=calls)


def text_of(message):
    """모델에 따라 content가 문자열 또는 [{"type": "text", "text": ...}] 목록이라 문자열로 통일."""
    if isinstance(message.content, str):
        return message.content
    return "".join(p.get("text", "") for p in message.content if isinstance(p, dict))


def run_agent(question):
    """에이전트 루프: LLM 호출 → 도구 요청이 있으면 실행 → 결과를 다시 LLM에 → 최종 답변까지 반복.

    반환값 trace 에 단계별 기록을 담아 터미널·브라우저에서 과정을 볼 수 있게 한다.
    """
    real = gemini_or_none(temperature=0)
    llm = real.bind_tools(list(TOOLS.values())) if real else ScriptedLLM()
    trace = {"model": "Gemini + bind_tools" if real else "ScriptedLLM (모의)", "steps": [], "answer": None}

    messages = [SystemMessage("필요하면 도구를 사용해 정확하게 답하라."), HumanMessage(question)]
    for step in range(1, MAX_STEPS + 1):
        ai = llm.invoke(messages)
        messages.append(ai)
        if not ai.tool_calls:
            trace["answer"] = text_of(ai)
            trace["steps"].append({"step": step, "type": "answer", "content": trace["answer"]})
            return trace
        for call in ai.tool_calls:
            selected = TOOLS.get(call["name"])
            result = selected.invoke(call["args"]) if selected else f"알 수 없는 도구: {call['name']}"
            trace["steps"].append({"step": step, "type": "tool", "name": call["name"], "args": call["args"],
                                   "result": result})
            messages.append(ToolMessage(result, tool_call_id=call["id"]))
    trace["answer"] = "최대 단계를 초과했습니다."
    return trace


def main():
    question = " ".join(sys.argv[1:]) or "오늘 날짜와 12345 * 678 의 결과를 알려줘"
    trace = run_agent(question)
    print(f"[모델] {trace['model']}\n질문: {question}\n")
    for s in trace["steps"]:
        if s["type"] == "tool":
            print(f"[{s['step']}단계] 도구 호출 {s['name']}({s['args']}) → {s['result']}")
        else:
            print(f"[{s['step']}단계] 최종 답변 → {s['content']}")


if __name__ == "__main__":
    main()
