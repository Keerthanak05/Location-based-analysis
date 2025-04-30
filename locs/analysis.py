import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from typing import Dict, List, Tuple, Any, Optional
from sklearn.cluster import KMeans, DBSCAN
from sklearn.preprocessing import StandardScaler
import scipy.spatial as spatial

def create_distribution_plot(data: pd.DataFrame, column: str) -> go.Figure:
    """
    Create a distribution plot for a numeric column.
    
    Args:
        data: DataFrame with restaurant data
        column: Column name to visualize
        
    Returns:
        Plotly figure with distribution plot
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Create a histogram with KDE curve
    fig = px.histogram(
        data, 
        x=column,
        marginal="rug",
        nbins=20,
        title=f"Distribution of {column.title()}",
        labels={column: column.title()},
        color_discrete_sequence=['#636EFA']
    )
    
    # Add mean line
    mean_val = data[column].mean()
    fig.add_vline(x=mean_val, line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {mean_val:.2f}", 
                  annotation_position="top right")
    
    # Update layout
    fig.update_layout(
        xaxis_title=column.title(),
        yaxis_title="Frequency",
        bargap=0.1
    )
    
    return fig

def create_categorical_distribution(data: pd.DataFrame, column: str, limit: int = 10) -> go.Figure:
    """
    Create a bar chart for a categorical column.
    
    Args:
        data: DataFrame with restaurant data
        column: Column name to visualize
        limit: Maximum number of categories to show
        
    Returns:
        Plotly figure with bar chart
    """
    if column not in data.columns:
        raise ValueError(f"Column '{column}' not found in data")
    
    # Get value counts
    value_counts = data[column].value_counts().nlargest(limit)
    
    # Create bar chart
    fig = px.bar(
        x=value_counts.index,
        y=value_counts.values,
        title=f"Distribution of {column.title()}",
        labels={'x': column.title(), 'y': 'Count'},
        color=value_counts.values,
        color_continuous_scale='Viridis'
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title=column.title(),
        yaxis_title="Count",
        xaxis={'categoryorder':'total descending'}
    )
    
    return fig

def create_correlation_matrix(data: pd.DataFrame) -> go.Figure:
    """
    Create a correlation matrix heatmap.
    
    Args:
        data: DataFrame with numeric columns
        
    Returns:
        Plotly figure with correlation heatmap
    """
    # Calculate correlation matrix
    corr = data.corr()
    
    # Create heatmap
    fig = px.imshow(
        corr,
        text_auto='.2f',
        aspect="auto",
        color_continuous_scale='RdBu_r',
        title="Correlation Matrix"
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="",
        yaxis_title="",
    )
    
    return fig

def create_scatter_plot(
    data: pd.DataFrame, 
    x_var: str, 
    y_var: str, 
    color_by_cuisine: bool = False
) -> go.Figure:
    """
    Create a scatter plot between two variables.
    
    Args:
        data: DataFrame with restaurant data
        x_var: Column name for x-axis
        y_var: Column name for y-axis
        color_by_cuisine: Whether to color points by cuisine
        
    Returns:
        Plotly figure with scatter plot
    """
    if x_var not in data.columns or y_var not in data.columns:
        raise ValueError(f"Columns '{x_var}' or '{y_var}' not found in data")
    
    # Determine color variable
    color = None
    if color_by_cuisine and 'cuisine' in data.columns:
        color = 'cuisine'
        # Limit to top cuisines for better visualization
        top_cuisines = data['cuisine'].value_counts().nlargest(10).index.tolist()
        plot_data = data[data['cuisine'].isin(top_cuisines)].copy()
    else:
        plot_data = data.copy()
    
    # Create scatter plot
    fig = px.scatter(
        plot_data,
        x=x_var,
        y=y_var,
        color=color,
        hover_name='name' if 'name' in data.columns else None,
        title=f"{y_var.title()} vs {x_var.title()}",
        labels={x_var: x_var.title(), y_var: y_var.title()},
        opacity=0.7
    )
    
    # Add trendline
    fig.update_layout(
        xaxis_title=x_var.title(),
        yaxis_title=y_var.title(),
    )
    
    return fig

def perform_clustering(
    data: pd.DataFrame, 
    features: List[str], 
    n_clusters: int = 5
) -> pd.DataFrame:
    """
    Perform clustering on restaurant data.
    
    Args:
        data: DataFrame with restaurant data
        features: List of columns to use for clustering
        n_clusters: Number of clusters to create
        
    Returns:
        DataFrame with original data and added cluster assignment
    """
    # Check if all features exist
    for feature in features:
        if feature not in data.columns:
            raise ValueError(f"Feature '{feature}' not found in data")
    
    # Create a copy of the data
    result_data = data.copy()
    
    # Extract features for clustering
    X = result_data[features].values
    
    # Standardize features
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    
    # Perform KMeans clustering
    kmeans = KMeans(n_clusters=n_clusters, random_state=42)
    clusters = kmeans.fit_predict(X_scaled)
    
    # Add cluster assignment to dataframe
    result_data['cluster'] = clusters
    
    return result_data

def analyze_clusters(clustered_data: pd.DataFrame) -> pd.DataFrame:
    """
    Analyze the characteristics of each cluster.
    
    Args:
        clustered_data: DataFrame with restaurant data and cluster assignments
        
    Returns:
        DataFrame with cluster profiles
    """
    if 'cluster' not in clustered_data.columns:
        raise ValueError("Data must contain 'cluster' column")
    
    # List of numeric columns to analyze
    numeric_cols = clustered_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col != 'cluster']
    
    # Create cluster profiles
    profiles = []
    
    for cluster_id in sorted(clustered_data['cluster'].unique()):
        cluster_data = clustered_data[clustered_data['cluster'] == cluster_id]
        
        profile = {'Cluster': cluster_id, 'Count': len(cluster_data)}
        
        # Add numeric column averages
        for col in numeric_cols:
            if col in ['latitude', 'longitude']:
                continue
            profile[f'Avg {col.title()}'] = cluster_data[col].mean()
        
        # Add top cuisines if available
        if 'cuisine' in clustered_data.columns:
            top_cuisine = cluster_data['cuisine'].value_counts().nlargest(1)
            if not top_cuisine.empty:
                profile['Top Cuisine'] = top_cuisine.index[0]
                profile['Cuisine %'] = top_cuisine.values[0] / len(cluster_data) * 100
        
        profiles.append(profile)
    
    return pd.DataFrame(profiles)

def visualize_cluster_characteristics(clustered_data: pd.DataFrame) -> go.Figure:
    """
    Create a radar chart showing cluster characteristics.
    
    Args:
        clustered_data: DataFrame with restaurant data and cluster assignments
        
    Returns:
        Plotly figure with radar chart
    """
    if 'cluster' not in clustered_data.columns:
        raise ValueError("Data must contain 'cluster' column")
    
    # Get numeric columns for radar chart (excluding lat/long)
    numeric_cols = clustered_data.select_dtypes(include=['float64', 'int64']).columns.tolist()
    numeric_cols = [col for col in numeric_cols if col not in ['latitude', 'longitude', 'cluster']]
    
    if not numeric_cols:
        # If no numeric columns, create a bar chart of cluster sizes instead
        cluster_counts = clustered_data['cluster'].value_counts().sort_index()
        
        fig = px.bar(
            x=cluster_counts.index,
            y=cluster_counts.values,
            title="Cluster Sizes",
            labels={'x': 'Cluster', 'y': 'Number of Restaurants'}
        )
        
        return fig
    
    # Calculate cluster means
    cluster_stats = {}
    clusters = sorted(clustered_data['cluster'].unique())
    
    for col in numeric_cols:
        # Normalize the values to 0-1 range for radar chart
        min_val = clustered_data[col].min()
        max_val = clustered_data[col].max()
        range_val = max_val - min_val
        
        if range_val == 0:  # Skip constant columns
            continue
            
        for cluster in clusters:
            if cluster not in cluster_stats:
                cluster_stats[cluster] = {}
                
            cluster_mean = clustered_data[clustered_data['cluster'] == cluster][col].mean()
            normalized_val = (cluster_mean - min_val) / range_val if range_val > 0 else 0.5
            cluster_stats[cluster][col] = normalized_val
    
    # Create radar chart
    fig = go.Figure()
    
    for cluster in clusters:
        fig.add_trace(go.Scatterpolar(
            r=[cluster_stats[cluster].get(col, 0) for col in numeric_cols],
            theta=numeric_cols,
            fill='toself',
            name=f'Cluster {cluster}'
        ))
    
    fig.update_layout(
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 1]
            )
        ),
        title="Cluster Characteristics"
    )
    
    return fig

def nearest_neighbor_analysis(data: pd.DataFrame) -> Dict[str, float]:
    """
    Perform nearest neighbor analysis to determine restaurant distribution patterns.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        
    Returns:
        Dictionary with nearest neighbor statistics
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Extract coordinates
    coords = data[['latitude', 'longitude']].values
    
    # Calculate study area (approximate in square km)
    lat_min, lat_max = data['latitude'].min(), data['latitude'].max()
    lng_min, lng_max = data['longitude'].min(), data['longitude'].max()
    
    # Convert to distance (very rough approximation)
    # 1 degree latitude = ~111km
    # 1 degree longitude = ~111km * cos(latitude)
    avg_lat = (lat_min + lat_max) / 2
    lat_dist = (lat_max - lat_min) * 111
    lng_dist = (lng_max - lng_min) * 111 * np.cos(np.radians(avg_lat))
    study_area = lat_dist * lng_dist
    
    # Build KD-tree for efficient nearest neighbor calculation
    tree = spatial.KDTree(coords)
    
    # Calculate distance to nearest neighbor for each point
    nn_distances = []
    for coord in coords:
        # Query with k=2 to get nearest neighbor (first result is the point itself)
        distances, indices = tree.query(coord, k=2)
        nn_distances.append(distances[1])  # Take the second closest (first is self)
    
    # Calculate average nearest neighbor distance (in degrees)
    avg_nn_distance = np.mean(nn_distances)
    
    # Convert to approximate kilometers
    avg_nn_distance_km = avg_nn_distance * 111
    
    # Calculate expected nearest neighbor distance for random distribution
    # Formula: 0.5 * sqrt(study_area / n)
    n = len(data)
    expected_nn_distance = 0.5 * np.sqrt(study_area / n)
    
    # Calculate nearest neighbor index
    nn_index = avg_nn_distance_km / expected_nn_distance if expected_nn_distance > 0 else 0
    
    return {
        'avg_nn_distance': avg_nn_distance_km,
        'expected_nn_distance': expected_nn_distance,
        'nn_index': nn_index
    }

