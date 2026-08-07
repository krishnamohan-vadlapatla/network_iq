"""
NetworkIQ — UI Components
=========================
"""

import plotly.graph_objects as go
import pandas as pd

def draw_network_map(regions: list, transfers: list):
    """Draw a simple network graph of transfers."""
    # Simplified mock visualization
    fig = go.Figure()
    
    # Add nodes
    for r in regions:
        fig.add_trace(go.Scatter(x=[0], y=[0], mode='markers+text', name=r, text=[r]))
        
    fig.update_layout(title="Transfer Network", showlegend=False)
    return fig
