import pandas as pd
import numpy as np
import base64
import io
from typing import Optional, List, Dict, Any

def get_example_data() -> pd.DataFrame:
    """
    Generate example restaurant data for testing purposes.
    
    Returns:
        DataFrame with example restaurant data
    """
    # This is just for demonstration when no data is uploaded
    # In a real application, we would avoid generating synthetic data
    
    # Number of example restaurants
    n = 50
    
    # Set random seed for reproducibility
    np.random.seed(42)
    
    # Generate data
    data = {
        'name': [f"Restaurant {i+1}" for i in range(n)],
        'address': [f"{np.random.randint(1, 1000)} Main St, City" for _ in range(n)],
        'latitude': np.random.uniform(40.7, 40.8, n),  # NYC area
        'longitude': np.random.uniform(-74.05, -73.95, n),
        'cuisine': np.random.choice(
            ['Italian', 'Mexican', 'Chinese', 'American', 'Japanese', 'Thai', 'Indian', 'French'],
            n
        ),
        'rating': np.random.uniform(2.0, 5.0, n),
        'price': np.random.choice([1, 2, 3, 4], n, p=[0.3, 0.4, 0.2, 0.1])
    }
    
    return pd.DataFrame(data)

def generate_download_link(df: pd.DataFrame, file_format: str = 'csv') -> str:
    """
    Generate a download link for a DataFrame.
    
    Args:
        df: DataFrame to download
        file_format: Format to download ('csv', 'excel', or 'json')
        
    Returns:
        HTML link for downloading the data
    """
    if file_format == 'csv':
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        href = f'<a href="data:file/csv;base64,{b64}" download="restaurant_data.csv">Download CSV File</a>'
    elif file_format == 'excel':
        towrite = io.BytesIO()
        df.to_excel(towrite, index=False)
        towrite.seek(0)
        b64 = base64.b64encode(towrite.read()).decode()
        href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="restaurant_data.xlsx">Download Excel File</a>'
    elif file_format == 'json':
        json_str = df.to_json(orient='records')
        b64 = base64.b64encode(json_str.encode()).decode()
        href = f'<a href="data:file/json;base64,{b64}" download="restaurant_data.json">Download JSON File</a>'
    else:
        href = "Unsupported file format"
    
    return href

def haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great circle distance between two points on the earth.
    
    Args:
        lat1: Latitude of point 1 (in degrees)
        lon1: Longitude of point 1 (in degrees)
        lat2: Latitude of point 2 (in degrees)
        lon2: Longitude of point 2 (in degrees)
        
    Returns:
        Distance in kilometers
    """
    # Convert decimal degrees to radians
    lat1, lon1, lat2, lon2 = map(np.radians, [lat1, lon1, lat2, lon2])
    
    # Haversine formula
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = np.sin(dlat/2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon/2)**2
    c = 2 * np.arcsin(np.sqrt(a))
    r = 6371  # Radius of earth in kilometers
    
    return c * r