def plot_nearest_neighbors(data: pd.DataFrame) -> go.Figure:
    """
    Create a visualization of nearest neighbors among restaurants.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        
    Returns:
        Plotly figure with nearest neighbor visualization
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Extract coordinates
    coords = data[['latitude', 'longitude']].values
    
    # Build KD-tree for efficient nearest neighbor calculation
    tree = spatial.KDTree(coords)
    
    # Find nearest neighbor for each point
    lines = []
    for i, coord in enumerate(coords):
        distances, indices = tree.query(coord, k=2)
        nearest_idx = indices[1]  # First one is self
        
        # Create a line between the point and its nearest neighbor
        line = {
            'type': 'line',
            'x0': coord[1],  # longitude is x
            'y0': coord[0],  # latitude is y
            'x1': coords[nearest_idx][1],
            'y1': coords[nearest_idx][0],
            'line': {
                'color': 'rgba(128, 128, 128, 0.5)',
                'width': 1
            }
        }
        lines.append(line)
    
    # Create the base map
    fig = px.scatter_mapbox(
        data,
        lat='latitude',
        lon='longitude',
        hover_name='name' if 'name' in data.columns else None,
        zoom=10,
        height=600,
        title="Nearest Neighbor Analysis"
    )
    
    # Add the nearest neighbor lines
    for line in lines:
        fig.add_shape(
            type="line",
            x0=line['x0'],
            y0=line['y0'],
            x1=line['x1'],
            y1=line['y1'],
            line=dict(color='rgba(128, 128, 128, 0.3)', width=1),
            layer='below'
        )
    
    # Use open-source map tiles
    fig.update_layout(
        mapbox_style="open-street-map",
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    
    return fig

def analyze_distance_distribution(
    data: pd.DataFrame, 
    center_lat: float, 
    center_lng: float, 
    center_name: str
) -> go.Figure:
    """
    Analyze the distribution of distances from a central point.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        center_lat: Latitude of the central point
        center_lng: Longitude of the central point
        center_name: Name of the central point
        
    Returns:
        Plotly figure with distance distribution
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Calculate distance from center for each restaurant
    # This is an approximation using Euclidean distance in degree space
    # For more accurate distances, haversine formula should be used
    data_with_dist = data.copy()
    
    # Calculate distance in km (rough approximation)
    # 1 degree of latitude = ~111km
    # 1 degree of longitude = ~111km * cos(latitude)
    cos_lat = np.cos(np.radians(center_lat))
    data_with_dist['distance'] = np.sqrt(
        ((data_with_dist['latitude'] - center_lat) * 111) ** 2 +
        ((data_with_dist['longitude'] - center_lng) * 111 * cos_lat) ** 2
    )
    
    # Create histogram of distances
    fig = px.histogram(
        data_with_dist,
        x='distance',
        nbins=20,
        title=f"Distance Distribution from {center_name}",
        labels={'distance': 'Distance (km)'},
        color_discrete_sequence=['#636EFA']
    )
    
    # Add mean distance line
    mean_dist = data_with_dist['distance'].mean()
    fig.add_vline(x=mean_dist, line_dash="dash", line_color="red", 
                  annotation_text=f"Mean: {mean_dist:.2f} km", 
                  annotation_position="top right")
    
    # Update layout
    fig.update_layout(
        xaxis_title="Distance (km)",
        yaxis_title="Number of Restaurants",
        bargap=0.1
    )
    
    return fig

