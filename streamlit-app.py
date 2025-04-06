import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import plotly.express as px

# Set page config
st.set_page_config(
    page_title="Data Science Explorer",
    page_icon="📊",
    layout="wide"
)

# App title and description
st.title("📊 Data Science Explorer")
st.markdown("""
This application demonstrates various data science capabilities using Streamlit.
Upload your dataset and explore visualizations, statistics, and predictive models.
""")

# Sidebar for navigation
st.sidebar.title("Navigation")
pages = ["Data Upload & Exploration", "Visualization", "Predictive Modeling"]
selection = st.sidebar.radio("Go to", pages)

# Initialize session state variables if they don't exist
if 'data' not in st.session_state:
    st.session_state.data = None
if 'filename' not in st.session_state:
    st.session_state.filename = None

# Function to load sample data
def load_sample_data():
    # Load sample data (using seaborn's built-in dataset)
    df = sns.load_dataset('tips')
    return df

# Data upload page
if selection == "Data Upload & Exploration":
    st.header("Data Upload & Exploration")
    
    col1, col2 = st.columns(2)
    
    with col1:
        uploaded_file = st.file_uploader("Upload your CSV file", type=['csv'])
        
        if uploaded_file is not None:
            try:
                df = pd.read_csv(uploaded_file)
                st.session_state.data = df
                st.session_state.filename = uploaded_file.name
                st.success(f"Successfully loaded: {uploaded_file.name}")
            except Exception as e:
                st.error(f"Error: {e}")
    
    with col2:
        if st.button("Load Sample Data"):
            df = load_sample_data()
            st.session_state.data = df
            st.session_state.filename = "sample_tips_data.csv"
            st.success("Sample data loaded!")
    
    # Display data and basic info if available
    if st.session_state.data is not None:
        df = st.session_state.data
        
        # Display data overview
        st.subheader("Data Overview")
        
        # Tabs for different views
        tab1, tab2, tab3 = st.tabs(["Preview", "Statistics", "Structure"])
        
        with tab1:
            st.dataframe(df.head(10))
            st.text(f"Dataset shape: {df.shape[0]} rows, {df.shape[1]} columns")
        
        with tab2:
            st.subheader("Descriptive Statistics")
            st.dataframe(df.describe())
            
            # Missing values info
            st.subheader("Missing Values")
            missing_values = df.isnull().sum()
            missing_df = pd.DataFrame({
                'Column': missing_values.index,
                'Missing Values': missing_values.values,
                'Percentage': (missing_values.values / len(df) * 100).round(2)
            })
            st.dataframe(missing_df)
        
        with tab3:
            st.subheader("Data Types")
            dtypes_df = pd.DataFrame({
                'Column': df.dtypes.index,
                'Data Type': df.dtypes.values
            })
            st.dataframe(dtypes_df)
            
            # Show unique values for categorical columns
            st.subheader("Categorical Columns")
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            
            if len(cat_cols) > 0:
                selected_cat_col = st.selectbox("Select a categorical column:", cat_cols)
                st.write(f"Unique values in {selected_cat_col}:")
                
                # Display value counts
                value_counts = df[selected_cat_col].value_counts().reset_index()
                value_counts.columns = [selected_cat_col, 'Count']
                st.dataframe(value_counts)
                
                # Simple bar chart of value counts
                fig, ax = plt.subplots(figsize=(10, 5))
                sns.barplot(x=selected_cat_col, y='Count', data=value_counts, ax=ax)
                plt.xticks(rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            else:
                st.write("No categorical columns found.")
    else:
        st.info("Please upload a CSV file or load the sample data to begin.")

# Visualization page
elif selection == "Visualization":
    st.header("Data Visualization")
    
    if st.session_state.data is not None:
        df = st.session_state.data
        
        # Select visualization type
        viz_type = st.selectbox(
            "Select Visualization Type",
            ["Distribution Plot", "Scatter Plot", "Box Plot", "Correlation Heatmap", "Pair Plot"]
        )
        
        # Distribution Plot
        if viz_type == "Distribution Plot":
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(num_cols) > 0:
                selected_col = st.selectbox("Select a numerical column:", num_cols)
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # Histogram
                    fig = px.histogram(df, x=selected_col, title=f"Histogram of {selected_col}")
                    st.plotly_chart(fig, use_container_width=True)
                
                with col2:
                    # Box plot
                    fig = px.box(df, y=selected_col, title=f"Box Plot of {selected_col}")
                    st.plotly_chart(fig, use_container_width=True)
                
                # Additional statistics
                st.subheader(f"Statistics for {selected_col}")
                stats = df[selected_col].describe()
                st.write(stats)
            else:
                st.write("No numerical columns found for distribution plot.")
        
        # Scatter Plot
        elif viz_type == "Scatter Plot":
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(num_cols) >= 2:
                col1, col2 = st.columns(2)
                
                with col1:
                    x_col = st.selectbox("Select X-axis:", num_cols)
                
                with col2:
                    y_col = st.selectbox("Select Y-axis:", [col for col in num_cols if col != x_col] if len(num_cols) > 1 else num_cols)
                
                # Optional color by categorical
                cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                color_col = None
                
                if len(cat_cols) > 0:
                    cat_cols = ['None'] + cat_cols
                    color_col = st.selectbox("Color by (optional):", cat_cols)
                    if color_col == 'None':
                        color_col = None
                
                # Create scatter plot
                fig = px.scatter(
                    df,
                    x=x_col,
                    y=y_col,
                    color=color_col,
                    title=f"Scatter Plot: {x_col} vs {y_col}",
                    trendline="ols" if st.checkbox("Add Trendline") else None,
                    opacity=0.7
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # Show correlation
                correlation = df[[x_col, y_col]].corr().iloc[0, 1]
                st.write(f"Correlation between {x_col} and {y_col}: {correlation:.4f}")
            else:
                st.write("Need at least 2 numerical columns for scatter plot.")
        
        # Box Plot
        elif viz_type == "Box Plot":
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            cat_cols = df.select_dtypes(include=['object', 'category']).columns
            
            if len(num_cols) > 0 and len(cat_cols) > 0:
                col1, col2 = st.columns(2)
                
                with col1:
                    y_col = st.selectbox("Select Value (Y-axis):", num_cols)
                
                with col2:
                    x_col = st.selectbox("Select Category (X-axis):", cat_cols)
                
                # Create box plot
                fig = px.box(
                    df,
                    x=x_col,
                    y=y_col,
                    title=f"Box Plot of {y_col} by {x_col}",
                    color=x_col if st.checkbox("Add Color") else None,
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
                # ANOVA test option could be added here
            elif len(num_cols) > 0:
                st.write("No categorical columns available for grouping. Using a single box plot.")
                y_col = st.selectbox("Select Value:", num_cols)
                
                fig = px.box(df, y=y_col, title=f"Box Plot of {y_col}")
                st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("No numerical columns found for box plot.")
        
        # Correlation Heatmap
        elif viz_type == "Correlation Heatmap":
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(num_cols) > 1:
                # Select columns for correlation
                selected_cols = st.multiselect(
                    "Select columns for correlation matrix (default: all numeric):",
                    num_cols,
                    default=list(num_cols[:min(8, len(num_cols))])  # Default select first 8 or fewer
                )
                
                if not selected_cols:
                    st.warning("Please select at least two columns.")
                elif len(selected_cols) < 2:
                    st.warning("Please select at least two columns.")
                else:
                    # Calculate correlation matrix
                    corr_matrix = df[selected_cols].corr()
                    
                    # Plot heatmap
                    fig = px.imshow(
                        corr_matrix,
                        text_auto=True,
                        color_continuous_scale='RdBu_r',
                        title="Correlation Matrix Heatmap",
                        zmin=-1, zmax=1
                    )
                    
                    st.plotly_chart(fig, use_container_width=True)
                    
                    # Display the matrix as a table
                    st.subheader("Correlation Values")
                    st.dataframe(corr_matrix.style.background_gradient(cmap='coolwarm', axis=None, vmin=-1, vmax=1))
            else:
                st.write("Need at least 2 numerical columns for correlation heatmap.")
        
        # Pair Plot
        elif viz_type == "Pair Plot":
            num_cols = df.select_dtypes(include=['int64', 'float64']).columns
            
            if len(num_cols) > 1:
                # Select columns for pair plot
                selected_cols = st.multiselect(
                    "Select columns for pair plot (recommended: 2-5 columns):",
                    num_cols,
                    default=list(num_cols[:min(4, len(num_cols))])  # Default select first 4 or fewer
                )
                
                # Optional color by categorical
                cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
                color_col = None
                
                if len(cat_cols) > 0:
                    cat_cols = ['None'] + cat_cols
                    color_col = st.selectbox("Color by (optional):", cat_cols)
                    if color_col == 'None':
                        color_col = None
                
                if len(selected_cols) < 2:
                    st.warning("Please select at least two columns.")
                else:
                    if len(selected_cols) > 5:
                        st.warning("Many columns selected. Pair plot may be crowded and slow to render.")
                    
                    # Create pair plot
                    with st.spinner("Generating pair plot..."):
                        fig = px.scatter_matrix(
                            df,
                            dimensions=selected_cols,
                            color=color_col,
                            title="Pair Plot Matrix",
                            opacity=0.7
                        )
                        # Update axis labels to be more readable
                        fig.update_traces(diagonal_visible=False)
                        
                        st.plotly_chart(fig, use_container_width=True)
            else:
                st.write("Need at least 2 numerical columns for pair plot.")
                
    else:
        st.info("Please upload data in the 'Data Upload & Exploration' tab first.")

# Predictive Modeling page
elif selection == "Predictive Modeling":
    st.header("Predictive Modeling")
    
    if st.session_state.data is not None:
        df = st.session_state.data
        
        # Get numerical columns for features
        num_cols = df.select_dtypes(include=['int64', 'float64']).columns.tolist()
        
        if len(num_cols) > 1:
            # Select target variable
            target_var = st.selectbox("Select Target Variable:", num_cols)
            
            # Select feature variables (exclude target)
            available_features = [col for col in num_cols if col != target_var]
            
            selected_features = st.multiselect(
                "Select Features:",
                available_features,
                default=available_features[:min(3, len(available_features))]
            )
            
            if len(selected_features) > 0:
                # Show a preview of the data
                preview_data = df[selected_features + [target_var]].head()
                st.subheader("Data Preview")
                st.dataframe(preview_data)
                
                # Set up model parameters
                st.subheader("Model Parameters")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    test_size = st.slider("Test Size (%)", 10, 50, 20) / 100
                
                with col2:
                    n_estimators = st.slider("Number of Trees", 50, 500, 100, 50)
                
                # Model training button
                if st.button("Train Model"):
                    with st.spinner("Training model..."):
                        # Prepare the data
                        X = df[selected_features]
                        y = df[target_var]
                        
                        # Split the data
                        X_train, X_test, y_train, y_test = train_test_split(
                            X, y, test_size=test_size, random_state=42
                        )
                        
                        # Train a Random Forest model
                        model = RandomForestRegressor(
                            n_estimators=n_estimators,
                            random_state=42,
                            n_jobs=-1
                        )
                        
                        model.fit(X_train, y_train)
                        
                        # Make predictions
                        train_preds = model.predict(X_train)
                        test_preds = model.predict(X_test)
                        
                        # Evaluate the model
                        train_rmse = np.sqrt(mean_squared_error(y_train, train_preds))
                        test_rmse = np.sqrt(mean_squared_error(y_test, test_preds))
                        
                        train_r2 = r2_score(y_train, train_preds)
                        test_r2 = r2_score(y_test, test_preds)
                        
                        # Display metrics
                        st.subheader("Model Performance")
                        
                        metrics_cols = st.columns(2)
                        
                        with metrics_cols[0]:
                            st.metric("Training RMSE", f"{train_rmse:.4f}")
                            st.metric("Training R²", f"{train_r2:.4f}")
                        
                        with metrics_cols[1]:
                            st.metric("Testing RMSE", f"{test_rmse:.4f}")
                            st.metric("Testing R²", f"{test_r2:.4f}")
                        
                        # Feature importance
                        st.subheader("Feature Importance")
                        
                        importance_df = pd.DataFrame({
                            'Feature': selected_features,
                            'Importance': model.feature_importances_
                        }).sort_values('Importance', ascending=False)
                        
                        fig = px.bar(
                            importance_df,
                            x='Importance',
                            y='Feature',
                            orientation='h',
                            title="Feature Importance"
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Actual vs Predicted plot
                        st.subheader("Actual vs Predicted")
                        
                        # Create a dataframe for plotting
                        test_results = pd.DataFrame({
                            'Actual': y_test,
                            'Predicted': test_preds
                        })
                        
                        fig = px.scatter(
                            test_results,
                            x='Actual',
                            y='Predicted',
                            title="Actual vs Predicted Values",
                            opacity=0.7
                        )
                        
                        # Add 45-degree line (perfect predictions)
                        min_val = min(test_results['Actual'].min(), test_results['Predicted'].min())
                        max_val = max(test_results['Actual'].max(), test_results['Predicted'].max())
                        
                        fig.add_shape(
                            type="line",
                            line=dict(color="red", dash="dash"),
                            x0=min_val,
                            y0=min_val,
                            x1=max_val,
                            y1=max_val
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                        
                        # Residuals plot
                        st.subheader("Residuals Analysis")
                        
                        test_results['Residuals'] = test_results['Actual'] - test_results['Predicted']
                        
                        fig = px.scatter(
                            test_results,
                            x='Predicted',
                            y='Residuals',
                            title="Residuals vs Predicted Values",
                            opacity=0.7
                        )
                        
                        # Add horizontal line at y=0
                        fig.add_shape(
                            type="line",
                            line=dict(color="red", dash="dash"),
                            x0=min(test_results['Predicted']),
                            y0=0,
                            x1=max(test_results['Predicted']),
                            y1=0
                        )
                        
                        st.plotly_chart(fig, use_container_width=True)
                
            else:
                st.warning("Please select at least one feature.")
        else:
            st.warning("Need at least 2 numerical columns for predictive modeling.")
    else:
        st.info("Please upload data in the 'Data Upload & Exploration' tab first.")

# Add footer with contact info
st.sidebar.markdown("---")
st.sidebar.subheader("About")
st.sidebar.info(
    """
    This is a data science demo app created with Streamlit.
    
    For more information, contact:  
    [youremail@example.com](mailto:youremail@example.com)
    """
)
