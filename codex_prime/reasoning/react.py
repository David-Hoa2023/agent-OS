"""ReAct (Reason + Act) pattern for tool-augmented reasoning."""

from typing import Dict, Any, List, Optional


class ReActAgent:
    """Agent using Reason → Act → Observe loop."""

    def __init__(self, provider=None, tools_registry=None, max_iterations: int = 5):
        """
        Initialize ReAct agent.

        Args:
            provider: LLM provider
            tools_registry: Tool registry for actions
            max_iterations: Maximum ReAct iterations
        """
        self.provider = provider
        self.tools_registry = tools_registry
        self.max_iterations = max_iterations

    def solve(
        self,
        task: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Solve task using ReAct loop.

        Args:
            task: Task to solve
            context: Optional context

        Returns:
            Solution with reasoning and action trace
        """
        if not self.provider:
            return self._basic_solve(task)

        trace = []
        iteration = 0

        while iteration < self.max_iterations:
            iteration += 1

            # Reason: What should I do next?
            reasoning = self._reason(task, trace, context)
            trace.append({"type": "thought", "content": reasoning})

            # Check if done
            if self._is_complete(reasoning):
                break

            # Act: Execute an action
            action = self._decide_action(reasoning, trace)
            if not action:
                break

            trace.append({"type": "action", "content": action})

            # Observe: Get action result
            observation = self._execute_action(action)
            trace.append({"type": "observation", "content": observation})

        # Final answer
        final_answer = self._synthesize_answer(task, trace)

        return {
            "task": task,
            "trace": trace,
            "answer": final_answer,
            "iterations": iteration
        }

    def _reason(
        self,
        task: str,
        trace: List[Dict[str, Any]],
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Reason about what to do next."""
        prompt_parts = [f"Task: {task}", ""]

        if context:
            prompt_parts.append("Context: " + str(context))
            prompt_parts.append("")

        if trace:
            prompt_parts.append("Previous steps:")
            for step in trace:
                prompt_parts.append(f"- {step['type']}: {step['content']}")
            prompt_parts.append("")

        prompt_parts.append("What should I do next? Think step by step.")

        prompt = "\n".join(prompt_parts)

        response = self.provider.chat(
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        return response

    def _get_system_prompt(self) -> str:
        """Get system prompt for ReAct."""
        available_tools = ""
        if self.tools_registry:
            tools = self.tools_registry.list_enabled()
            available_tools = "\n".join(f"- {t.name}: {t.description}" for t in tools)

        return f"""You are a ReAct agent using Reason → Act → Observe loop.

Available tools:
{available_tools if available_tools else "No tools available"}

For each step:
1. THINK: Reason about what you know and what you need
2. ACT: Choose an action (use a tool or provide final answer)
3. OBSERVE: See the result and update your understanding

Format your reasoning clearly:
Thought: [Your reasoning]
Action: [Tool to use or FINAL_ANSWER]
"""

    def _is_complete(self, reasoning: str) -> bool:
        """Check if task is complete."""
        complete_markers = [
            "FINAL_ANSWER",
            "task is complete",
            "have the answer",
            "conclusion:"
        ]
        reasoning_lower = reasoning.lower()
        return any(marker in reasoning_lower for marker in complete_markers)

    def _decide_action(
        self,
        reasoning: str,
        trace: List[Dict[str, Any]]
    ) -> Optional[Dict[str, Any]]:
        """Decide which action to take based on reasoning."""
        if "Action:" in reasoning:
            action_part = reasoning.split("Action:")[1].split("\n")[0].strip()

            # Parse tool name and params
            if "(" in action_part:
                tool_name = action_part.split("(")[0].strip()
                return {"tool": tool_name, "params": {}}
            else:
                return {"tool": action_part, "params": {}}

        return None

    def _execute_action(self, action: Dict[str, Any]) -> str:
        """Execute an action and return observation."""
        if not self.tools_registry:
            return "No tools available"

        tool_name = action.get("tool")
        params = action.get("params", {})

        result = self.tools_registry.execute(tool_name, **params)

        if result.get("success"):
            return str(result.get("result"))
        else:
            return f"Error: {result.get('error')}"

    def _synthesize_answer(self, task: str, trace: List[Dict[str, Any]]) -> str:
        """Synthesize final answer from trace."""
        if not self.provider:
            return "Configure LLM provider for detailed answers"

        trace_text = "\n".join(
            f"{step['type'].upper()}: {step['content']}"
            for step in trace
        )

        prompt = f"""Task: {task}

Reasoning trace:
{trace_text}

Based on this trace, what is the final answer to the task?"""

        return self.provider.chat(
            system="Synthesize the final answer from the reasoning trace.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )

    def _basic_solve(self, task: str) -> Dict[str, Any]:
        """Basic solve without LLM."""
        return {
            "task": task,
            "trace": [
                {"type": "thought", "content": "Need LLM provider"},
                {"type": "action", "content": "Configure provider"},
                {"type": "observation", "content": "No provider available"}
            ],
            "answer": "Configure LLM provider for ReAct reasoning",
            "iterations": 1
        }
