"""Tree of Thoughts for exploring multiple solution paths."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


@dataclass
class ThoughtNode:
    """Single node in the thought tree."""
    thought: str
    score: float = 0.0
    depth: int = 0
    children: List['ThoughtNode'] = field(default_factory=list)
    parent: Optional['ThoughtNode'] = None


class TreeOfThoughts:
    """Explore multiple reasoning paths using tree search."""

    def __init__(self, provider=None, max_depth: int = 3, branches_per_node: int = 3):
        """
        Initialize ToT.

        Args:
            provider: LLM provider
            max_depth: Maximum tree depth
            branches_per_node: Number of alternative thoughts per node
        """
        self.provider = provider
        self.max_depth = max_depth
        self.branches_per_node = branches_per_node

    def explore(
        self,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Explore solution space using tree of thoughts.

        Args:
            problem: Problem to solve
            context: Optional context

        Returns:
            Best solution path and alternatives
        """
        if not self.provider:
            return self._basic_exploration(problem)

        # Create root node
        root = ThoughtNode(thought=f"Problem: {problem}", depth=0)

        # Expand tree
        self._expand_node(root, problem, context)

        # Find best path
        best_path = self._find_best_path(root)

        # Get alternative paths
        alternatives = self._get_top_paths(root, n=3)

        return {
            "problem": problem,
            "best_solution": best_path,
            "alternatives": alternatives,
            "tree_size": self._count_nodes(root),
            "confidence": best_path[-1].score if best_path else 0.0
        }

    def _expand_node(
        self,
        node: ThoughtNode,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ):
        """Recursively expand a node."""
        if node.depth >= self.max_depth:
            return

        # Generate alternative thoughts
        thoughts = self._generate_thoughts(node, problem, context)

        # Create child nodes
        for thought_text, score in thoughts:
            child = ThoughtNode(
                thought=thought_text,
                score=score,
                depth=node.depth + 1,
                parent=node
            )
            node.children.append(child)

            # Recursively expand promising children
            if score > 0.5:  # Only expand promising paths
                self._expand_node(child, problem, context)

    def _generate_thoughts(
        self,
        node: ThoughtNode,
        problem: str,
        context: Optional[Dict[str, Any]] = None
    ) -> List[tuple[str, float]]:
        """Generate alternative thoughts from a node."""
        if not self.provider:
            return [("Alternative path", 0.5) for _ in range(self.branches_per_node)]

        # Build prompt for generating alternatives
        prompt = f"""Problem: {problem}

Current reasoning path:
{self._get_path_text(node)}

Generate {self.branches_per_node} alternative next steps to solve this problem.
For each alternative, rate its promise (0-1).

Format:
Alternative 1: [thought] (score: 0.X)
Alternative 2: [thought] (score: 0.X)
..."""

        response = self.provider.chat(
            system="You are exploring solution paths. Generate diverse alternatives.",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.7  # Higher temperature for diversity
        )

        # Parse alternatives
        return self._parse_alternatives(response)

    def _parse_alternatives(self, response: str) -> List[tuple[str, float]]:
        """Parse alternative thoughts from response."""
        alternatives = []
        lines = response.split("\n")

        for line in lines:
            if "Alternative" in line and ":" in line:
                parts = line.split(":", 1)
                if len(parts) == 2:
                    thought = parts[1].strip()

                    # Extract score
                    score = 0.5
                    if "(score:" in thought:
                        score_part = thought.split("(score:")[1].split(")")[0].strip()
                        try:
                            score = float(score_part)
                        except ValueError:
                            pass
                        thought = thought.split("(score:")[0].strip()

                    alternatives.append((thought, score))

        return alternatives[:self.branches_per_node]

    def _get_path_text(self, node: ThoughtNode) -> str:
        """Get text representation of path to node."""
        path = []
        current = node
        while current:
            path.insert(0, current.thought)
            current = current.parent
        return "\n→ ".join(path)

    def _find_best_path(self, root: ThoughtNode) -> List[ThoughtNode]:
        """Find best path from root to leaf."""
        if not root.children:
            return [root]

        best_child = max(root.children, key=lambda c: c.score)
        return [root] + self._find_best_path(best_child)

    def _get_top_paths(self, root: ThoughtNode, n: int = 3) -> List[List[ThoughtNode]]:
        """Get top N solution paths."""
        all_paths = []
        self._collect_paths(root, [], all_paths)

        # Sort by average score
        all_paths.sort(key=lambda p: sum(node.score for node in p) / len(p), reverse=True)

        return all_paths[:n]

    def _collect_paths(
        self,
        node: ThoughtNode,
        current_path: List[ThoughtNode],
        all_paths: List[List[ThoughtNode]]
    ):
        """Recursively collect all paths."""
        current_path = current_path + [node]

        if not node.children:
            all_paths.append(current_path)
        else:
            for child in node.children:
                self._collect_paths(child, current_path, all_paths)

    def _count_nodes(self, node: ThoughtNode) -> int:
        """Count total nodes in tree."""
        count = 1
        for child in node.children:
            count += self._count_nodes(child)
        return count

    def _basic_exploration(self, problem: str) -> Dict[str, Any]:
        """Basic exploration without LLM."""
        return {
            "problem": problem,
            "best_solution": [
                ThoughtNode("Understand problem"),
                ThoughtNode("Explore alternatives"),
                ThoughtNode("Select best approach")
            ],
            "alternatives": [],
            "tree_size": 3,
            "confidence": 0.3
        }
