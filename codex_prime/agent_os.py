"""Core Agent OS implementation."""

from dataclasses import dataclass, field
from typing import Any, Optional
import json


@dataclass
class StateCapsule:
    """Agent state container with persona, mission, and constraints."""

    persona: str = ""
    mission: dict[str, Any] = field(default_factory=dict)
    constraints: list[str] = field(default_factory=list)
    open_threads: list[dict[str, Any]] = field(default_factory=list)

    def pack(self) -> str:
        """Serialize capsule to compact string format."""
        data = {
            "persona": self.persona,
            "mission": self.mission,
            "constraints": self.constraints,
            "open_threads": self.open_threads
        }
        return json.dumps(data, indent=2)

    def update_from_dict(self, data: dict[str, Any]) -> None:
        """Update capsule fields from dictionary."""
        if "persona" in data:
            self.persona = data["persona"]
        if "mission" in data:
            self.mission = data["mission"]
        if "constraints" in data:
            self.constraints = data["constraints"]
        if "open_threads" in data:
            self.open_threads = data["open_threads"]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "StateCapsule":
        """Create capsule from dictionary."""
        return cls(
            persona=data.get("persona", ""),
            mission=data.get("mission", {}),
            constraints=data.get("constraints", []),
            open_threads=data.get("open_threads", [])
        )


class AgentOS:
    """Main Agent OS coordinator."""

    def __init__(self, project_id: str, capsule: Optional[StateCapsule] = None):
        self.project_id = project_id
        self.capsule = capsule or StateCapsule()

    def fortify(
        self,
        system_prompt: str,
        capsule: StateCapsule,
        user_msg: str,
        checklist: Optional[list[str]] = None,
        loops: int = 1
    ) -> str:
        """
        Run fortification loop: draft → critique → revise.

        Args:
            system_prompt: Base system prompt
            capsule: State capsule
            user_msg: User message
            checklist: Criteria for critique
            loops: Number of fortification passes

        Returns:
            Final fortified response
        """
        if checklist is None:
            checklist = [
                "Factuality",
                "Clarity",
                "Directness",
                "Completeness",
                "Tone faithfulness",
                "Mission alignment"
            ]

        # TODO: Implement actual fortification with LLM
        # For now, return placeholder
        return f"[Fortified response after {loops} loops for: {user_msg}]"
