import pandas as pd

# 1. Load the input file (corrected path with raw string or double backslashes)
input_file_path = r"C:\Users\Sowmya\Downloads\Current Works\NoSQL\Raw_Data.tsv"

df_input = pd.read_csv(input_file_path, sep='\t')  # Assuming the input is a TSV file

# 2. Process the InterPro domains
df_input['InterPro'] = df_input['InterPro'].fillna('')  # Fill NaN with empty strings

# 3. Split the InterPro domains and format as individual strings with commas
df_input['InterPro'] = df_input['InterPro'].apply(
    lambda x: ', '.join([f"'{domain.strip()}'" for domain in x.split(';') if domain.strip()])
)

# 4. Define the output file path and save the result as a CSV
output_file_path = r"C:\Users\Sowmya\Downloads\Current Works\NoSQL\Domain_in_One.csv"
df_input.to_csv(output_file_path, index=False)  # Use default ',' separator for CSV

# 5. Print the output path
print(f"File saved at: {output_file_path}")



