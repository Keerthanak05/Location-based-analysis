import streamlit as st
import pandas as pd
import numpy as np
import base64
import io
from io import StringIO

import data_processing as dp
import visualization as viz
import analysis as analysis
import utils

# Set page config
st.set_page_config(page_title="Restaurant Geo-Analysis Tool",
                   page_icon="🍽️",
                   layout="wide",
                   initial_sidebar_state="expanded")

# Initialize session state variables if they don't exist
if 'data' not in st.session_state:
    st.session_state.data = None
if 'cleaned_data' not in st.session_state:
    st.session_state.cleaned_data = None
if 'has_geo_data' not in st.session_state:
    st.session_state.has_geo_data = False
if 'map_created' not in st.session_state:
    st.session_state.map_created = False

# Sidebar for data upload and controls
with st.sidebar:
    st.title("🍽️ Restaurant Geo-Analysis")
    st.write(
        "Upload your restaurant data to analyze geographic patterns, ratings, and more."
    )

    # File upload
    uploaded_file = st.file_uploader("Upload Restaurant Data (CSV or Excel)",
                                     type=['csv', 'xlsx', 'xls'])

    # Option to use example data
    use_example_data = st.checkbox(
        "Don't have data? Try our example restaurant dataset", value=False)

    if use_example_data:
        # Generate example data for testing
        st.info("Using auto-generated sample data for demonstration purposes.")
        st.session_state.data = utils.get_example_data()

        # Display data preview
        st.subheader("Data Preview")
        st.dataframe(st.session_state.data.head(3))

        # Data info
        st.text(
            f"Rows: {st.session_state.data.shape[0]}, Columns: {st.session_state.data.shape[1]}"
        )

        # Since example data has coordinates, set has_geo_data to True
        st.session_state.has_geo_data = True
        st.success("✅ Geographic coordinates detected in example data")

    elif uploaded_file is not None:
        try:
            # Check file type and read accordingly
            if uploaded_file.name.endswith('.csv'):
                data = pd.read_csv(uploaded_file)
            else:  # Excel files
                data = pd.read_excel(uploaded_file)

            # Store the data in session state
            st.session_state.data = data

            # Display data preview
            st.subheader("Data Preview")
            st.dataframe(data.head(3))

            # Data info
            st.text(f"Rows: {data.shape[0]}, Columns: {data.shape[1]}")

            # Check if there are location columns
            location_check = dp.check_location_columns(data)
            if location_check['has_coords']:
                st.session_state.has_geo_data = True
                st.success("✅ Geographic coordinates detected")
            elif location_check['has_address']:
                st.warning(
                    "⚠️ Address data found but no coordinates. Use 'Process Data' to geocode addresses."
                )
            else:
                st.error(
                    "❌ No geographic data detected. Please ensure your data includes latitude/longitude or address information."
                )

        except Exception as e:
            st.error(f"Error loading data: {e}")

    # Sidebar navigation
    st.subheader("Navigation")
    page = st.radio(
        "Go to",
        ["Data Processing", "Visualization", "Analysis", "Export & Share"])

# Main content area
st.title("Restaurant Geographic Analysis Tool")

