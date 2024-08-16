import pandas as pd

# Load the exported data
df = pd.read_csv('/home/user/cleaned_fressnapf.csv')

# Check data types
print(df.dtypes)

# Print the shape of the DataFrame
print(f"Number of rows: {df.shape[0]}")
print(f"Number of columns: {df.shape[1]}")

# Check for null values
print(df.isna().sum())

# Check for duplicates
print(df.duplicated().sum())

# Display summary statistics
print(df.describe())

# Display a sample of the DataFrame
print("Sample of the DataFrame:")
print(df.sample(10))