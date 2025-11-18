"""Data analysis agent for business intelligence."""

from typing import Dict, Any, Optional, List
from ..base_agent import BaseAgent, AgentCapability, AgentResponse


class DataAnalystAgent(BaseAgent):
    """Agent specialized in data analysis and insights."""

    def __init__(self, provider=None, tools_registry=None):
        super().__init__(
            name="DataAnalyst",
            capabilities=[
                AgentCapability.DATA_ANALYSIS,
                AgentCapability.RESEARCH
            ],
            provider=provider,
            tools_registry=tools_registry
        )

    @property
    def system_prompt(self) -> str:
        """System prompt for data analyst."""
        return """You are an expert data analyst with deep knowledge of statistics, data visualization, and business intelligence.

Your expertise:
1. Analyze datasets to find patterns, trends, and insights
2. Identify correlations and potential causations
3. Detect anomalies and outliers
4. Generate actionable business recommendations
5. Suggest appropriate visualizations
6. Perform statistical analysis and hypothesis testing

Analysis Framework:
- **Descriptive Statistics**: Mean, median, mode, std dev, quartiles
- **Trend Analysis**: Identify patterns over time
- **Correlation Analysis**: Relationships between variables
- **Segmentation**: Group data by meaningful categories
- **Anomaly Detection**: Spot unusual data points
- **Forecasting**: Predict future trends (when applicable)

Format your response as:
## Executive Summary
[Key findings in 2-3 sentences]

## Data Overview
[Summary statistics and data quality notes]

## Key Insights
[3-5 most important findings with numbers]

## Visualizations Recommended
[Charts and graphs that would best show these insights]

## Business Recommendations
[Actionable next steps based on data]

## Further Analysis
[Additional analyses that could provide value]

Be data-driven. Support claims with numbers. Focus on actionable insights."""

    def process(self, task: str, context: Optional[Dict[str, Any]] = None) -> AgentResponse:
        """
        Analyze data and generate insights.

        Args:
            task: Analysis request or data description
            context: Optional context (dataset info, business goals, etc.)

        Returns:
            AgentResponse with analysis results
        """
        # Build context
        analysis_context = context or {}

        # Prepare prompt
        messages = self._build_messages(task, analysis_context)

        # Get analysis from LLM
        if self.provider:
            analysis = self._call_llm(messages, temperature=0.3)
        else:
            # Fallback: basic template
            analysis = self._basic_analysis(task, analysis_context)

        # Extract insights
        insights = self._extract_insights(analysis)

        # Confidence depends on data quality
        data_quality = analysis_context.get("data_quality", "unknown")
        confidence = 0.85 if data_quality == "high" else 0.7

        return AgentResponse(
            content=analysis,
            confidence=confidence,
            suggestions=insights,
            metadata={
                "agent": self.name,
                "analysis_type": analysis_context.get("type", "general"),
                "insights_count": len(insights)
            }
        )

    def _basic_analysis(self, task: str, context: Dict[str, Any]) -> str:
        """Basic analysis template when no LLM available."""
        return f"""## Executive Summary
Analysis request received: {task[:100]}...

## Data Overview
- Data source: {context.get('source', 'Not specified')}
- Data quality: {context.get('data_quality', 'Unknown')}
- Records: {context.get('record_count', 'Unknown')}

## Key Insights
To perform detailed analysis, please:
1. Configure an LLM provider for advanced analytics
2. Provide dataset summary statistics
3. Specify business goals and metrics

## Recommendations
- Use tools like calculate() for statistical analysis
- Provide data samples or summary statistics
- Define key performance indicators (KPIs)

## Note
This is a basic template. Enable LLM provider for full analysis capabilities."""

    def _extract_insights(self, analysis: str) -> List[str]:
        """Extract key insights from analysis."""
        insights = []

        if "## Key Insights" in analysis:
            parts = analysis.split("## Key Insights")
            if len(parts) > 1:
                insights_text = parts[1].split("##")[0]
                for line in insights_text.split("\n"):
                    line = line.strip()
                    if line and (line.startswith("-") or line.startswith("*") or line[0].isdigit()):
                        insights.append(line.lstrip("-*0123456789.").strip())

        return insights[:5]  # Top 5 insights