# Page routing
if page == "Data Processing":
    st.header("Data Processing")

    if st.session_state.data is not None:
        # Column selection
        st.subheader("Column Configuration")

        cols = st.session_state.data.columns.tolist()

        # Required columns for analysis
        col1, col2 = st.columns(2)
        with col1:
            name_col = st.selectbox("Restaurant Name Column",
                                    options=[''] + cols,
                                    index=dp.find_column_index(
                                        cols, ['name', 'restaurant', 'place']))

            lat_col = st.selectbox("Latitude Column",
                                   options=[''] + cols,
                                   index=dp.find_column_index(
                                       cols, ['lat', 'latitude', 'y']))

            cuisine_col = st.selectbox(
                "Cuisine Column",
                options=[''] + cols,
                index=dp.find_column_index(
                    cols, ['cuisine', 'type', 'food', 'category']))

        with col2:
            addr_col = st.selectbox(
                "Address Column",
                options=[''] + cols,
                index=dp.find_column_index(
                    cols, ['address', 'addr', 'location', 'street']))

            lng_col = st.selectbox("Longitude Column",
                                   options=[''] + cols,
                                   index=dp.find_column_index(
                                       cols, ['lng', 'lon', 'longitude', 'x']))

            rating_col = st.selectbox("Rating Column",
                                      options=[''] + cols,
                                      index=dp.find_column_index(
                                          cols, ['rating', 'stars', 'score']))

        price_col = st.selectbox("Price Range Column",
                                 options=[''] + cols,
                                 index=dp.find_column_index(
                                     cols, ['price', 'price_range', 'cost']))

        # Data cleaning options
        st.subheader("Data Cleaning Options")

        remove_duplicates = st.checkbox("Remove duplicate restaurants",
                                        value=True)
        handle_missing = st.checkbox("Handle missing values", value=True)

        # Geocoding section - only show if lat/lng not available
        if not st.session_state.has_geo_data and addr_col:
            st.subheader("Geocoding")
            st.warning(
                "This feature would normally use a geocoding service API to convert addresses to coordinates. For this application, we'll simulate geocoding with random coordinates."
            )
            geocode_data = st.button("Simulate Geocoding Addresses")

            if geocode_data:
                with st.spinner('Simulating geocoding addresses...'):
                    # Processing data with selected columns
                    cleaned_data = dp.process_data(
                        st.session_state.data,
                        name_col=name_col,
                        addr_col=addr_col,
                        lat_col=lat_col,
                        lng_col=lng_col,
                        cuisine_col=cuisine_col,
                        rating_col=rating_col,
                        price_col=price_col,
                        remove_duplicates=remove_duplicates,
                        handle_missing=handle_missing,
                        geocode=True)

                    st.session_state.cleaned_data = cleaned_data
                    st.session_state.has_geo_data = True
                    st.success(
                        "Geocoding completed! Your data now contains geographic coordinates."
                    )
                    st.dataframe(cleaned_data.head())

        # Process data button
        process_data = st.button("Process Data")

        if process_data:
            with st.spinner('Processing data...'):
                # Processing data with selected columns
                cleaned_data = dp.process_data(
                    st.session_state.data,
                    name_col=name_col,
                    addr_col=addr_col,
                    lat_col=lat_col,
                    lng_col=lng_col,
                    cuisine_col=cuisine_col,
                    rating_col=rating_col,
                    price_col=price_col,
                    remove_duplicates=remove_duplicates,
                    handle_missing=handle_missing,
                    geocode=False)

                st.session_state.cleaned_data = cleaned_data
                st.success("Data processed successfully!")
                st.dataframe(cleaned_data.head())

                # Basic statistics
                st.subheader("Basic Statistics")
                if cuisine_col and cuisine_col in cleaned_data.columns:
                    top_cuisines = cleaned_data[cuisine_col].value_counts(
                    ).head(5)
                    st.write("Top cuisines:", top_cuisines)

                if rating_col and rating_col in cleaned_data.columns:
                    st.write(
                        f"Average rating: {cleaned_data[rating_col].mean():.2f}"
                    )
    else:
        st.info("Please upload data using the sidebar to begin.")

elif page == "Visualization":
    st.header("Geographic Visualization")

    if st.session_state.cleaned_data is not None and st.session_state.has_geo_data:
        data = st.session_state.cleaned_data

        # Map type selection
        map_type = st.selectbox(
            "Select Map Type",
            ["Basic Location Map", "Heatmap", "Cluster Map", "Choropleth Map"])

        # Columns to use for visualization
        vis_cols = data.columns.tolist()
        color_by = st.selectbox("Color by",
                                options=['None'] + vis_cols,
                                index=0)
        size_by = st.selectbox("Size by", options=['None'] + vis_cols, index=0)

        # Filter options
        st.subheader("Filter Data (Optional)")

        # Cuisine filter
        if 'cuisine' in data.columns:
            cuisines = ['All'] + sorted(data['cuisine'].unique().tolist())
            selected_cuisine = st.selectbox("Filter by Cuisine", cuisines)

        # Rating filter
        if 'rating' in data.columns:
            min_rating, max_rating = data['rating'].min(), data['rating'].max()
            rating_filter = st.slider("Minimum Rating", min_rating, max_rating,
                                      min_rating)

        # Price filter
        if 'price' in data.columns:
            price_categories = ['All'] + sorted(
                data['price'].unique().tolist())
            selected_price = st.selectbox("Filter by Price", price_categories)

        # Apply filters
        filtered_data = data.copy()

        if 'cuisine' in data.columns and selected_cuisine != 'All':
            filtered_data = filtered_data[filtered_data['cuisine'] ==
                                          selected_cuisine]

        if 'rating' in data.columns:
            filtered_data = filtered_data[filtered_data['rating'] >=
                                          rating_filter]

        if 'price' in data.columns and selected_price != 'All':
            filtered_data = filtered_data[filtered_data['price'] ==
                                          selected_price]

        # Display map
        st.subheader(f"Restaurant Map: {map_type}")

        if len(filtered_data) > 0:
            if map_type == "Basic Location Map":
                map_fig = viz.create_location_map(filtered_data, color_by,
                                                  size_by)
                st.plotly_chart(map_fig, use_container_width=True)

            elif map_type == "Heatmap":
                map_fig = viz.create_heatmap(filtered_data)
                st.plotly_chart(map_fig, use_container_width=True)

            elif map_type == "Cluster Map":
                map_fig = viz.create_cluster_map(filtered_data, color_by)
                st.plotly_chart(map_fig, use_container_width=True)

            elif map_type == "Choropleth Map":
                st.write(
                    "Choropleth maps are useful for aggregate data by regions. For a full implementation, we would need to join the restaurant data with region boundaries."
                )
                map_fig = viz.create_location_map(filtered_data, color_by,
                                                  size_by)
                st.plotly_chart(map_fig, use_container_width=True)

            # Display data table
            with st.expander("View Filtered Data"):
                st.dataframe(filtered_data)

            # Map analytics
            st.subheader("Map Analytics")
            st.write(
                f"Displaying {len(filtered_data)} restaurants out of {len(data)} total"
            )

            # Location details
            try:
                center_lat = filtered_data['latitude'].mean()
                center_lng = filtered_data['longitude'].mean()
                st.write(
                    f"Map centered at: {center_lat:.4f}, {center_lng:.4f}")
            except:
                pass
        else:
            st.warning(
                "No data to display after applying filters. Please adjust your filter criteria."
            )

    elif st.session_state.data is not None:
        st.warning(
            "Please process your data first and ensure it contains geographic coordinates."
        )
    else:
        st.info("Please upload and process data to create visualizations.")