def get_distance_statistics(
    data: pd.DataFrame, 
    center_lat: float, 
    center_lng: float
) -> Dict[str, float]:
    """
    Calculate distance statistics from a central point.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        center_lat: Latitude of the central point
        center_lng: Longitude of the central point
        
    Returns:
        Dictionary with distance statistics
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Calculate distance from center for each restaurant (in km)
    cos_lat = np.cos(np.radians(center_lat))
    distances = np.sqrt(
        ((data['latitude'] - center_lat) * 111) ** 2 +
        ((data['longitude'] - center_lng) * 111 * cos_lat) ** 2
    )
    
    # Calculate statistics
    avg_distance = distances.mean()
    max_distance = distances.max()
    count_1km = (distances <= 1).sum()
    count_5km = (distances <= 5).sum()
    
    return {
        'avg_distance': avg_distance,
        'max_distance': max_distance,
        'count_1km': count_1km,
        'count_5km': count_5km
    }

def create_density_map(data: pd.DataFrame) -> go.Figure:
    """
    Create a density map using kernel density estimation.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        
    Returns:
        Plotly figure with density map
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Create a heatmap
    fig = px.density_mapbox(
        data,
        lat='latitude',
        lon='longitude',
        z=data.index,  # Use index for count-based density
        radius=10,
        zoom=10,
        height=600,
        color_continuous_scale='Viridis',
        mapbox_style="open-street-map",
        title="Restaurant Density Map"
    )
    
    fig.update_layout(
        margin={"r": 0, "t": 40, "l": 0, "b": 0},
    )
    
    return fig

