import streamlit as st
import pandas as pd
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser
import io

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except:
        return False

def read_csv_with_handling(file, bad_lines_action='skip'):
    try:
        return pd.read_csv(file, on_bad_lines=bad_lines_action)
    except pd.errors.ParserError as e:
        st.error(f"Parsing error: {e}")
        return None

def handle_error(file):
    df = read_csv_with_handling(file)
    if df is None:
        proceed = st.radio("Errors occurred while reading the file. Do you want to proceed by ignoring problematic lines?", ('Yes', 'No'))
        if proceed == 'Yes':
            df = read_csv_with_handling(file, bad_lines_action='warn')
            st.warning("File loaded with problematic lines ignored")
        else:
            st.warning("Aborting file loading.")
            return None
    return df

def parse_date(date_str):
    try:
        return parser.parse(date_str).strftime('%Y-%m-%d')
    except:
        return None

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        return None

def clean_data(df):
    # Remove duplicate rows
    df = df.drop_duplicates()

    # Standardize 'Stock' column
    if 'Stock' in df.columns:
        df['Stock'] = df['Stock'].str.strip().str.lower()
    
    # Fill missing values with 'Unavailable' for specific columns
    columns_to_fill = ['Brand', 'Part number', 'Stock', 'Website', 'Ref_no_space', 'Description']
    for col in columns_to_fill:
        if col in df.columns:
            df[col] = df[col].fillna('Unavailable')

    # Check URL validity and uniqueness
    if 'URL' in df.columns:
        df['URL_valid'] = df['URL'].apply(is_valid_url)
        df['URL_unique'] = df['URL'].duplicated(keep=False)

    # Standardize date and time formats
    if 'Date' in df.columns:
        df['Date'] = df['Date'].apply(parse_date)
        df = df.dropna(subset=['Date'])
        df['Date'] = df['Date'].fillna(method='ffill')

    if 'Time' in df.columns:
        df['Time'] = df['Time'].apply(parse_time)
        df['Time'] = df['Time'].fillna(method='ffill')

    return df

def display_statistics(df):
    st.subheader("Data Cleaning Statistics")

    # Display total number of rows
    st.write(f"Total rows: {len(df)}")

    # URL statistics
    if 'URL_valid' in df.columns:
        st.write(f"Valid URLs: {df['URL_valid'].sum()}")
        st.write(f"Invalid URLs: {len(df) - df['URL_valid'].sum()}")
        st.write(f"Duplicate URLs: {df['URL_unique'].sum()}")

    # Summary statistics for numeric columns
    numeric_columns = df.select_dtypes(include=['number']).columns
    if not numeric_columns.empty:
        st.subheader("Numeric Columns Summary")
        st.write(df[numeric_columns].describe())

    # Summary statistics for categorical columns
    categorical_columns = df.select_dtypes(include=['object']).columns
    if categorical_columns.empty:
        st.write("No categorical columns found.")
    else:
        st.subheader("Categorical Columns Summary")
        for col in categorical_columns:
            st.write(f"**{col}**")
            st.write(df[col].value_counts(dropna=False))

def convert_df_to_csv(df):
    """Converts DataFrame to CSV and returns as a byte stream."""
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

st.title('CSV File Uploader and Data Cleaner')

# File uploader widget
uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    # Read and handle the CSV file
    df = handle_error(uploaded_file)
    
    if df is not None:
        st.write("File loaded successfully!")
        
        # Perform data cleaning
        df = clean_data(df)
        
        st.write("Data after cleaning:")
        st.dataframe(df.head())

        # Display summary statistics
        display_statistics(df)

        # Convert cleaned DataFrame to CSV
        csv_data = convert_df_to_csv(df)
        
        # Download button
        st.download_button(
            label="Download Cleaned Dataset as CSV",
            data=csv_data,
            file_name='cleaned_dataset.csv',
            mime='text/csv'
        )
    else:
        st.write("No data loaded. Please check the file and try again.")