elif page == "Analysis":
    st.header("Data Analysis")

    if st.session_state.cleaned_data is not None:
        data = st.session_state.cleaned_data

        # Analysis type selection
        analysis_type = st.selectbox("Select Analysis Type", [
            "Distribution Analysis", "Correlation Analysis",
            "Clustering Analysis", "Spatial Analysis"
        ])

        if analysis_type == "Distribution Analysis":
            st.subheader("Distribution Analysis")

            # Column to analyze
            numeric_cols = data.select_dtypes(
                include=['float64', 'int64']).columns.tolist()
            categorical_cols = data.select_dtypes(
                include=['object', 'category']).columns.tolist()

            dist_col_type = st.radio("Distribution type",
                                     ["Numeric", "Categorical"])

            if dist_col_type == "Numeric" and numeric_cols:
                dist_col = st.selectbox(
                    "Select column for distribution analysis", numeric_cols)

                # Generate distribution plot
                fig = analysis.create_distribution_plot(data, dist_col)
                st.plotly_chart(fig, use_container_width=True)

                # Statistics
                st.subheader(f"Statistics for {dist_col}")
                stats = data[dist_col].describe()
                st.write(stats)

            elif dist_col_type == "Categorical" and categorical_cols:
                dist_col = st.selectbox(
                    "Select column for distribution analysis",
                    categorical_cols)
                limit = st.slider("Number of categories to show", 5, 30, 10)

                # Generate bar chart
                fig = analysis.create_categorical_distribution(
                    data, dist_col, limit)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning(
                    f"No {dist_col_type.lower()} columns found in the data.")

        elif analysis_type == "Correlation Analysis":
            st.subheader("Correlation Analysis")

            # Only use numeric columns for correlation
            numeric_data = data.select_dtypes(include=['float64', 'int64'])

            if len(numeric_data.columns) >= 2:
                # Correlation matrix
                fig = analysis.create_correlation_matrix(numeric_data)
                st.plotly_chart(fig, use_container_width=True)

                # Scatter plot for selected variables
                st.subheader("Scatter Plot")

                col1, col2 = st.columns(2)
                with col1:
                    x_var = st.selectbox("X-axis", numeric_data.columns)
                with col2:
                    y_var = st.selectbox("Y-axis",
                                         numeric_data.columns,
                                         index=min(
                                             1,
                                             len(numeric_data.columns) - 1))

                if 'cuisine' in data.columns:
                    color_by = st.checkbox("Color by cuisine", value=True)
                else:
                    color_by = False

                fig = analysis.create_scatter_plot(data,
                                                   x_var,
                                                   y_var,
                                                   color_by_cuisine=color_by)
                st.plotly_chart(fig, use_container_width=True)

            else:
                st.warning(
                    "Need at least two numeric columns for correlation analysis."
                )

        elif analysis_type == "Clustering Analysis":
            st.subheader("Restaurant Clustering Analysis")

            # Select clustering features
            st.write("Select features for clustering")

            numeric_cols = data.select_dtypes(
                include=['float64', 'int64']).columns.tolist()

            if len(
                    numeric_cols
            ) >= 2 and 'latitude' in data.columns and 'longitude' in data.columns:
                use_location = st.checkbox(
                    "Use geographic location for clustering", value=True)

                other_features = [
                    col for col in numeric_cols
                    if col not in ['latitude', 'longitude']
                ]
                selected_features = st.multiselect(
                    "Additional features for clustering", other_features)

                if use_location or selected_features:
                    n_clusters = st.slider("Number of clusters", 2, 10, 5)

                    # Run clustering
                    cluster_features = []
                    if use_location:
                        cluster_features.extend(['latitude', 'longitude'])
                    cluster_features.extend(selected_features)

                    clustered_data = analysis.perform_clustering(
                        data, cluster_features, n_clusters)

                    # Show clustering result on map
                    st.subheader("Clustering Results")
                    cluster_map = viz.create_cluster_result_map(clustered_data)
                    st.plotly_chart(cluster_map, use_container_width=True)

                    # Cluster analysis
                    st.subheader("Cluster Profiles")
                    cluster_profile = analysis.analyze_clusters(clustered_data)
                    st.write(cluster_profile)

                    # Visualize cluster characteristics
                    fig = analysis.visualize_cluster_characteristics(
                        clustered_data)
                    st.plotly_chart(fig, use_container_width=True)

                else:
                    st.warning(
                        "Please select at least one feature for clustering.")
            else:
                st.error(
                    "Need geographic coordinates and at least one additional numeric feature for clustering."
                )

        elif analysis_type == "Spatial Analysis":
            st.subheader("Spatial Analysis")

            if 'latitude' in data.columns and 'longitude' in data.columns:
                # Spatial analysis options
                spatial_method = st.selectbox(
                    "Select Spatial Analysis Method", [
                        "Nearest Neighbor Analysis", "Distance Distribution",
                        "Spatial Density"
                    ])

                if spatial_method == "Nearest Neighbor Analysis":
                    st.write(
                        "Analyzing distribution patterns to determine if restaurants are clustered, random, or evenly dispersed."
                    )
                    nn_results = analysis.nearest_neighbor_analysis(data)

                    # Display results
                    col1, col2, col3 = st.columns(3)
                    col1.metric("Average NN Distance",
                                f"{nn_results['avg_nn_distance']:.2f} km")
                    col2.metric("NN Index", f"{nn_results['nn_index']:.2f}")

                    # Interpretation
                    st.subheader("Interpretation")
                    if nn_results['nn_index'] < 0.8:
                        col3.metric("Pattern", "Clustered")
                        st.write(
                            "Restaurants show a clustered pattern, indicating concentrated areas of restaurant activity."
                        )
                    elif nn_results['nn_index'] > 1.2:
                        col3.metric("Pattern", "Dispersed")
                        st.write(
                            "Restaurants are evenly dispersed, suggesting planning or competition effects."
                        )
                    else:
                        col3.metric("Pattern", "Random")
                        st.write(
                            "Restaurants follow a random distribution pattern."
                        )

                    # Visualization
                    nn_fig = analysis.plot_nearest_neighbors(data)
                    st.plotly_chart(nn_fig, use_container_width=True)

                elif spatial_method == "Distance Distribution":
                    st.write("Analyzing distances between restaurants")

                    # Central point selection
                    center_method = st.radio("Center point selection", [
                        "Use geographic center",
                        "Select a restaurant as center"
                    ])

                    if center_method == "Use geographic center":
                        center_lat = data['latitude'].mean()
                        center_lng = data['longitude'].mean()
                        center_name = "Geographic Center"
                    else:
                        selected_restaurant = st.selectbox(
                            "Select central restaurant", data['name'].tolist())
                        center_rest = data[data['name'] ==
                                           selected_restaurant].iloc[0]
                        center_lat = center_rest['latitude']
                        center_lng = center_rest['longitude']
                        center_name = selected_restaurant

                    # Calculate and visualize distances
                    distance_fig = analysis.analyze_distance_distribution(
                        data, center_lat, center_lng, center_name)
                    st.plotly_chart(distance_fig, use_container_width=True)

                    # Distance statistics
                    distance_data = analysis.get_distance_statistics(
                        data, center_lat, center_lng)

                    col1, col2, col3 = st.columns(3)
                    col1.metric("Average Distance",
                                f"{distance_data['avg_distance']:.2f} km")
                    col2.metric("Max Distance",
                                f"{distance_data['max_distance']:.2f} km")
                    col3.metric("Restaurants within 1km",
                                f"{distance_data['count_1km']}")

                elif spatial_method == "Spatial Density":
                    st.write(
                        "Analyzing the density of restaurants across the area")

                    # Create density map
                    density_fig = analysis.create_density_map(data)
                    st.plotly_chart(density_fig, use_container_width=True)

                    # Density insights
                    hotspots = analysis.identify_hotspots(data)

                    st.subheader("Restaurant Density Insights")
                    st.write(f"Identified {len(hotspots)} restaurant hotspots")

                    # Display hotspot info
                    for i, hotspot in enumerate(hotspots[:5]):
                        st.write(
                            f"Hotspot {i+1}: {hotspot['count']} restaurants within {hotspot['radius']}km radius of {hotspot['center_lat']:.4f}, {hotspot['center_lng']:.4f}"
                        )

                    # Density analytics
                    if 'cuisine' in data.columns:
                        st.subheader("Cuisine Type Distribution in Hotspots")
                        cuisine_density = analysis.analyze_cuisine_density(
                            data, hotspots)
                        st.plotly_chart(cuisine_density,
                                        use_container_width=True)
            else:
                st.error(
                    "Spatial analysis requires latitude and longitude data.")
    else:
        st.info("Please upload and process data to perform analysis.")

