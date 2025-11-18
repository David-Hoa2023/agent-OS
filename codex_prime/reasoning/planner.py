"""Long-term planning for multi-day projects."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime, timedelta


@dataclass
class Task:
    """Single task in a plan."""
    task_id: str
    name: str
    description: str
    estimated_hours: float
    dependencies: List[str] = field(default_factory=list)
    status: str = "pending"  # pending, in_progress, completed
    assigned_to: Optional[str] = None


@dataclass
class Milestone:
    """Project milestone."""
    name: str
    tasks: List[str]  # Task IDs
    deadline: Optional[str] = None


class LongTermPlanner:
    """Plan long-term projects with task breakdown."""

    def __init__(self, provider=None):
        """
        Initialize planner.

        Args:
            provider: LLM provider for planning
        """
        self.provider = provider

    def create_plan(
        self,
        project_goal: str,
        duration_days: int,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Create a long-term project plan.

        Args:
            project_goal: High-level project goal
            duration_days: Project duration in days
            context: Optional context (team size, constraints, etc.)

        Returns:
            Detailed project plan
        """
        if not self.provider:
            return self._basic_plan(project_goal, duration_days)

        # Generate plan
        prompt = self._build_planning_prompt(project_goal, duration_days, context)

        response = self.provider.chat(
            system=self._get_planning_prompt(),
            messages=[{"role": "user", "content": prompt}],
            temperature=0.4
        )

        # Parse plan
        tasks = self._parse_tasks(response)
        milestones = self._parse_milestones(response)

        return {
            "project_goal": project_goal,
            "duration_days": duration_days,
            "tasks": tasks,
            "milestones": milestones,
            "timeline": self._generate_timeline(tasks, duration_days),
            "total_estimated_hours": sum(t.estimated_hours for t in tasks)
        }

    def _get_planning_prompt(self) -> str:
        """Get system prompt for planning."""
        return """You are an expert project planner.

Create detailed project plans with:
1. Task breakdown (break large goals into manageable tasks)
2. Time estimates (realistic hours per task)
3. Dependencies (which tasks depend on others)
4. Milestones (key checkpoints)
5. Risk assessment

Format your plan as:
## Tasks
- Task ID: [name] ([X] hours) [depends on: IDs]

## Milestones
- [Milestone name]: Tasks [IDs]

## Timeline
- Week 1: [tasks]
- Week 2: [tasks]
...

Be realistic about time estimates. Account for unknowns and risks."""

    def _build_planning_prompt(
        self,
        project_goal: str,
        duration_days: int,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build planning prompt."""
        parts = [
            f"Project Goal: {project_goal}",
            f"Duration: {duration_days} days",
            ""
        ]

        if context:
            parts.append("Context:")
            for key, value in context.items():
                parts.append(f"- {key}: {value}")
            parts.append("")

        parts.append("Create a detailed project plan with tasks, estimates, and milestones.")

        return "\n".join(parts)

    def _parse_tasks(self, response: str) -> List[Task]:
        """Parse tasks from planning response."""
        tasks = []

        # Simple parsing - can be enhanced
        lines = response.split("\n")
        for line in lines:
            if line.strip().startswith("-") and ":" in line:
                # Extract task details
                parts = line.split(":")
                if len(parts) >= 2:
                    task_id = f"task_{len(tasks) + 1}"
                    name = parts[1].strip()

                    # Extract hours estimate
                    hours = 8.0  # Default
                    if "(" in name and "hours)" in name:
                        try:
                            hours_str = name.split("(")[1].split("hours)")[0].strip()
                            hours = float(hours_str)
                        except (ValueError, IndexError):
                            pass

                    # Extract dependencies
                    dependencies = []
                    if "depends on:" in line.lower():
                        dep_part = line.split("depends on:")[1].strip()
                        # Simple parsing of task IDs
                        dependencies = [d.strip() for d in dep_part.split(",")]

                    tasks.append(Task(
                        task_id=task_id,
                        name=name.split("(")[0].strip(),
                        description=name,
                        estimated_hours=hours,
                        dependencies=dependencies
                    ))

        return tasks

    def _parse_milestones(self, response: str) -> List[Milestone]:
        """Parse milestones from planning response."""
        milestones = []

        # Look for milestones section
        if "## Milestones" in response:
            milestone_section = response.split("## Milestones")[1]
            if "##" in milestone_section:
                milestone_section = milestone_section.split("##")[0]

            lines = milestone_section.split("\n")
            for line in lines:
                if line.strip().startswith("-") and ":" in line:
                    parts = line.split(":", 1)
                    if len(parts) == 2:
                        name = parts[0].strip().lstrip("-").strip()
                        tasks = []  # Extract task IDs from description
                        milestones.append(Milestone(name=name, tasks=tasks))

        return milestones

    def _generate_timeline(self, tasks: List[Task], duration_days: int) -> Dict[str, List[str]]:
        """Generate week-by-week timeline."""
        timeline = {}
        hours_per_day = 8
        total_hours_available = duration_days * hours_per_day

        current_week = 1
        hours_used = 0

        for task in tasks:
            week_key = f"Week {current_week}"
            if week_key not in timeline:
                timeline[week_key] = []

            timeline[week_key].append(task.name)

            hours_used += task.estimated_hours

            # Move to next week if over 40 hours
            if hours_used > (current_week * 40):
                current_week += 1

        return timeline

    def _basic_plan(self, project_goal: str, duration_days: int) -> Dict[str, Any]:
        """Basic plan without LLM."""
        weeks = duration_days // 7

        tasks = [
            Task("task_1", "Planning & Setup", "Initial planning", 16),
            Task("task_2", "Implementation", "Core development", duration_days * 4),
            Task("task_3", "Testing", "QA and testing", duration_days * 2),
            Task("task_4", "Deployment", "Final deployment", 8)
        ]

        return {
            "project_goal": project_goal,
            "duration_days": duration_days,
            "tasks": tasks,
            "milestones": [
                Milestone("Planning Complete", ["task_1"]),
                Milestone("MVP Ready", ["task_2"]),
                Milestone("Launch", ["task_4"])
            ],
            "timeline": {f"Week {i+1}": ["Work on tasks"] for i in range(weeks)},
            "total_estimated_hours": sum(t.estimated_hours for t in tasks)
        }
