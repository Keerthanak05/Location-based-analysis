import pandas as pd
import numpy as np
from typing import Dict, List, Union, Tuple, Optional
import re

def check_location_columns(data: pd.DataFrame) -> Dict[str, bool]:
    """
    Check if the dataframe has location information (coordinates or addresses).
    
    Args:
        data: Pandas DataFrame containing restaurant data
        
    Returns:
        Dictionary with flags for coordinates and address columns
    """
    # Common names for coordinate columns
    lat_columns = ['lat', 'latitude', 'y', 'ylat']
    lng_columns = ['lng', 'lon', 'longitude', 'x', 'xlong']
    
    # Common names for address columns
    addr_columns = ['address', 'addr', 'location', 'street', 'full_address']
    
    has_coords = any(col.lower() in data.columns.str.lower().tolist() for col in lat_columns) and \
                any(col.lower() in data.columns.str.lower().tolist() for col in lng_columns)
    
    has_address = any(col.lower() in data.columns.str.lower().tolist() for col in addr_columns)
    
    return {
        'has_coords': has_coords,
        'has_address': has_address
    }

def find_column_index(columns: List[str], patterns: List[str]) -> int:
    """
    Find the index of a column that matches one of the given patterns.
    
    Args:
        columns: List of column names
        patterns: List of patterns to match
        
    Returns:
        Index of the matching column or 0 if no match is found
    """
    for pattern in patterns:
        for i, col in enumerate(columns):
            if pattern.lower() in col.lower():
                return i + 1  # +1 because we have an empty option at index 0
    return 0

def clean_column_names(data: pd.DataFrame) -> pd.DataFrame:
    """
    Standardize column names by converting to lowercase and replacing spaces with underscores.
    
    Args:
        data: Pandas DataFrame containing restaurant data
        
    Returns:
        DataFrame with cleaned column names
    """
    data.columns = data.columns.str.lower().str.replace(' ', '_').str.replace('[^a-zA-Z0-9_]', '', regex=True)
    return data

