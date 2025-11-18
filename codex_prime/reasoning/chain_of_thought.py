"""Chain-of-Thought reasoning for structured problem solving."""

from typing import List, Dict, Any, Optional


class ChainOfThought:
    """Implement chain-of-thought reasoning."""

    def __init__(self, provider=None):
        """
        Initialize CoT reasoner.

        Args:
            provider: LLM provider for generation
        """
        self.provider = provider

    def reason(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None,
        max_steps: int = 5
    ) -> Dict[str, Any]:
        """
        Apply chain-of-thought reasoning to a problem.

        Args:
            problem: Problem to solve
            context: Optional context
            max_steps: Maximum reasoning steps

        Returns:
            Dictionary with reasoning chain and conclusion
        """
        if not self.provider:
            return self._basic_reasoning(problem)

        # Build CoT prompt
        prompt = self._build_cot_prompt(problem, context)

        # Get structured reasoning
        response = self.provider.chat(
            system=self._get_system_prompt(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )

        # Parse response
        steps = self._parse_reasoning_steps(response)

        return {
            "problem": problem,
            "reasoning_steps": steps,
            "conclusion": steps[-1] if steps else "Unable to reach conclusion",
            "confidence": self._calculate_confidence(steps)
        }

    def _get_system_prompt(self) -> str:
        """Get system prompt for CoT."""
        return """You are an expert problem solver using chain-of-thought reasoning.

For each problem:
1. Break it down into logical steps
2. Reason through each step explicitly
3. Show your work and thinking
4. Reach a well-supported conclusion

Format your response as:
Step 1: [First reasoning step]
Step 2: [Second reasoning step]
...
Conclusion: [Final answer with confidence level]

Think step-by-step and be explicit about your reasoning process."""

    def _build_cot_prompt(self, problem: str, context: Optional[Dict[str, Any]] = None) -> str:
        """Build chain-of-thought prompt."""
        prompt_parts = ["Problem:", problem, ""]

        if context:
            prompt_parts.append("Context:")
            for key, value in context.items():
                prompt_parts.append(f"- {key}: {value}")
            prompt_parts.append("")

        prompt_parts.append("Please solve this problem using step-by-step reasoning:")

        return "\n".join(prompt_parts)

    def _parse_reasoning_steps(self, response: str) -> List[str]:
        """Parse reasoning steps from response."""
        steps = []
        lines = response.split("\n")

        for line in lines:
            line = line.strip()
            if line.startswith("Step") or line.startswith("Conclusion"):
                # Extract the reasoning part
                if ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        steps.append(parts[1].strip())

        return steps

    def _calculate_confidence(self, steps: List[str]) -> float:
        """Calculate confidence based on reasoning quality."""
        if not steps:
            return 0.0

        # Simple heuristic: more steps with detail = higher confidence
        avg_length = sum(len(s) for s in steps) / len(steps)
        confidence = min(0.5 + (len(steps) * 0.1) + (avg_length / 1000), 0.95)

        return confidence

    def _basic_reasoning(self, problem: str) -> Dict[str, Any]:
        """Basic reasoning without LLM."""
        return {
            "problem": problem,
            "reasoning_steps": [
                "Identify the problem type",
                "Break down into sub-problems",
                "Solve each sub-problem",
                "Synthesize solution"
            ],
            "conclusion": "Configure LLM provider for detailed reasoning",
            "confidence": 0.3
        }
