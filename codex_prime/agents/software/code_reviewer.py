"""Code review agent for analyzing code quality."""

from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent, AgentCapability, AgentResponse


class CodeReviewerAgent(BaseAgent):
    """Agent specialized in code review and quality analysis."""

    def __init__(self, provider=None, tools_registry=None):
        super().__init__(
            name="CodeReviewer",
            capabilities=[
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.REVIEW,
                AgentCapability.DOCUMENTATION
            ],
            provider=provider,
            tools_registry=tools_registry
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for code reviewer."""
        return """You are an expert code reviewer with deep knowledge of software engineering best practices.

Your responsibilities:
1. Analyze code for potential bugs, security issues, and performance problems
2. Check adherence to coding standards and best practices
3. Suggest improvements for readability and maintainability
4. Identify missing edge cases and error handling
5. Recommend better design patterns where applicable

Review Criteria:
- **Correctness**: Does the code work as intended?
- **Security**: Are there any security vulnerabilities?
- **Performance**: Any performance bottlenecks?
- **Readability**: Is the code easy to understand?
- **Maintainability**: Will this be easy to modify later?
- **Testing**: Is the code testable? Are tests present?

Format your response as:
## Summary
[Brief overall assessment]

## Issues Found
[List specific issues with severity: CRITICAL, HIGH, MEDIUM, LOW]

## Suggestions
[Concrete improvement recommendations]

## Positive Aspects
[What the code does well]

Be direct, specific, and constructive. Focus on actionable feedback."""

    def process(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Review code and provide feedback.

        Args:
            task: Code to review
            context: Optional context (file path, language, etc.)

        Returns:
            AgentResponse with review feedback
        """
        # Build context
        review_context = context or {}

        # Prepare prompt
        messages = self._build_messages(task, review_context)

        # Get review from LLM
        if self.provider:
            review = self._call_llm(messages, temperature=0.2)
        else:
            # Fallback: basic analysis
            review = self._basic_review(task)

        # Extract suggestions
        suggestions = self._extract_suggestions(review)

        # Calculate confidence (simple heuristic)
        confidence = 0.8 if self.provider else 0.5

        return AgentResponse(
            content=review,
            confidence=confidence,
            suggestions=suggestions,
            metadata={
                "agent": self.name,
                "language": review_context.get("language", "unknown")
            }
        )

    def _basic_review(self, code: str) -> str:
        """Basic code review without LLM."""
        issues = []

        # Simple heuristics
        if "TODO" in code or "FIXME" in code:
            issues.append("- LOW: Code contains TODO/FIXME comments")

        if "password" in code.lower() or "secret" in code.lower():
            issues.append("- HIGH: Potential hardcoded credentials detected")

        if len(code.split("\n")) > 500:
            issues.append("- MEDIUM: Function/file is quite long, consider breaking it up")

        if not issues:
            issues.append("- No obvious issues detected (limited static analysis)")

        return f"""## Summary
Basic static analysis complete.

## Issues Found
{chr(10).join(issues)}

## Suggestions
- Consider running full code review with LLM provider configured
- Add automated linting tools (pylint, ruff, etc.)
- Ensure unit tests are present

## Note
This is a basic review. Configure an LLM provider for deeper analysis."""

    def _extract_suggestions(self, review: str) -> List[str]:
        """Extract specific suggestions from review text."""
        suggestions = []

        # Look for suggestion sections
        if "## Suggestions" in review:
            parts = review.split("## Suggestions")
            if len(parts) > 1:
                suggestion_text = parts[1].split("##")[0]
                # Extract bullet points
                for line in suggestion_text.split("\n"):
                    line = line.strip()
                    if line.startswith("-") or line.startswith("*"):
                        suggestions.append(line.lstrip("-*").strip())

        return suggestions[:5]  # Top 5 suggestions