def standardize_columns(
    data: pd.DataFrame,
    name_col: str = None,
    addr_col: str = None,
    lat_col: str = None,
    lng_col: str = None,
    cuisine_col: str = None,
    rating_col: str = None,
    price_col: str = None
) -> pd.DataFrame:
    """
    Standardize the column names for easier analysis.
    
    Args:
        data: Pandas DataFrame containing restaurant data
        name_col: Column containing restaurant names
        addr_col: Column containing restaurant addresses
        lat_col: Column containing latitude
        lng_col: Column containing longitude
        cuisine_col: Column containing cuisine type
        rating_col: Column containing ratings
        price_col: Column containing price information
        
    Returns:
        DataFrame with standardized column names
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Map user-selected columns to standard names
    column_mapping = {}
    
    if name_col and name_col != '':
        column_mapping[name_col] = 'name'
    
    if addr_col and addr_col != '':
        column_mapping[addr_col] = 'address'
    
    if lat_col and lat_col != '':
        column_mapping[lat_col] = 'latitude'
    
    if lng_col and lng_col != '':
        column_mapping[lng_col] = 'longitude'
    
    if cuisine_col and cuisine_col != '':
        column_mapping[cuisine_col] = 'cuisine'
    
    if rating_col and rating_col != '':
        column_mapping[rating_col] = 'rating'
    
    if price_col and price_col != '':
        column_mapping[price_col] = 'price'
    
    # Rename columns
    df = df.rename(columns=column_mapping)
    
    return df

def clean_restaurant_data(data: pd.DataFrame, remove_duplicates: bool = True, handle_missing: bool = True) -> pd.DataFrame:
    """
    Clean restaurant data by handling duplicates, missing values, and outliers.
    
    Args:
        data: Pandas DataFrame containing restaurant data
        remove_duplicates: Whether to remove duplicate restaurants
        handle_missing: Whether to handle missing values
        
    Returns:
        Cleaned DataFrame
    """
    # Create a copy to avoid modifying the original
    df = data.copy()
    
    # Remove duplicates if requested
    if remove_duplicates and 'name' in df.columns:
        # Consider restaurants with the same name and very close locations as duplicates
        if 'latitude' in df.columns and 'longitude' in df.columns:
            # Round coordinates to 5 decimal places (about 1 meter precision)
            df['lat_round'] = df['latitude'].round(5)
            df['lng_round'] = df['longitude'].round(5)
            df = df.drop_duplicates(subset=['name', 'lat_round', 'lng_round'])
            df = df.drop(columns=['lat_round', 'lng_round'])
        else:
            # If no coordinates, just use name
            df = df.drop_duplicates(subset=['name'])
    
    # Handle missing values if requested
    if handle_missing:
        # For essential columns, drop rows with missing values
        essential_cols = ['name']
        if 'latitude' in df.columns and 'longitude' in df.columns:
            essential_cols.extend(['latitude', 'longitude'])
            
        df = df.dropna(subset=essential_cols)
        
        # For non-essential columns, fill missing values
        if 'cuisine' in df.columns:
            df['cuisine'] = df['cuisine'].fillna('Unknown')
        
        if 'rating' in df.columns:
            df['rating'] = df['rating'].fillna(df['rating'].median())
        
        if 'price' in df.columns:
            # If price is numeric
            if df['price'].dtype in [np.float64, np.int64]:
                df['price'] = df['price'].fillna(df['price'].median())
            else:
                # If price is categorical (e.g., '$', '$$', etc.)
                df['price'] = df['price'].fillna(df['price'].mode()[0] if not df['price'].mode().empty else 'Unknown')
    
    return df

def standardize_data_types(data: pd.DataFrame) -> pd.DataFrame:
    """
    Ensure consistent data types for analysis.
    
    Args:
        data: Pandas DataFrame containing restaurant data
        
    Returns:
        DataFrame with standardized data types
    """
    df = data.copy()
    
    # Convert coordinates to float
    if 'latitude' in df.columns:
        df['latitude'] = pd.to_numeric(df['latitude'], errors='coerce')
    
    if 'longitude' in df.columns:
        df['longitude'] = pd.to_numeric(df['longitude'], errors='coerce')
    
    # Convert rating to float
    if 'rating' in df.columns:
        df['rating'] = pd.to_numeric(df['rating'], errors='coerce')
    
    # Standardize price format if it's a string
    if 'price' in df.columns and df['price'].dtype == 'object':
        # Check if price is in currency format (e.g., $, $$, $$$)
        if df['price'].str.contains('\$').any():
            # Count number of $ signs
            df['price'] = df['price'].apply(lambda x: len(str(x)) if isinstance(x, str) and '$' in x else x)
        
        # Try to convert to numeric if possible
        try:
            df['price'] = pd.to_numeric(df['price'], errors='coerce')
        except:
            pass
    
    return df

def simulate_geocoding(data: pd.DataFrame) -> pd.DataFrame:
    """
    Simulate geocoding by generating random coordinates for addresses.
    This is a placeholder for a real geocoding service.
    
    Args:
        data: Pandas DataFrame containing restaurant data with addresses
        
    Returns:
        DataFrame with added latitude and longitude columns
    """
    df = data.copy()
    
    # Check if we have address but no coordinates
    if 'address' in df.columns and ('latitude' not in df.columns or 'longitude' not in df.columns):
        # Generate random coordinates centered around a plausible area
        # This is just for demonstration - in a real app, use a geocoding service
        center_lat, center_lng = 40.7128, -74.0060  # New York City center
        
        # Generate random offsets (roughly within city limits)
        np.random.seed(42)  # For reproducibility
        lat_offsets = np.random.uniform(-0.1, 0.1, size=len(df))
        lng_offsets = np.random.uniform(-0.1, 0.1, size=len(df))
        
        # Add columns
        df['latitude'] = center_lat + lat_offsets
        df['longitude'] = center_lng + lng_offsets
    
    return df

def process_data(
    data: pd.DataFrame,
    name_col: str = None,
    addr_col: str = None,
    lat_col: str = None,
    lng_col: str = None,
    cuisine_col: str = None,
    rating_col: str = None,
    price_col: str = None,
    remove_duplicates: bool = True,
    handle_missing: bool = True,
    geocode: bool = False
) -> pd.DataFrame:
    """
    Process restaurant data for analysis.
    
    Args:
        data: Pandas DataFrame containing restaurant data
        name_col: Column containing restaurant names
        addr_col: Column containing restaurant addresses
        lat_col: Column containing latitude
        lng_col: Column containing longitude
        cuisine_col: Column containing cuisine type
        rating_col: Column containing ratings
        price_col: Column containing price information
        remove_duplicates: Whether to remove duplicate restaurants
        handle_missing: Whether to handle missing values
        geocode: Whether to perform geocoding if coordinates are missing
        
    Returns:
        Processed DataFrame ready for analysis
    """
    # Standardize column names
    df = standardize_columns(
        data,
        name_col,
        addr_col,
        lat_col,
        lng_col,
        cuisine_col,
        rating_col,
        price_col
    )
    
    # Clean the data
    df = clean_restaurant_data(df, remove_duplicates, handle_missing)
    
    # Standardize data types
    df = standardize_data_types(df)
    
    # Geocode if requested
    if geocode:
        df = simulate_geocoding(df)
    
    return df
