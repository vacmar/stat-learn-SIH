from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, SystemMessage

from app.personas.prompts import (
    PATHWAY_REASONER_SYSTEM_PROMPT,
    PROJECT_MENTOR_SYSTEM_PROMPT,
    TUTOR_SYSTEM_PROMPT,
)
from app.tools.backend_client import backend_client


class ContextBuilder:
    """Constructs token-budgeted, state-grounded message sequences for LLM invocations."""

    def __init__(self, backend_cli=None):
        self.backend = backend_cli or backend_client

    async def build_messages(
        self,
        persona: str,
        user_message: str,
        learner_id: str = "learner_01",
        node_id: str | None = None,
        conversation_id: str | None = None,
        role_id: str | None = None,
        history: list[dict[str, str]] | None = None,
    ) -> list[BaseMessage]:
        # 1. Select persona base prompt
        if persona == "pathway_reasoner":
            base_prompt = PATHWAY_REASONER_SYSTEM_PROMPT
        elif persona == "project_mentor":
            base_prompt = PROJECT_MENTOR_SYSTEM_PROMPT
        else:
            base_prompt = TUTOR_SYSTEM_PROMPT

        # 2. Gather state context
        state_lines: list[str] = [f"Learner ID: {learner_id}"]

        if node_id:
            node_state = await self.backend.get_learning_node_state(node_id)
            weak_concepts = await self.backend.get_weak_concepts(learner_id, node_id)
            state_lines.append(
                f"Active Course/Node: {node_state.get('course_title', node_id)}"
            )
            state_lines.append(
                f"Current Module: {node_state.get('current_module', 'General')}"
            )
            state_lines.append(
                f"Current Concept: {node_state.get('current_concept', 'Overview')}"
            )
            state_lines.append(
                f"Progress: {node_state.get('progress_percentage', 0.0)}%"
            )
            if weak_concepts:
                weak_names = [
                    c.get("concept", "") for c in weak_concepts if c.get("concept")
                ]
                state_lines.append(f"Target Weak Concepts: {', '.join(weak_names)}")

        if role_id:
            state_lines.append(f"Target Career Role: {role_id}")

        summary_text = ""
        recent_context_msgs: list[BaseMessage] = []
        if conversation_id:
            conv_data = await self.backend.get_conversation_context(
                conversation_id, limit=5
            )
            summary_text = conv_data.get("summary", "")
            for m in conv_data.get("recent_messages", []):
                role = m.get("role")
                content = m.get("content", "")
                if role == "user":
                    recent_context_msgs.append(HumanMessage(content=content))
                elif role == "assistant":
                    recent_context_msgs.append(AIMessage(content=content))

        if summary_text:
            state_lines.append(f"Prior Conversation Summary: {summary_text}")

        # 3. Assemble system message with grounded state block
        state_block = "\n".join(state_lines)
        full_system_text = (
            f"{base_prompt}\n\n[AUTHORITATIVE STATE CONTEXT]\n{state_block}"
        )
        messages: list[BaseMessage] = [SystemMessage(content=full_system_text)]

        # 4. Append historical context messages (from caller or backend)
        if history:
            for item in history[-6:]:  # Cap recent history window
                role = item.get("role")
                content = item.get("content", "")
                if role == "user":
                    messages.append(HumanMessage(content=content))
                elif role == "assistant":
                    messages.append(AIMessage(content=content))
        elif recent_context_msgs:
            messages.extend(recent_context_msgs)

        # 5. Append latest user message
        messages.append(HumanMessage(content=user_message))

        return messages


context_builder = ContextBuilder()
