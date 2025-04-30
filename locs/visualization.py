import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Optional, List, Dict, Any

def create_location_map(
    data: pd.DataFrame, 
    color_by: Optional[str] = None, 
    size_by: Optional[str] = None
) -> go.Figure:
    """
    Create an interactive map showing restaurant locations.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        color_by: Column name to color points by (e.g. rating, cuisine)
        size_by: Column name to size points by (e.g. rating, price)
        
    Returns:
        Plotly figure object with the map
    """
    # Check if required columns exist
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Prepare hover text
    hover_data = ['name']
    if 'address' in data.columns:
        hover_data.append('address')
    if 'cuisine' in data.columns:
        hover_data.append('cuisine')
    if 'rating' in data.columns and color_by != 'rating':
        hover_data.append('rating')
    if 'price' in data.columns and color_by != 'price' and size_by != 'price':
        hover_data.append('price')
    
    # Size configuration
    size = None
    size_max = 15
    
    if size_by and size_by != 'None' and size_by in data.columns:
        size = size_by
    
    # Color configuration
    color = None
    color_continuous_scale = 'Viridis'
    
    if color_by and color_by != 'None' and color_by in data.columns:
        color = color_by
        if color_by == 'rating':
            color_continuous_scale = 'RdYlGn'  # Red-Yellow-Green for ratings
    
    # Create the map
    fig = px.scatter_mapbox(
        data,
        lat='latitude',
        lon='longitude',
        hover_name='name' if 'name' in data.columns else None,
        hover_data=hover_data,
        color=color,
        size=size,
        size_max=size_max,
        zoom=10,
        height=600,
        color_continuous_scale=color_continuous_scale,
        title="Restaurant Locations"
    )
    
    # Use open-source map tiles
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    
    return fig

def create_heatmap(data: pd.DataFrame) -> go.Figure:
    """
    Create a heatmap showing restaurant density.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        
    Returns:
        Plotly figure object with the heatmap
    """
    # Check if required columns exist
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Create the heatmap
    fig = px.density_mapbox(
        data,
        lat='latitude',
        lon='longitude',
        z=data.index,  # Use index for count-based density
        radius=15,
        zoom=10,
        height=600,
        mapbox_style="open-street-map",
        title="Restaurant Density Heatmap"
    )
    
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    
    return fig

def create_cluster_map(data: pd.DataFrame, color_by: Optional[str] = None) -> go.Figure:
    """
    Create a map with clustered restaurant locations.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        color_by: Column name to color points by (e.g. rating, cuisine)
        
    Returns:
        Plotly figure object with the cluster map
    """
    # Check if required columns exist
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Determine if we're coloring by category or continuous value
    is_categorical = False
    if color_by and color_by != 'None' and color_by in data.columns:
        if data[color_by].dtype == 'object' or data[color_by].dtype.name == 'category':
            is_categorical = True
    
    # Create a scatter map base
    fig = create_location_map(data, color_by)
    
    # Add a caption about clustering
    fig.update_layout(
        title="Restaurant Clusters",
        annotations=[
            dict(
                x=0.5,
                y=1.02,
                xref="paper",
                yref="paper",
                text="Clusters are visualized by color and proximity",
                showarrow=False,
                font=dict(size=14)
            )
        ]
    )
    
    return fig

def create_cluster_result_map(clustered_data: pd.DataFrame) -> go.Figure:
    """
    Create a map visualizing clustering results.
    
    Args:
        clustered_data: DataFrame with restaurant data and a 'cluster' column
        
    Returns:
        Plotly figure object with the cluster map
    """
    # Check if required columns exist
    if 'latitude' not in clustered_data.columns or 'longitude' not in clustered_data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    if 'cluster' not in clustered_data.columns:
        raise ValueError("Data must contain a 'cluster' column")
    
    # Create the map
    fig = px.scatter_mapbox(
        clustered_data,
        lat='latitude',
        lon='longitude',
        color='cluster',
        hover_name='name' if 'name' in clustered_data.columns else None,
        hover_data=['name', 'cluster', 'cuisine', 'rating'] if 'cuisine' in clustered_data.columns and 'rating' in clustered_data.columns else ['name', 'cluster'],
        zoom=10,
        height=600,
        title="Restaurant Clusters Analysis"
    )
    
    # Use open-source map tiles
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    
    return fig

def create_choropleth_map(
    data: pd.DataFrame, 
    region_boundaries: Dict[str, Any],
    region_column: str, 
    metric: str = 'count'
) -> go.Figure:
    """
    Create a choropleth map showing restaurant metrics by region.
    
    Args:
        data: DataFrame with restaurant data including region information
        region_boundaries: GeoJSON or similar structure with region boundaries
        region_column: Column in data that matches region identifiers in boundaries
        metric: Metric to visualize ('count', 'avg_rating', etc.)
        
    Returns:
        Plotly figure object with the choropleth map
    """
    # Note: This is a placeholder implementation as it requires region boundaries
    # In a real application, you would load GeoJSON files with region boundaries
    
    if region_column not in data.columns:
        raise ValueError(f"Data must contain the region column '{region_column}'")
    
    # Aggregate data by region
    if metric == 'count':
        region_data = data.groupby(region_column).size().reset_index(name='count')
    elif metric == 'avg_rating' and 'rating' in data.columns:
        region_data = data.groupby(region_column)['rating'].mean().reset_index(name='avg_rating')
    else:
        raise ValueError(f"Unsupported metric: {metric}")
    
    # Placeholder for choropleth creation
    # In a real app, you would use:
    # fig = px.choropleth_mapbox(
    #     region_data,
    #     geojson=region_boundaries,
    #     locations=region_column,
    #     color=metric,
    #     ...
    # )
    
    # For now, return a basic map
    return create_location_map(data)
