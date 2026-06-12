"""Plotly chart utilities for the dashboard."""

import plotly.graph_objects as go


def score_trend_chart(daily_scores: list[dict]) -> go.Figure:
    """Create a line chart of daily score trends."""
    dates = [d["date"] for d in daily_scores]
    scores = [d["score"] for d in daily_scores]
    counts = [d["count"] for d in daily_scores]

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=dates,
            y=scores,
            mode="lines+markers",
            name="平均スコア",
            line=dict(color="#4F46E5", width=2),
            marker=dict(size=8),
            text=[f"回答数: {c}" for c in counts],
            hovertemplate="日付: %{x}<br>平均スコア: %{y:.1f}<br>%{text}<extra></extra>",
        )
    )
    fig.update_layout(
        title="日別スコア推移",
        xaxis_title="日付",
        yaxis_title="スコア",
        yaxis=dict(range=[0, 105]),
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def topic_bar_chart(topic_trends: list[dict]) -> go.Figure:
    """Create a bar chart of per-topic average scores."""
    topics = [t["topic"] for t in topic_trends]
    scores = [t["average_score"] for t in topic_trends]
    counts = [t["count"] for t in topic_trends]

    colors = ["#4F46E5" if s >= 80 else "#F59E0B" if s >= 60 else "#EF4444" for s in scores]

    fig = go.Figure()
    fig.add_trace(
        go.Bar(
            x=topics,
            y=scores,
            marker_color=colors,
            text=[f"{s:.1f}" for s in scores],
            textposition="outside",
            hovertemplate="トピック: %{x}<br>平均スコア: %{y:.1f}<br>回答数: %{customdata}<extra></extra>",
            customdata=counts,
        )
    )
    fig.update_layout(
        title="トピック別スコア",
        xaxis_title="トピック",
        yaxis_title="平均スコア",
        yaxis=dict(range=[0, 105]),
        height=350,
        margin=dict(l=40, r=20, t=50, b=40),
    )
    return fig


def accuracy_gauge(accuracy: float) -> go.Figure:
    """Create a gauge chart for accuracy rate."""
    fig = go.Figure(
        go.Indicator(
            mode="gauge+number+delta",
            value=accuracy,
            number={"suffix": "%"},
            title={"text": "正答率"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#4F46E5"},
                "steps": [
                    {"range": [0, 50], "color": "#FEE2E2"},
                    {"range": [50, 75], "color": "#FEF3C7"},
                    {"range": [75, 100], "color": "#D1FAE5"},
                ],
                "threshold": {
                    "line": {"color": "red", "width": 4},
                    "thickness": 0.75,
                    "value": 60,
                },
            },
        )
    )
    fig.update_layout(height=250, margin=dict(l=20, r=20, t=40, b=20))
    return fig
