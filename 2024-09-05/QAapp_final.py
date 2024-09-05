import streamlit as st
import json
import pandas as pd
import re

st.set_page_config(layout="wide")

# Define correct fields and mandatory fields globally
correct_fields = set([
    "first_name", "middle_name", "last_name", "office_name", "title",
    "description", "languages", "image_url", "address", "city", "state",
    "country", "zipcode", "office_phone_numbers", "agent_phone_numbers",
    "email", "website", "social", "profile_url"
])

mandatory_fields = set([
    "first_name", "last_name", "email", "address"
])

def check_field_order(json_data, user_field_order):
    keys = list(json_data.keys())
    return keys == user_field_order, keys

def check_field_spelling(json_data):
    incorrect_fields = [field for field in json_data.keys() if field not in correct_fields]
    return incorrect_fields

def check_field_format(json_data):
    incorrect_format_fields = [field for field in json_data.keys() if not re.match(r"^[a-z_]+$", field)]
    return incorrect_format_fields

def check_file_name_format(file_name):
    pattern = r'^.+_\d{4}_\d{2}_\d{2}\.json$'
    return re.match(pattern, file_name)

def flatten_list_of_lists(lst):
    """Flatten a list of lists into a single list."""
    flattened = []
    for item in lst:
        if isinstance(item, list):
            flattened.extend(flatten_list_of_lists(item))  # Recursively flatten
        else:
            flattened.append(item)
    return flattened

def find_empty_columns(df):
    empty_columns = []
    for column in df.columns:
        all_empty = df[column].apply(lambda x: x in ('', None, {}, [], set()) or (isinstance(x, (list, dict, set)) and len(x) == 0)).all()
        if all_empty:
            empty_columns.append(column)
    return empty_columns

def display_column_values(df, column_name, unique_only=False):
    st.write(f"Values in column '{column_name}':")

    column_values = df[column_name]
    
    # Convert dicts to a standard string representation
    def process_value(value):
        if isinstance(value, dict):
            return str(value)  # Convert dict to string
        elif isinstance(value, (list, set)):
            return str(value)  # Convert list/set to string
        return value
    
    processed_values = column_values.apply(process_value).tolist()
    
    # Remove empty values for uniqueness check if needed
    if unique_only:
        processed_values = [v for v in processed_values if v not in ('', None, '{}', '[]', '{}', 'set()')]
        processed_values = list(set(processed_values))
    
    # Convert to DataFrame for display
    flattened_values_df = pd.DataFrame(processed_values, columns=[column_name])
    
    # Display the DataFrame with adjustable width and scrollable option
    st.dataframe(flattened_values_df, use_container_width=True)

    total_rows = len(flattened_values_df)
    st.write(f"Total rows: {total_rows}")

    return flattened_values_df

def validate_emails(df, email_column):
    email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
    invalid_emails = df[~df[email_column].str.match(email_pattern, na=False)]
    return invalid_emails

def validate_urls(df, url_column):
    url_pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$')
    invalid_urls = df[~df[url_column].str.match(url_pattern, na=False)]
    return invalid_urls

def validate_social(df, social_column):
    invalid_social = []
    for idx, social in df[social_column].items():  # Use items() for Series
        if isinstance(social, dict):
            for key, url in social.items():
                if url and not re.match(r'^https?://[^\s/$.?#].[^\s]*$', url):
                    invalid_social.append((idx, key, url))
    return invalid_social

def check_mandatory_fields(df, mandatory_fields):
    missing_fields = [field for field in mandatory_fields if field not in df.columns or df[field].isnull().any()]
    return missing_fields

def preprocess_json_file(file):
    content = file.read().decode('utf-8')
    lines = content.splitlines()
    lines = [line.strip() + ',' for line in lines if line.strip()]
    if lines:
        lines[0] = '[' + lines[0]  # Add [ at the start of the first line
        lines[-1] = lines[-1][:-1]  # Remove the last comma
        lines[-1] += ']'  # Add ] at the end of the last line
    modified_content = "\n".join(lines)
    return modified_content

def expand_social_column(df):
    if 'social' in df.columns:
        # Check if 'social' column contains non-empty dictionaries
        non_empty_social = df['social'].apply(lambda x: isinstance(x, dict) and bool(x))
        if non_empty_social.any():  # Only expand if there's at least one non-empty dictionary
            social_df = pd.json_normalize(df['social']).add_prefix('social_')
            df = pd.concat([df.drop(columns=['social']), social_df], axis=1)
    return df

