"""
Nova AI - Agent Qrafı (LangGraph)
=====================================
Bu, Nova-nın "beynidir". Hər istifadəçi mesajı bu qrafdan keçir:

    [dil aşkarla] -> [yaddaşdan kontekst çək] -> [LLM cavab/tool qərarı] 
        -> (əgər tool lazımdırsa) [plugin icra et] -> [LLM final cavab] -> [yaddaşa yaz]

Tool-çağırma protokolu: Provayderlər arasında native tool-calling API-ləri
fərqli olduğu üçün (OpenAI/Anthropic fərqli formatlar tələb edir), sadə və
provayder-aqnostik yanaşma seçilib: LLM-ə mövcud alətlər sistem promptunda
təsvir edilir və çağırmaq istədikdə ciddi JSON formatında qaytarması xahiş
olunur. Bu, bütün provayderlərlə (lokal modellər daxil) eyni cür işləyir.
"""
from __future__ import annotations

import json
import re

from langgraph.graph import END, StateGraph

from app.agent.language_detector import detect_language, get_system_prompt_language_instruction
from app.agent.state import AgentState
from app.core.logging_config import logger
from app.llm.base import ChatMessage
from app.llm.factory import get_llm_provider
from app.memory.memory_manager import get_memory_manager
from app.plugins.loader import get_plugin_registry

_TOOL_CALL_PATTERN = re.compile(r"```tool_call\s*(\{.*?\})\s*```", re.DOTALL)

_BASE_SYSTEM_PROMPT = """Sənin adın Nova-dır. Sən istifadəçinin şəxsi AI köməkçisisən.
Məqsədin: bilik, karyera, proqramlaşdırma, kibertəhlükəsizlik və şəxsi inkişaf
sahələrində dəqiq, faydalı və dürüst kömək etməkdir.

Qaydalar:
- Faktları istifadəçini razı salmaq üçün əyme, düz danış.
- Bilmədiyini açıq de.
- Qısa və mənalı cavab ver, istəyəndə ətraflı izah et.

Mövcud alətlər (lazım gəldikdə çağıra bilərsən):
{tools_description}

Əgər alət çağırmaq lazımdırsa, YALNIZ aşağıdakı formatda cavab ver (başqa heç nə yazma):
```tool_call
{{"tool": "alət_adı", "arguments": {{"parametr": "dəyər"}}}}
```
Əks halda, adi mətn şəklində birbaşa cavab ver."""


def _build_tools_description() -> str:
    registry = get_plugin_registry()
    schemas = registry.tool_schemas()
    if not schemas:
        return "(hazırda heç bir alət qoşulmayıb)"
    lines = []
    for s in schemas:
        lines.append(f"- {s['name']}: {s['description']}")
    return "\n".join(lines)


async def node_detect_language(state: AgentState) -> AgentState:
    """1. addım: istifadəçi mesajının dilini aşkarlayır."""
    lang = detect_language(state["user_input"])
    logger.debug("Aşkarlanan dil: {}", lang)
    return {**state, "detected_language": lang}


async def node_retrieve_context(state: AgentState) -> AgentState:
    """2. addım: söhbət tarixçəsi + semantik yaddaşdan kontekst toplayır."""
    memory = get_memory_manager()
    context = await memory.build_context_messages(state["conversation_id"], state["user_input"])
    return {**state, "context_messages": context}


async def node_generate(state: AgentState) -> AgentState:
    """3. addım: LLM-i çağırır. Ya birbaşa cavab, ya da tool-call qaytarır."""
    provider = get_llm_provider()
    lang_instruction = get_system_prompt_language_instruction(state["detected_language"])
    system = _BASE_SYSTEM_PROMPT.format(tools_description=_build_tools_description())
    system = f"{system}\n\n{lang_instruction}"

    messages = [ChatMessage(role="system", content=system)]
    messages.extend(state.get("context_messages", []))
    messages.append(ChatMessage(role="user", content=state["user_input"]))

    try:
        response = await provider.generate(messages)
    except Exception as e:
        logger.error("LLM cavab xətası: {}", e)
        return {**state, "error": str(e), "final_response": (
            "Üzr istəyirəm, hazırda AI provayderinə qoşula bilmirəm. "
            "Zəhmət olmasa Settings-dən API açarını/provayderi yoxla."
        )}

    match = _TOOL_CALL_PATTERN.search(response.content)
    if match:
        try:
            tool_data = json.loads(match.group(1))
            return {**state, "tool_calls": [tool_data]}
        except json.JSONDecodeError:
            logger.warning("Tool-call JSON parse edilə bilmədi, adi mətn kimi qəbul edilir")

    return {**state, "final_response": response.content}


