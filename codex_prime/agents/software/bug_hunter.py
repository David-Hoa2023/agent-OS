"""Bug hunting agent for finding potential bugs in code."""

from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent, AgentCapability, AgentResponse
import re


class BugHunterAgent(BaseAgent):
    """Agent specialized in finding bugs and edge cases."""

    def __init__(self, provider=None, tools_registry=None):
        super().__init__(
            name="BugHunter",
            capabilities=[
                AgentCapability.CODE_ANALYSIS,
                AgentCapability.TESTING
            ],
            provider=provider,
            tools_registry=tools_registry
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for bug hunter."""
        return """You are an expert bug hunter and security analyst with a keen eye for edge cases.

Your mission:
1. Find potential bugs, crashes, and undefined behavior
2. Identify missing input validation and error handling
3. Spot race conditions and concurrency issues
4. Detect memory leaks and resource management problems
5. Find security vulnerabilities (SQL injection, XSS, etc.)
6. Identify edge cases that might break the code

Analysis Focus:
- **Null/None Handling**: Are null/none values handled properly?
- **Boundary Conditions**: What happens with empty inputs, max values?
- **Error Handling**: Are exceptions caught and handled appropriately?
- **Resource Management**: Are files, connections, etc. properly closed?
- **Type Safety**: Are types validated and conversions safe?
- **Security**: Any injection vulnerabilities or unsafe operations?
- **Concurrency**: Any race conditions or deadlock risks?

Format your response as:
## Critical Bugs
[Bugs that will definitely cause crashes or security issues]

## Potential Issues
[Code smells and edge cases that might cause problems]

## Missing Validations
[Input validation and error handling gaps]

## Recommended Tests
[Specific test cases to add]

Be paranoid. Assume malicious input. Think like an attacker."""

    def process(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Hunt for bugs in code.

        Args:
            task: Code to analyze
            context: Optional context

        Returns:
            AgentResponse with bug report
        """
        # Build context
        bug_context = context or {}

        # Run static analysis first
        static_bugs = self._static_analysis(task)

        # Prepare prompt
        messages = self._build_messages(
            f"{task}\n\nStatic analysis found: {static_bugs}",
            bug_context
        )

        # Get deep analysis from LLM
        if self.provider:
            analysis = self._call_llm(messages, temperature=0.1)  # Low temp for precision
        else:
            analysis = self._format_static_bugs(static_bugs)

        # Extract bug list
        bugs = self._extract_bugs(analysis)

        # Confidence based on number of bugs found
        confidence = min(0.9, 0.5 + (len(bugs) * 0.05))

        return AgentResponse(
            content=analysis,
            confidence=confidence,
            suggestions=bugs,
            metadata={
                "agent": self.name,
                "bugs_found": len(bugs),
                "has_llm": self.provider is not None
            }
        )

    def _static_analysis(self, code: str) -> List[str]:
        """Run static analysis to find obvious bugs."""
        bugs = []

        # Check for common patterns
        patterns = {
            r'except\s*:': "CRITICAL: Bare except clause catches all exceptions",
            r'eval\(': "CRITICAL: Use of eval() is dangerous",
            r'exec\(': "CRITICAL: Use of exec() is dangerous",
            r'\/\s*0': "HIGH: Potential division by zero",
            r'password\s*=\s*["\']': "HIGH: Hardcoded password detected",
            r'api[_-]?key\s*=\s*["\']': "HIGH: Hardcoded API key detected",
            r'TODO|FIXME|HACK': "LOW: Code contains TODO/FIXME/HACK comments",
        }

        for pattern, message in patterns.items():
            if re.search(pattern, code, re.IGNORECASE):
                bugs.append(message)

        # Check for missing error handling
        if "open(" in code and "with" not in code:
            bugs.append("MEDIUM: File opened without context manager (may not close)")

        # Check for SQL injection risk
        if "execute(" in code and "+" in code:
            bugs.append("HIGH: Possible SQL injection via string concatenation")

        # Check for common None issues
        if ".get(" in code and "or" not in code:
            bugs.append("LOW: dict.get() without default value - check for None")

        return bugs

    def _format_static_bugs(self, bugs: List[str]) -> str:
        """Format static analysis results."""
        if not bugs:
            return """## Critical Bugs
None detected via static analysis.

## Potential Issues
None found in basic scan.

## Recommendations
- Run with LLM provider for deeper analysis
- Add comprehensive unit tests
- Use static analysis tools (mypy, pylint, bandit)"""

        critical = [b for b in bugs if b.startswith("CRITICAL")]
        high = [b for b in bugs if b.startswith("HIGH")]
        medium = [b for b in bugs if b.startswith("MEDIUM")]
        low = [b for b in bugs if b.startswith("LOW")]

        output = []

        if critical:
            output.append("## Critical Bugs\n" + "\n".join(f"- {b}" for b in critical))

        if high or medium:
            output.append("## Potential Issues\n" + "\n".join(f"- {b}" for b in high + medium))

        if low:
            output.append("## Minor Issues\n" + "\n".join(f"- {b}" for b in low))

        output.append("\n## Recommendations\n- Fix critical bugs immediately\n- Add input validation\n- Write tests for edge cases")

        return "\n\n".join(output)

    def _extract_bugs(self, analysis: str) -> List[str]:
        """Extract bug list from analysis."""
        bugs = []

        # Extract from Critical Bugs and Potential Issues sections
        for section in ["Critical Bugs", "Potential Issues"]:
            if f"## {section}" in analysis:
                parts = analysis.split(f"## {section}")
                if len(parts) > 1:
                    section_text = parts[1].split("##")[0]
                    for line in section_text.split("\n"):
                        line = line.strip()
                        if line.startswith("-") or line.startswith("*"):
                            bugs.append(line.lstrip("-*").strip())

        return bugs[:10]  # Top 10 bugs