def main():
    st.title("JSON Data QA App")
    uploaded_file = st.file_uploader("Upload a JSON file", type="json")

    if uploaded_file is not None:
        try:
            # Preprocess the JSON file
            modified_content = preprocess_json_file(uploaded_file)
            json_data = json.loads(modified_content)
            df = pd.DataFrame(json_data)

            # Expand the social column into separate columns
            df = expand_social_column(df)

            st.write("**Specify the Correct Field Order**")

            # Reorder fields by selecting from a dropdown list
            field_order = st.multiselect(
                "Select and reorder the fields (drag to reorder):",
                options=list(correct_fields),
                default=list(correct_fields)
            )

            # Check if the selected order is correct
            order_correct, fields_in_order = check_field_order(json_data[0], field_order)
            
            if order_correct:
                st.success("The field order is correct.")
            else:
                st.error(f"Incorrect field order. Current order: {fields_in_order}")

            incorrect_fields = check_field_spelling(json_data[0])
            if not incorrect_fields:
                st.success("Field spelling is correct.")
            else:
                st.error(f"Incorrect field names: {', '.join(incorrect_fields)}")

            incorrect_format_fields = check_field_format(json_data[0])
            if not incorrect_format_fields:
                st.success("Field names format is correct (lowercase with underscores).")
            else:
                st.error(f"Incorrect format for field names: {', '.join(incorrect_format_fields)}")
            
            # Display the file name
            st.write(f"Uploaded file name: **{uploaded_file.name}**")
            # Check if the file name is correct
            if check_file_name_format(uploaded_file.name):
                st.success("File name is in the correct format.")
            else:
                st.error("File name is not in the correct format. Expected: filename_YYYY_MM_DD.json")

            # Display the count of data (number of rows)
            st.write(f"Total number of rows in the dataset: {len(df)}")

            # Allow the user to select mandatory fields
            st.write("**Select Mandatory Fields to Check**")
            mandatory_fields = st.multiselect(
                "Select the mandatory fields:",
                options=df.columns.tolist(),
                default=[]
            )

            # Check for mandatory fields
            if mandatory_fields:
                missing_fields = check_mandatory_fields(df, mandatory_fields)
    
                if missing_fields:
                    st.error(f"The following mandatory fields are missing: {', '.join(missing_fields)}")
                else:
                    st.success("All mandatory fields are present.")

            # Check for empty columns
            empty_columns = find_empty_columns(df)
            if empty_columns:
                st.write("**Columns with all empty values (null, '', None):**")
                st.write(", ".join(empty_columns))
            else:
                st.success("No columns with all empty values found.")

            # Display the dataset
            st.write("Dataset:")
            st.dataframe(df, height=400)

            # Column selection for detailed inspection
            column_name = st.selectbox("Select a column to inspect", df.columns)
            if column_name:
                # Option to display only unique values
                unique_only = st.checkbox("Display unique values only")

                # Display column values with the selected options
                display_column_values(df, column_name, unique_only)

                # Validate specific columns
                if column_name == 'email':
                    invalid_emails = validate_emails(df, column_name)
                    if not invalid_emails.empty:
                        st.write("Invalid emails:")
                        st.dataframe(invalid_emails)
                    else:
                        st.success("All emails are valid.")
                
                elif column_name == 'profile_url':
                    invalid_urls = validate_urls(df, column_name)
                    if not invalid_urls.empty:
                        st.write("Invalid profile URLs:")
                        st.dataframe(invalid_urls)
                    else:
                        st.success("All profile URLs are valid.")

                elif column_name == 'image_url':
                    invalid_urls = validate_urls(df, column_name)
                    if not invalid_urls.empty:
                        st.write("Invalid image URLs:")
                        st.dataframe(invalid_urls)
                    else:
                        st.success("All image URLs are valid.")

                elif column_name == 'website':
                    invalid_websites = validate_urls(df, column_name)  # Assuming validate_website is similar to validate_urls
                    if not invalid_websites.empty:
                        st.write("Invalid websites:")
                        st.dataframe(invalid_websites)
                    else:
                        st.success("All websites are valid.")
                
                elif column_name.startswith('social_'):
                    invalid_social = validate_social(df, column_name)
                    if invalid_social:
                        st.write("Invalid social URLs:")
                        for idx, key, url in invalid_social:
                            st.write(f"Index: {idx}, Social Media: {key}, URL: {url}")
                    else:
                        st.success("All social URLs are valid.")

        except Exception as e:
            st.error(f"Error processing JSON file: {e}")

if __name__ == "__main__":
    main()