async def node_execute_tools(state: AgentState) -> AgentState:
    """4. addım (şərti): LLM alət çağırmaq istəyibsə, plugin-i icra edir."""
    registry = get_plugin_registry()
    results = []
    for call in state.get("tool_calls", []):
        tool_name = call.get("tool", "")
        args = call.get("arguments", {})
        try:
            result = await registry.execute(tool_name, **args)
        except Exception as e:
            result = f"Alət icrası uğursuz oldu: {e}"
        results.append(f"[{tool_name}] {result}")
    return {**state, "tool_results": results}


async def node_finalize_with_tools(state: AgentState) -> AgentState:
    """5. addım: alət nəticələrini LLM-ə göstərib son, insan-oxunaqlı cavab alır."""
    provider = get_llm_provider()
    tool_results_text = "\n".join(state.get("tool_results", []))
    lang_instruction = get_system_prompt_language_instruction(state["detected_language"])

    messages = [
        ChatMessage(
            role="system",
            content=f"Alət nəticələrinə əsasən istifadəçiyə təbii dildə cavab ver. {lang_instruction}",
        ),
        ChatMessage(role="user", content=state["user_input"]),
        ChatMessage(role="assistant", content=f"Alət nəticələri:\n{tool_results_text}"),
    ]
    try:
        response = await provider.generate(messages)
        return {**state, "final_response": response.content}
    except Exception as e:
        logger.error("Final cavab xətası: {}", e)
        return {**state, "final_response": tool_results_text or "Xəta baş verdi."}


async def node_save_to_memory(state: AgentState) -> AgentState:
    """6. addım: user+assistant mesajlarını yaddaşa yazır."""
    memory = get_memory_manager()
    await memory.save_message(
        state["conversation_id"], "user", state["user_input"], language=state["detected_language"]
    )
    await memory.save_message(
        state["conversation_id"], "assistant", state["final_response"], language=state["detected_language"]
    )
    return state


def _route_after_generate(state: AgentState) -> str:
    """Şərti kənar: tool-call varsa icra qoluna, yoxdursa birbaşa yadda-saxlama qoluna get."""
    return "execute_tools" if state.get("tool_calls") else "save_to_memory"


def build_agent_graph():
    """LangGraph StateGraph-ı qurur və compile edir."""
    graph = StateGraph(AgentState)

    graph.add_node("detect_language", node_detect_language)
    graph.add_node("retrieve_context", node_retrieve_context)
    graph.add_node("generate", node_generate)
    graph.add_node("execute_tools", node_execute_tools)
    graph.add_node("finalize_with_tools", node_finalize_with_tools)
    graph.add_node("save_to_memory", node_save_to_memory)

    graph.set_entry_point("detect_language")
    graph.add_edge("detect_language", "retrieve_context")
    graph.add_edge("retrieve_context", "generate")
    graph.add_conditional_edges(
        "generate",
        _route_after_generate,
        {"execute_tools": "execute_tools", "save_to_memory": "save_to_memory"},
    )
    graph.add_edge("execute_tools", "finalize_with_tools")
    graph.add_edge("finalize_with_tools", "save_to_memory")
    graph.add_edge("save_to_memory", END)

    return graph.compile()


_compiled_graph = None


def get_agent():
    """Compiled graph-ın singleton instansı."""
    global _compiled_graph
    if _compiled_graph is None:
        _compiled_graph = build_agent_graph()
    return _compiled_graph


async def run_agent(conversation_id: str, user_input: str) -> str:
    """Xarici modullar (API, GUI) üçün sadə giriş nöqtəsi."""
    agent = get_agent()
    result: AgentState = await agent.ainvoke(
        {"conversation_id": conversation_id, "user_input": user_input}
    )
    return result.get("final_response", "Cavab formalaşdırıla bilmədi.")
