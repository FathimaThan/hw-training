import streamlit as st
import pandas as pd
import warnings
from urllib.parse import urlparse
from datetime import datetime
from dateutil import parser
import io
import re
from collections import Counter

def is_valid_url(url):
    try:
        result = urlparse(url)
        return all([result.scheme, result.netloc])
    except Exception:
        return False

def read_csv_with_handling(file, bad_lines_action='warn'):
    try:
        if bad_lines_action == 'warn':
            with warnings.catch_warnings(record=True) as w:
                warnings.simplefilter("always")
                df = pd.read_csv(file, on_bad_lines=bad_lines_action)
                for warning in w:
                    st.warning(f"Warning: {warning.message}")
        else:
            df = pd.read_csv(file, on_bad_lines=bad_lines_action)
    except pd.errors.ParserError as e:
        st.error(f"Parsing error: {e}")
        return None
    return df

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

def identify_date_formats(df, date_column):
    date_patterns = {
        "YYYY-MM-DD": r"^\d{4}-\d{2}-\d{2}$",
        "MM/DD/YYYY": r"^\d{2}/\d{2}/\d{4}$",
        "DD-MM-YYYY": r"^\d{2}-\d{2}-\d{4}$",
        "YYYY/MM/DD": r"^\d{4}/\d{2}/\d{2}$",
    }
    
    format_counter = Counter()
    others_dates = []

    for date in df[date_column].astype(str):
        matched = False
        for format_name, pattern in date_patterns.items():
            if re.match(pattern, date):
                format_counter[format_name] += 1
                matched = True
                break
        if not matched:
            format_counter["Others"] += 1
            others_dates.append(date)

    return format_counter, others_dates

def check_columns(df: pd.DataFrame):
    required_columns = [
        'url', 'catalogue price', 'net price', 'brand', 'part number', 
        'date', 'time', 'stock', 'website', 'ref_no_space', 'description'
    ]
    lower_columns = [col.lower() for col in df.columns]
    missing_columns = [col for col in required_columns if col not in lower_columns]

    if missing_columns:
        st.error(f"Missing columns: {', '.join(missing_columns)}")
    else:
        st.success("All required columns are present.")

def display_data_issues(df: pd.DataFrame):
    missing_values = df.isnull().sum()
    duplicates = df.duplicated().sum()
    invalid_types = df.select_dtypes(exclude=['int64', 'float64']).applymap(lambda x: isinstance(x, (int, float))).sum()
    
    st.header("Data Quality Report")
    
    if missing_values.any():
        st.subheader("Missing Values")
        st.write(missing_values[missing_values > 0])
    else:
        st.success("No missing values found.")
    
    if duplicates > 0:
        st.error(f"Number of duplicate rows: {duplicates}")
    else:
        st.success("No duplicate rows found.")
    
    if invalid_types.any():
        st.subheader("Invalid Data Types")
        st.write(invalid_types[invalid_types > 0])
    else:
        st.success("No invalid data types found.")

    date_formats, others_dates = identify_date_formats(df, 'Date')

    st.subheader("Date Column")
    st.write("Date Formats:")
    st.write(date_formats)
    if others_dates:
        st.warning("Dates that don't match any common format:")
        st.write(others_dates)
    else:
        st.success("All dates matched common formats.")

    st.subheader("Summary Statistics")
    st.write("Numerical Columns Summary:")
    st.write(df.describe())
    
    st.write("Categorical Columns Summary:")
    st.write(df.describe(include=['object']))

    st.subheader("Data Information (info)")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

def parse_date(date_str):
    try:
        return pd.to_datetime(date_str, errors='coerce').strftime('%Y-%m-%d')
    except Exception:
        return None

def parse_time(time_str):
    try:
        return datetime.strptime(time_str, '%H:%M:%S').time()
    except ValueError:
        return None

def clean_data(df):
    df = df.drop_duplicates()

    if 'Stock' in df.columns:
        df['Stock'] = df['Stock'].str.strip().str.lower()
    
    columns_to_fill = ['Brand', 'Part number', 'Stock', 'Website', 'Ref_no_space', 'Description']
    for col in columns_to_fill:
        if col in df.columns:
            df[col] = df[col].fillna('Unavailable')

    if 'URL' in df.columns:
        df['URL_valid'] = df['URL'].apply(is_valid_url)
        invalid_urls = df[~df['URL_valid']]
        
        if not invalid_urls.empty:
            st.warning("The following rows have invalid URLs:")
            st.write(invalid_urls[['URL']])
            df = df[df['URL_valid']]

        duplicate_urls_count = df['URL'].duplicated(keep=False).sum()
        if duplicate_urls_count > 0:
            st.warning(f"Number of duplicate URLs: {duplicate_urls_count}")
            st.write(df[df['URL'].duplicated(keep=False)])
            df = df.drop_duplicates(subset='URL', keep='first')

        df = df.drop(columns=['URL_valid'])

    if 'Date' in df.columns:
        df['Date'] = df['Date'].apply(parse_date)
        df = df.dropna(subset=['Date'])
        df['Date'] = df['Date'].ffill()

    if 'Time' in df.columns:
        df['Time'] = df['Time'].apply(parse_time)
        df['Time'] = df['Time'].ffill()

    null_counts = df.isnull().sum(axis=1)
    rows_with_many_nulls = df[null_counts > 6]

    if not rows_with_many_nulls.empty:
        st.warning(f"The following rows have more than 6 null values:")
        st.write(rows_with_many_nulls)
        df = df[null_counts <= 6]

    return df

def display_statistics(df):
    st.subheader("Data Cleaning Statistics")

    st.write(f"Total rows: {len(df)}")
    
    missing_values_after_cleaning = df.isnull().sum()
    st.subheader("Missing Values After Cleaning")
    st.write(missing_values_after_cleaning[missing_values_after_cleaning > 0])

    duplicate_rows_count = df.duplicated().sum()
    st.write(f"Number of duplicate rows: {duplicate_rows_count}")

    st.subheader("Summary Statistics")
    st.write("Numerical Columns Summary:")
    st.write(df.describe())

    st.write("Categorical Columns Summary:")
    categorical_columns = df.select_dtypes(include=['object']).columns
    if categorical_columns.empty:
        st.write("No categorical columns found.")
    else:
        st.write(df.describe(include=['object']))

    st.subheader("Data Information (info)")
    buffer = io.StringIO()
    df.info(buf=buffer)
    st.text(buffer.getvalue())

def convert_df_to_csv(df):
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    return csv_buffer.getvalue()

st.title('CSV File Uploader and Data Cleaner')

uploaded_file = st.file_uploader("Choose a CSV file", type="csv")

if uploaded_file is not None:
    df = handle_error(uploaded_file)
    
    if df is not None:
        st.write("File loaded successfully!")

        check_columns(df)

        display_data_issues(df)

        df = clean_data(df)
        
        st.header("Data after cleaning:")
        st.dataframe(df.head())

        display_statistics(df)

        csv_data = convert_df_to_csv(df)
        
        st.download_button(
            label="Download Cleaned Dataset as CSV",
            data=csv_data,
            file_name='cleaned_dataset.csv',
            mime='text/csv'
        )
    else:
        st.write("No data loaded. Please check the file and try again.")