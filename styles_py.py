import streamlit as st

def load_css():
    """Load CSS styles for the app"""
    st.markdown("""
    <style>
        .main-header {
            font-size: 2.5rem;
            color: #1E88E5;
            font-weight: 700;
            margin-bottom: 1rem;
        }
        .sub-header {
            font-size: 1.8rem;
            color: #0D47A1;
            font-weight: 600;
            margin: 1rem 0;
        }
        .card {
            border-radius: 5px;
            background-color: white;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            padding: 20px;
            margin-bottom: 20px;
        }
        .metric-card {
            text-align: center;
            padding: 15px;
            border-radius: 5px;
            background-color: #f8f9fa;
            box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05);
        }
        .metric-value {
            font-size: 1.8rem;
            font-weight: 700;
            color: #1E88E5;
        }
        .metric-label {
            font-size: 0.9rem;
            color: #616161;
            margin-top: 5px;
        }
        .status-active {
            color: white;
            background-color: #4CAF50;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        .status-completed {
            color: white;
            background-color: #2196F3;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        .status-overdue {
            color: white;
            background-color: #F44336;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        .status-pending {
            color: white;
            background-color: #FF9800;
            padding: 3px 10px;
            border-radius: 12px;
            font-size: 0.8rem;
        }
        .highlight {
            background-color: #f0f7ff;
            padding: 15px;
            border-radius: 5px;
            border-left: 5px solid #1E88E5;
        }
        .footer {
            text-align: center;
            margin-top: 40px;
            padding: 20px;
            border-top: 1px solid #e0e0e0;
            color: #9e9e9e;
        }
        /* Hide Streamlit branding */
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        /* Custom styling for tabs */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            height: 50px;
            white-space: pre-wrap;
            background-color: #f8f9fa;
            border-radius: 4px 4px 0px 0px;
            padding: 10px 16px;
            font-size: 16px;
        }
        .stTabs [aria-selected="true"] {
            background-color: #1E88E5;
            color: white;
        }
        /* Weekend highlight in resource utilization */
        .weekend {
            background-color: #f8f9fa;
        }
        /* Task detail panel */
        .task-detail {
            padding: 15px;
            border: 1px solid #e0e0e0;
            border-radius: 5px;
        }
        /* Button styling */
        .stButton>button {
            background-color: #1E88E5;
            color: white;
            border-radius: 4px;
            padding: 0.5rem 1rem;
            font-weight: 500;
        }
        .stButton>button:hover {
            background-color: #0D47A1;
        }
    </style>
    """, unsafe_allow_html=True)