def identify_hotspots(data: pd.DataFrame, min_count: int = 5) -> List[Dict[str, Any]]:
    """
    Identify restaurant hotspots based on density.
    
    Args:
        data: DataFrame with restaurant data including latitude and longitude
        min_count: Minimum number of restaurants to consider as a hotspot
        
    Returns:
        List of hotspot details
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    # Use DBSCAN for density-based clustering
    coords = data[['latitude', 'longitude']].values
    
    # Calculate approximate epsilon in kilometers
    # For a proper implementation, this should be tuned based on the dataset
    # or use a proper distance metric like haversine
    avg_lat = coords[:, 0].mean()
    epsilon_km = 0.5  # 500 meters radius
    epsilon_degrees = epsilon_km / 111  # Rough conversion from km to degrees
    
    # Adjust longitude epsilon based on latitude
    epsilon = np.array([epsilon_degrees, epsilon_degrees / np.cos(np.radians(avg_lat))])
    
    # Apply DBSCAN
    db = DBSCAN(
        eps=epsilon.mean(),
        min_samples=min_count,
        metric='euclidean'
    ).fit(coords)
    
    # Get cluster labels
    labels = db.labels_
    
    # Count of clusters (-1 is noise)
    n_clusters = len(set(labels)) - (1 if -1 in labels else 0)
    
    # Prepare hotspot information
    hotspots = []
    
    for cluster_id in range(n_clusters):
        # Get restaurants in this cluster
        cluster_mask = labels == cluster_id
        cluster_points = coords[cluster_mask]
        
        # Calculate cluster center
        center_lat = cluster_points[:, 0].mean()
        center_lng = cluster_points[:, 1].mean()
        
        # Calculate approximate radius (max distance from center)
        cos_lat = np.cos(np.radians(center_lat))
        distances = np.sqrt(
            ((cluster_points[:, 0] - center_lat) * 111) ** 2 +
            ((cluster_points[:, 1] - center_lng) * 111 * cos_lat) ** 2
        )
        radius = distances.max()
        
        # Add to hotspots
        hotspots.append({
            'center_lat': center_lat,
            'center_lng': center_lng,
            'count': np.sum(cluster_mask),
            'radius': radius
        })
    
    # Sort by count (descending)
    hotspots.sort(key=lambda x: x['count'], reverse=True)
    
    return hotspots

def analyze_cuisine_density(data: pd.DataFrame, hotspots: List[Dict[str, Any]]) -> go.Figure:
    """
    Analyze cuisine distribution within hotspots.
    
    Args:
        data: DataFrame with restaurant data
        hotspots: List of hotspot details from identify_hotspots
        
    Returns:
        Plotly figure with cuisine distribution by hotspot
    """
    if 'latitude' not in data.columns or 'longitude' not in data.columns:
        raise ValueError("Data must contain 'latitude' and 'longitude' columns")
    
    if 'cuisine' not in data.columns:
        raise ValueError("Data must contain a 'cuisine' column")
    
    # Get top cuisines
    top_cuisines = data['cuisine'].value_counts().nlargest(5).index.tolist()
    
    # Prepare data for visualization
    hotspot_data = []
    
    for i, hotspot in enumerate(hotspots[:5]):  # Limit to top 5 hotspots
        center_lat = hotspot['center_lat']
        center_lng = hotspot['center_lng']
        radius = hotspot['radius']
        
        # Find restaurants within this hotspot
        cos_lat = np.cos(np.radians(center_lat))
        data['distance_to_hotspot'] = np.sqrt(
            ((data['latitude'] - center_lat) * 111) ** 2 +
            ((data['longitude'] - center_lng) * 111 * cos_lat) ** 2
        )
        
        # Filter to restaurants in hotspot
        hotspot_restaurants = data[data['distance_to_hotspot'] <= radius]
        
        # Count cuisines
        cuisine_counts = hotspot_restaurants['cuisine'].value_counts()
        
        # Add to data
        for cuisine in top_cuisines:
            count = cuisine_counts.get(cuisine, 0)
            hotspot_data.append({
                'Hotspot': f'Hotspot {i+1}',
                'Cuisine': cuisine,
                'Count': count
            })
    
    # Create visualization
    hotspot_df = pd.DataFrame(hotspot_data)
    
    if len(hotspot_df) > 0:
        fig = px.bar(
            hotspot_df,
            x='Hotspot',
            y='Count',
            color='Cuisine',
            title="Cuisine Distribution by Restaurant Hotspot",
            barmode='group'
        )
        
        # Update layout
        fig.update_layout(
            xaxis_title="Hotspot",
            yaxis_title="Number of Restaurants",
        )
    else:
        # Fallback if no data
        fig = go.Figure()
        fig.update_layout(
            title="No cuisine data available for hotspots",
            xaxis_title="Hotspot",
            yaxis_title="Count"
        )
    
    return fig

def create_rating_by_cuisine(data: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing average rating by cuisine.
    
    Args:
        data: DataFrame with restaurant data including cuisine and rating
        
    Returns:
        Plotly figure with bar chart
    """
    if 'cuisine' not in data.columns or 'rating' not in data.columns:
        raise ValueError("Data must contain 'cuisine' and 'rating' columns")
    
    # Calculate average rating by cuisine
    rating_by_cuisine = data.groupby('cuisine')['rating'].mean().reset_index()
    
    # Add count for sizing
    cuisine_counts = data['cuisine'].value_counts().reset_index()
    cuisine_counts.columns = ['cuisine', 'count']
    
    rating_by_cuisine = rating_by_cuisine.merge(cuisine_counts, on='cuisine')
    
    # Sort by rating
    rating_by_cuisine = rating_by_cuisine.sort_values('rating', ascending=False)
    
    # Limit to top cuisines for better visualization
    rating_by_cuisine = rating_by_cuisine.head(15)
    
    # Create bar chart
    fig = px.bar(
        rating_by_cuisine,
        x='cuisine',
        y='rating',
        title="Average Rating by Cuisine Type",
        labels={'cuisine': 'Cuisine Type', 'rating': 'Average Rating'},
        color='rating',
        size='count',
        color_continuous_scale='RdYlGn',
        height=500
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Cuisine Type",
        yaxis_title="Average Rating",
        xaxis={'categoryorder':'total descending'}
    )
    
    return fig

