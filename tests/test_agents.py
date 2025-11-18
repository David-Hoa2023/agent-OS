"""Tests for domain-specific agents."""

import pytest
from codex_prime.agents import (
    BaseAgent,
    AgentCapability,
    CodeReviewerAgent,
    BugHunterAgent,
    DataAnalystAgent
)


def test_code_reviewer_creation():
    """Test creating code reviewer agent."""
    agent = CodeReviewerAgent()

    assert agent.name == "CodeReviewer"
    assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    assert AgentCapability.REVIEW in agent.capabilities


def test_code_reviewer_basic_review():
    """Test code reviewer without LLM."""
    agent = CodeReviewerAgent()

    code = """
def calculate(x, y):
    # TODO: Add error handling
    password = "secret123"
    return x / y
"""

    response = agent.process(code, context={"language": "python"})

    assert response.content is not None
    assert response.confidence > 0
    assert "password" in response.content.lower() or "TODO" in response.content


def test_code_reviewer_can_handle():
    """Test agent capability checking."""
    agent = CodeReviewerAgent()

    assert agent.can_handle(AgentCapability.CODE_ANALYSIS)
    assert agent.can_handle(AgentCapability.REVIEW)
    assert not agent.can_handle(AgentCapability.DATA_ANALYSIS)


def test_bug_hunter_creation():
    """Test creating bug hunter agent."""
    agent = BugHunterAgent()

    assert agent.name == "BugHunter"
    assert AgentCapability.CODE_ANALYSIS in agent.capabilities
    assert AgentCapability.TESTING in agent.capabilities


def test_bug_hunter_static_analysis():
    """Test bug hunter static analysis."""
    agent = BugHunterAgent()

    # Code with obvious bugs
    code = """
def divide(a, b):
    return a / 0  # Division by zero

def login(username, password):
    query = "SELECT * FROM users WHERE user='" + username + "'"
    eval(password)  # Dangerous!
"""

    response = agent.process(code, context={"language": "python"})

    assert response.content is not None
    assert "division by zero" in response.content.lower() or "CRITICAL" in response.content
    assert len(response.suggestions) > 0


def test_bug_hunter_finds_security_issues():
    """Test bug hunter finds security vulnerabilities."""
    agent = BugHunterAgent()

    code = """
api_key = "sk-1234567890"
password = "admin123"
"""

    response = agent.process(code)

    content_lower = response.content.lower()
    assert "api" in content_lower or "password" in content_lower or "hardcoded" in content_lower


def test_data_analyst_creation():
    """Test creating data analyst agent."""
    agent = DataAnalystAgent()

    assert agent.name == "DataAnalyst"
    assert AgentCapability.DATA_ANALYSIS in agent.capabilities
    assert AgentCapability.RESEARCH in agent.capabilities


def test_data_analyst_basic_analysis():
    """Test data analyst without LLM."""
    agent = DataAnalystAgent()

    task = "Analyze sales data for Q4 2024"
    context = {
        "source": "sales_db",
        "record_count": 10000,
        "data_quality": "high"
    }

    response = agent.process(task, context=context)

    assert response.content is not None
    assert response.confidence > 0
    assert "sales" in response.content.lower() or "analysis" in response.content.lower()


def test_agent_response_structure():
    """Test agent response structure."""
    agent = CodeReviewerAgent()

    response = agent.process("def hello(): print('hi')")

    assert hasattr(response, 'content')
    assert hasattr(response, 'confidence')
    assert hasattr(response, 'suggestions')
    assert hasattr(response, 'metadata')
    assert isinstance(response.suggestions, list)
    assert isinstance(response.metadata, dict)
    assert 0 <= response.confidence <= 1


def test_multiple_agents_collaboration():
    """Test using multiple agents on same code."""
    code = """
def process_user_data(data):
    # TODO: Validate input
    result = eval(data)
    return result
"""

    reviewer = CodeReviewerAgent()
    hunter = BugHunterAgent()

    review_response = reviewer.process(code)
    bug_response = hunter.process(code)

    # Both should find issues
    assert review_response.content is not None
    assert bug_response.content is not None

    # Bug hunter should be more critical
    assert "eval" in bug_response.content.lower() or "CRITICAL" in bug_response.content
