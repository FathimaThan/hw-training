import streamlit as st
import json
import pandas as pd

# Predefined field order and correct field names
correct_fields = [
    "first_name", "middle_name", "last_name", "office_name", "title",
    "description", "languages", "image_url", "address", "city", "state",
    "country", "zipcode", "office_phone_numbers", "agent_phone_numbers",
    "email", "website", "social", "profile_url"
]

def check_field_order(json_data):
    keys = list(json_data.keys())
    return keys == correct_fields, keys

def check_field_spelling(json_data):
    # Identify incorrect fields by comparing with the predefined correct fields
    incorrect_fields = [field for field in json_data.keys() if field not in correct_fields]
    return incorrect_fields

def flatten_list_of_lists(lst):
    """Flatten a list of lists into a single list."""
    flattened = []
    for item in lst:
        if isinstance(item, list):
            flattened.extend(flatten_list_of_lists(item))  # Recursively flatten
        else:
            flattened.append(item)
    return flattened

def display_column_values(df, column_name):
    st.write(f"Values in column '{column_name}':")
    
    # Extract column values
    column_values = df[column_name].dropna()
    
    # Flatten list of lists if necessary
    if column_values.apply(lambda x: isinstance(x, list)).any():
        flattened_values = column_values.apply(lambda x: flatten_list_of_lists(x) if isinstance(x, list) else [x])
        flattened_values = [item for sublist in flattened_values for item in sublist]
    else:
        flattened_values = column_values.tolist()
    
    # Convert to DataFrame for display
    flattened_values_df = pd.DataFrame(flattened_values, columns=[column_name])
    
    # Make DataFrame scrollable
    st.write("All values:")
    st.dataframe(flattened_values_df, height=400)  # Increase height for better visibility
    
    return flattened_values

def preprocess_json_file(file):
    # Read the file content
    content = file.read().decode('utf-8')
    
    # Split content by lines and process
    lines = content.splitlines()

    # Add commas and wrap with square brackets
    lines = [line.strip() + ',' for line in lines if line.strip()]
    if lines:
        lines[0] = '[' + lines[0]  # Add [ at the start of the first line
        lines[-1] = lines[-1][:-1]  # Remove the last comma
        lines[-1] += ']'  # Add ] at the end of the last line

    # Join lines to form a valid JSON string
    modified_content = "\n".join(lines)
    return modified_content

def main():
    st.title("JSON Data QA App")

    # Upload JSON file
    uploaded_file = st.file_uploader("Upload a JSON file", type="json")

    if uploaded_file is not None:
        # Preprocess JSON file
        try:
            modified_content = preprocess_json_file(uploaded_file)
            json_data = json.loads(modified_content)  # Parse modified JSON content

            # Convert JSON to DataFrame
            df = pd.DataFrame(json_data)

            # Check field order
            order_correct, fields_in_order = check_field_order(json_data[0])
            if order_correct:
                st.success("The field order is correct.")
            else:
                st.error(f"Incorrect field order. Current order: {fields_in_order}")

            # Check field spelling
            incorrect_fields = check_field_spelling(json_data[0])
            if not incorrect_fields:
                st.success("Field spelling is correct.")
            else:
                st.error(f"Incorrect field names: {', '.join(incorrect_fields)}")

            # Column selection
            column_name = st.selectbox("Select a column to inspect", df.columns)

            if column_name:
                # Display column values
                column_values = display_column_values(df, column_name)

                # Sorting selection
                sort_order = st.selectbox("Select sorting order", ["None", "Ascending", "Descending"])
                
                # Sort unique values based on user selection
                unique_values = pd.Series(column_values).unique()
                if sort_order == "Ascending":
                    sorted_unique_values = sorted(unique_values)
                elif sort_order == "Descending":
                    sorted_unique_values = sorted(unique_values, reverse=True)
                else:
                    sorted_unique_values = unique_values
                
                # Convert sorted unique values to DataFrame for table display
                sorted_values_df = pd.DataFrame(sorted_unique_values, columns=[column_name])
                
                st.write(f"Unique values in column '{column_name}' (sorted):")
                st.dataframe(sorted_values_df, height=400)  # Increase height for better visibility
                
                # Search feature
                search_value = st.text_input("Search for a value in this column", placeholder="Type value here...", key="search_input")
                
                if search_value:
                    # Filter DataFrame based on search value
                    filtered_df = df[df[column_name].astype(str).str.contains(search_value, case=False, na=False)]
                    
                    if not filtered_df.empty:
                        st.write(f"Rows containing '{search_value}':")
                        st.dataframe(filtered_df)
                    else:
                        st.write(f"No rows found containing '{search_value}'.")

            # Display all keys
            st.write("All keys (fields) in the JSON file:")
            st.write(list(json_data[0].keys()))

        except json.JSONDecodeError as e:
            st.error(f"Error decoding JSON: {e}")
        except Exception as e:
            st.error(f"Error processing JSON file: {e}")

if __name__ == "__main__":
    main()