def create_count_by_price(data: pd.DataFrame) -> go.Figure:
    """
    Create a pie chart showing restaurant count by price category.
    
    Args:
        data: DataFrame with restaurant data including price
        
    Returns:
        Plotly figure with pie chart
    """
    if 'price' not in data.columns:
        raise ValueError("Data must contain a 'price' column")
    
    # Get value counts
    price_counts = data['price'].value_counts().reset_index()
    price_counts.columns = ['price', 'count']
    
    # Create pie chart
    fig = px.pie(
        price_counts,
        values='count',
        names='price',
        title="Restaurants by Price Category",
        color_discrete_sequence=px.colors.sequential.Plasma_r
    )
    
    # Update layout
    fig.update_layout(
        legend_title="Price Category"
    )
    
    return fig

def create_rating_vs_price(data: pd.DataFrame) -> go.Figure:
    """
    Create a bar chart showing average rating vs price category.
    
    Args:
        data: DataFrame with restaurant data including rating and price
        
    Returns:
        Plotly figure with bar chart
    """
    if 'price' not in data.columns or 'rating' not in data.columns:
        raise ValueError("Data must contain 'price' and 'rating' columns")
    
    # Calculate average rating by price
    rating_by_price = data.groupby('price')['rating'].mean().reset_index()
    
    # Add count for reference
    price_counts = data['price'].value_counts().reset_index()
    price_counts.columns = ['price', 'count']
    
    rating_by_price = rating_by_price.merge(price_counts, on='price')
    
    # Sort by price if numeric, otherwise by rating
    try:
        rating_by_price = rating_by_price.sort_values('price')
    except:
        rating_by_price = rating_by_price.sort_values('rating', ascending=False)
    
    # Create bar chart
    fig = px.bar(
        rating_by_price,
        x='price',
        y='rating',
        title="Average Rating by Price Category",
        labels={'price': 'Price Category', 'rating': 'Average Rating'},
        color='rating',
        text='count',
        color_continuous_scale='RdYlGn',
        height=500
    )
    
    # Update layout
    fig.update_layout(
        xaxis_title="Price Category",
        yaxis_title="Average Rating"
    )
    
    return fig