elif page == "Export & Share":
    st.header("Export & Share Insights")

    if st.session_state.cleaned_data is not None:
        data = st.session_state.cleaned_data

        # Export options
        st.subheader("Export Data")

        col1, col2 = st.columns(2)
        with col1:
            export_format = st.radio("Select export format",
                                     ["CSV", "Excel", "JSON"])

            # Export selection options
            export_all = st.checkbox("Export all data", value=True)
            if not export_all:
                selected_columns = st.multiselect(
                    "Select columns to export",
                    data.columns.tolist(),
                    default=data.columns.tolist()[:min(5, len(data.columns))])
                export_data = data[
                    selected_columns] if selected_columns else data
            else:
                export_data = data

        with col2:
            # Show data preview before export
            st.write("Data Preview (first 5 rows)")
            if export_all:
                st.dataframe(data.head())
            else:
                if 'selected_columns' in locals() and selected_columns:
                    st.dataframe(data[selected_columns].head())
                else:
                    st.dataframe(data.head())

        # Add file name option
        file_prefix = st.text_input("File name prefix",
                                    "restaurant_data_export")

        # Generate download link
        if st.button("Generate Export File"):
            if export_format == "CSV":
                csv = export_data.to_csv(index=False)
                b64 = base64.b64encode(csv.encode()).decode()
                href = f'<a href="data:file/csv;base64,{b64}" download="{file_prefix}.csv">Download CSV File</a>'
            elif export_format == "Excel":
                towrite = io.BytesIO()
                export_data.to_excel(towrite, index=False)
                towrite.seek(0)
                b64 = base64.b64encode(towrite.read()).decode()
                href = f'<a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{file_prefix}.xlsx">Download Excel File</a>'
            else:  # JSON
                json_str = export_data.to_json(orient='records')
                b64 = base64.b64encode(json_str.encode()).decode()
                href = f'<a href="data:file/json;base64,{b64}" download="{file_prefix}.json">Download JSON File</a>'

            st.success("✅ Export file generated successfully!")
            st.markdown(href, unsafe_allow_html=True)

        # Share visualizations
        st.subheader("Save & Share Visualizations")

        # Create visualization for sharing
        viz_type = st.selectbox("Visualization to create", [
            "Restaurant Map", "Rating Distribution", "Cuisine Distribution",
            "Custom Analysis"
        ])

        # Configuration options for visualization export
        st.write("Export Settings:")
        viz_file_name = st.text_input(
            "Visualization file name",
            f"restaurant_{viz_type.lower().replace(' ', '_')}")

        col1, col2 = st.columns(2)
        with col1:
            export_format = st.radio("Export format",
                                     ["HTML", "PNG", "SVG", "PDF"])
        with col2:
            viz_width = st.number_input("Width (pixels)",
                                        min_value=600,
                                        max_value=2000,
                                        value=1000,
                                        step=100)
            viz_height = st.number_input("Height (pixels)",
                                         min_value=400,
                                         max_value=1500,
                                         value=600,
                                         step=100)

        if viz_type == "Restaurant Map":
            # Map customization options
            st.write("Map Configuration:")
            map_color_by = st.selectbox(
                "Color points by", ['None', 'rating', 'cuisine', 'price'],
                index=1 if 'rating' in data.columns else 0)
            color_by_val = map_color_by if map_color_by != 'None' else None

            map_size_by = st.selectbox("Size points by",
                                       ['None', 'rating', 'price'],
                                       index=0)
            size_by_val = map_size_by if map_size_by != 'None' else None

            # Create map for sharing
            st.write("Restaurant Location Map:")
            map_fig = viz.create_location_map(data,
                                              color_by=color_by_val,
                                              size_by=size_by_val)
            map_fig.update_layout(width=viz_width, height=viz_height)
            st.plotly_chart(map_fig, use_container_width=True)

            # Export map options
            if st.button("Save Map Visualization"):
                # Generate HTML for the visualization that could be downloaded
                html_bytes = map_fig.to_html(include_plotlyjs="cdn").encode()
                b64 = base64.b64encode(html_bytes).decode()
                href = f'<a href="data:text/html;base64,{b64}" download="{viz_file_name}.html">Download {export_format} Visualization</a>'
                st.markdown(href, unsafe_allow_html=True)
                st.success(
                    f"✅ Map visualization ready for download as {export_format}"
                )

        elif viz_type == "Rating Distribution":
            if 'rating' in data.columns:
                # Rating visualization options
                st.write("Rating Distribution Configuration:")
                bin_count = st.slider("Number of bins",
                                      min_value=5,
                                      max_value=50,
                                      value=20)

                # Create visualization
                st.write("Restaurant Rating Distribution:")
                fig = analysis.create_distribution_plot(data, 'rating')
                fig.update_layout(width=viz_width, height=viz_height)
                st.plotly_chart(fig, use_container_width=True)

                # Export visualization
                if st.button("Save Rating Visualization"):
                    html_bytes = fig.to_html(include_plotlyjs="cdn").encode()
                    b64 = base64.b64encode(html_bytes).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="{viz_file_name}.html">Download {export_format} Visualization</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success(
                        f"✅ Rating distribution visualization ready for download as {export_format}"
                    )
            else:
                st.warning("Rating data not available in the dataset.")

        elif viz_type == "Cuisine Distribution":
            if 'cuisine' in data.columns:
                # Cuisine visualization options
                st.write("Cuisine Distribution Configuration:")
                cuisine_limit = st.slider("Number of cuisines to show",
                                          min_value=5,
                                          max_value=30,
                                          value=10)

                # Create visualization
                st.write("Restaurant Cuisine Distribution:")
                fig = analysis.create_categorical_distribution(
                    data, 'cuisine', cuisine_limit)
                fig.update_layout(width=viz_width, height=viz_height)
                st.plotly_chart(fig, use_container_width=True)

                # Export visualization
                if st.button("Save Cuisine Visualization"):
                    html_bytes = fig.to_html(include_plotlyjs="cdn").encode()
                    b64 = base64.b64encode(html_bytes).decode()
                    href = f'<a href="data:text/html;base64,{b64}" download="{viz_file_name}.html">Download {export_format} Visualization</a>'
                    st.markdown(href, unsafe_allow_html=True)
                    st.success(
                        f"✅ Cuisine distribution visualization ready for download as {export_format}"
                    )
            else:
                st.warning("Cuisine data not available in the dataset.")

        elif viz_type == "Custom Analysis":
            st.write("Create a custom analysis")

            # Custom analysis options
            if 'rating' in data.columns and 'cuisine' in data.columns:
                analysis_metric = st.selectbox("Analysis metric", [
                    "Average Rating by Cuisine",
                    "Restaurant Count by Price Category",
                    "Rating vs. Price Analysis"
                ])

                # Create and display the selected analysis
                if analysis_metric == "Average Rating by Cuisine":
                    min_count = st.slider("Minimum restaurants per cuisine", 1,
                                          10, 2)
                    fig = analysis.create_rating_by_cuisine(data)
                    fig.update_layout(width=viz_width, height=viz_height)
                    st.plotly_chart(fig, use_container_width=True)

                elif analysis_metric == "Restaurant Count by Price Category":
                    if 'price' in data.columns:
                        fig = analysis.create_count_by_price(data)
                        fig.update_layout(width=viz_width, height=viz_height)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(
                            "Price category data not available in the dataset."
                        )

                elif analysis_metric == "Rating vs. Price Analysis":
                    if 'price' in data.columns:
                        fig = analysis.create_rating_vs_price(data)
                        fig.update_layout(width=viz_width, height=viz_height)
                        st.plotly_chart(fig, use_container_width=True)
                    else:
                        st.warning(
                            "Price category data not available in the dataset."
                        )

                # Export the analysis
                if st.button("Save Custom Analysis"):
                    try:
                        html_bytes = fig.to_html(
                            include_plotlyjs="cdn").encode()
                        b64 = base64.b64encode(html_bytes).decode()
                        href = f'<a href="data:text/html;base64,{b64}" download="{viz_file_name}.html">Download {export_format} Visualization</a>'
                        st.markdown(href, unsafe_allow_html=True)
                        st.success(
                            f"✅ Custom analysis visualization ready for download as {export_format}"
                        )
                    except:
                        st.error(
                            "Could not generate visualization. Please ensure you have selected a valid analysis type with available data."
                        )
            else:
                st.warning(
                    "Required data fields (rating, cuisine) not available for custom analysis."
                )

        # Create report
        st.subheader("Generate Report")

        # Report configuration settings
        col1, col2 = st.columns(2)
        with col1:
            report_title = st.text_input(
                "Report Title", "Restaurant Geographic Analysis Report")
            report_filename = st.text_input("Report Filename",
                                            "restaurant_analysis_report")
        with col2:
            report_format = st.radio("Report Format", ["HTML", "PDF"])
            report_include_intro = st.checkbox("Include introduction",
                                               value=True)

        include_sections = st.multiselect("Sections to include", [
            "Data Summary", "Geographic Distribution", "Rating Analysis",
            "Cuisine Analysis", "Price Analysis", "Spatial Patterns"
        ],
                                          default=[
                                              "Data Summary",
                                              "Geographic Distribution",
                                              "Rating Analysis"
                                          ])

        # Generate the report
        if st.button("Generate Report"):
            st.subheader(report_title)

            # Initialize HTML content for the report
            report_html = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{report_title}</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                    h1 {{ color: #2c3e50; }}
                    h2 {{ color: #3498db; border-bottom: 1px solid #eee; padding-bottom: 10px; }}
                    .date {{ color: #7f8c8d; font-size: 0.9em; }}
                    .summary {{ background-color: #f8f9fa; padding: 15px; border-radius: 5px; }}
                    .footer {{ margin-top: 50px; text-align: center; font-size: 0.8em; color: #7f8c8d; }}
                    hr {{ border: 0; height: 1px; background-color: #eee; margin: 30px 0; }}
                    img {{ max-width: 100%; height: auto; }}
                </style>
                <script src="https://cdn.plot.ly/plotly-latest.min.js"></script>
            </head>
            <body>
                <h1>{report_title}</h1>
                <p class="date">Generated on: {pd.Timestamp.now().strftime('%Y-%m-%d')}</p>
            """

            # Add introduction if selected
            if report_include_intro:
                report_html += f"""
                <div class="summary">
                    <p>This report provides analysis of restaurant data across geographic regions. 
                    It includes visualizations and statistics to help understand patterns and insights from the data.</p>
                    <p>Total restaurants analyzed: <strong>{len(data)}</strong></p>
                </div>
                <hr>
                """

            # Add table of contents
            report_html += """
            <h2>Table of Contents</h2>
            <ol>
            """

            for section in include_sections:
                report_html += f"<li><a href='#{section.lower().replace(' ', '-')}'>{section}</a></li>\n"

            report_html += """
            </ol>
            <hr>
            """

            # Generate selected report sections
            if "Data Summary" in include_sections:
                report_html += """
                <h2 id="data-summary">Data Summary</h2>
                <table border="1" cellpadding="5" style="border-collapse: collapse; width: 100%;">
                    <tr style="background-color: #f2f2f2;">
                        <th>Metric</th>
                        <th>Value</th>
                    </tr>
                """

                report_html += f"""
                    <tr>
                        <td>Total restaurants</td>
                        <td>{len(data)}</td>
                    </tr>
                """

                if 'cuisine' in data.columns:
                    report_html += f"""
                    <tr>
                        <td>Unique cuisine types</td>
                        <td>{data['cuisine'].nunique()}</td>
                    </tr>
                    """

                if 'rating' in data.columns:
                    report_html += f"""
                    <tr>
                        <td>Average rating</td>
                        <td>{data['rating'].mean():.2f}</td>
                    </tr>
                    <tr>
                        <td>Highest rated restaurant</td>
                        <td>{data.loc[data['rating'].idxmax(), 'name'] if 'name' in data.columns else 'N/A'} ({data['rating'].max():.1f})</td>
                    </tr>
                    """

                if 'price' in data.columns:
                    report_html += f"""
                    <tr>
                        <td>Average price category</td>
                        <td>{data['price'].mean():.1f}</td>
                    </tr>
                    """

                report_html += """
                </table>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Data Summary")
                st.write(f"Total restaurants: {len(data)}")
                if 'cuisine' in data.columns:
                    st.write(f"Cuisine types: {data['cuisine'].nunique()}")
                if 'rating' in data.columns:
                    st.write(f"Average rating: {data['rating'].mean():.2f}")
                st.write("---")

            if "Geographic Distribution" in include_sections:
                # Create the visualization
                geo_fig = viz.create_location_map(data, color_by='rating')

                # Add to HTML report (placeholder for real implementation)
                report_html += """
                <h2 id="geographic-distribution">Geographic Distribution</h2>
                <p>The map below shows the geographic distribution of restaurants in the dataset.</p>
                <div id="geo-map"></div>
                <script>
                    var geoData = """ + geo_fig.to_json() + """;
                    Plotly.newPlot('geo-map', geoData.data, geoData.layout);
                </script>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Geographic Distribution")
                st.plotly_chart(geo_fig, use_container_width=True)
                st.write("---")

            if "Rating Analysis" in include_sections and 'rating' in data.columns:
                # Create the visualization
                rating_fig = analysis.create_distribution_plot(data, 'rating')

                # Add to HTML report
                report_html += """
                <h2 id="rating-analysis">Rating Analysis</h2>
                <p>This section analyzes the distribution of restaurant ratings.</p>
                <div id="rating-plot"></div>
                <script>
                    var ratingData = """ + rating_fig.to_json() + """;
                    Plotly.newPlot('rating-plot', ratingData.data, ratingData.layout);
                </script>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Rating Analysis")
                st.plotly_chart(rating_fig, use_container_width=True)
                st.write("---")

            if "Cuisine Analysis" in include_sections and 'cuisine' in data.columns:
                # Create the visualization
                cuisine_fig = analysis.create_categorical_distribution(
                    data, 'cuisine', 10)

                # Add to HTML report
                report_html += """
                <h2 id="cuisine-analysis">Cuisine Analysis</h2>
                <p>This section shows the distribution of restaurant cuisines.</p>
                <div id="cuisine-plot"></div>
                <script>
                    var cuisineData = """ + cuisine_fig.to_json() + """;
                    Plotly.newPlot('cuisine-plot', cuisineData.data, cuisineData.layout);
                </script>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Cuisine Analysis")
                st.plotly_chart(cuisine_fig, use_container_width=True)
                st.write("---")

            if "Price Analysis" in include_sections and 'price' in data.columns:
                # Create the visualization
                price_fig = analysis.create_count_by_price(data)

                # Add to HTML report
                report_html += """
                <h2 id="price-analysis">Price Analysis</h2>
                <p>This section analyzes restaurant price categories.</p>
                <div id="price-plot"></div>
                <script>
                    var priceData = """ + price_fig.to_json() + """;
                    Plotly.newPlot('price-plot', priceData.data, priceData.layout);
                </script>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Price Analysis")
                st.plotly_chart(price_fig, use_container_width=True)
                st.write("---")

            if "Spatial Patterns" in include_sections:
                # Create the visualization
                density_fig = analysis.create_density_map(data)

                # Add to HTML report
                report_html += """
                <h2 id="spatial-patterns">Spatial Patterns</h2>
                <p>This section shows restaurant density patterns.</p>
                <div id="density-plot"></div>
                <script>
                    var densityData = """ + density_fig.to_json() + """;
                    Plotly.newPlot('density-plot', densityData.data, densityData.layout);
                </script>
                <hr>
                """

                # Display on the Streamlit app
                st.write("### Spatial Patterns")
                st.plotly_chart(density_fig, use_container_width=True)
                st.write("---")

            # Add footer to HTML report
            report_html += """
                <div class="footer">
                    <p>Report generated using Restaurant Geographic Analysis Tool</p>
                </div>
            </body>
            </html>
            """

            # Create download link for HTML report
            html_bytes = report_html.encode()
            b64 = base64.b64encode(html_bytes).decode()
            href = f'<a href="data:text/html;base64,{b64}" download="{report_filename}.html">Download Report as HTML</a>'

            # Download report option
            st.success("Report generated! You can now download it.")
            st.markdown(href, unsafe_allow_html=True)
    else:
        st.info("Please upload and process data to export and share insights.")
