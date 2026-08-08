import pandas as pd
from itertools import combinations

# Step 1: Load the dataset
file_path = r"C:\Users\Sowmya\Downloads\Current Works\NoSQL\Domain_in_One.csv"  # Update with your file path

try:
    df = pd.read_csv(file_path, sep=',')  # Load the CSV data
    print("Dataframe loaded successfully")
except FileNotFoundError:
    print(f"Error: The file at {file_path} was not found. Please check the file path.")
    exit()

# Step 2: Clean up column names by stripping any extra spaces
df.columns = df.columns.str.strip()
print("Columns after cleaning: ", df.columns)

# Ensure required columns exist
if "Entry" not in df.columns or "InterPro" not in df.columns:
    print("Error: Required columns 'Entry' or 'InterPro' are missing from the data.")
    exit()

# Step 3: Clean and parse the 'InterPro' column (convert to sets of domains)
# Add check for NaN values before processing
df['InterPro'] = df['InterPro'].apply(lambda x: set(x.replace("'", "").split(', ')) if isinstance(x, str) else set())

# Step 4: Initialize a list to store the relationships (protein pairs and their Jaccard similarity)
relationships = []

# Step 5: Calculate Jaccard similarity for each pair of proteins
for (protein1, domains1), (protein2, domains2) in combinations(df[['Entry', 'InterPro']].values, 2):
    intersection = domains1 & domains2  # Common domains
    union = domains1 | domains2  # All domains

    if union:  # Avoid division by zero if union is empty
        jaccard_similarity = len(intersection) / len(union)

        # Add relationship if similarity > 0
        if jaccard_similarity > 0.5:
            common_domains = ", ".join([str(domain) for domain in intersection])  # Join common domains as string
            relationships.append({
                "Protein1": protein1,
                "Protein2": protein2,
                "Similarity": jaccard_similarity,
                "Common Domains": common_domains
            })

# Step 6: Convert the relationships list to a DataFrame
df_relationships = pd.DataFrame(relationships)

# Step 7: Define output path and save the result as CSV
output_path = r"C:\Users\Sowmya\Downloads\Current Works\NoSQL\Jaccard_Data.csv"  # Set the output path
df_relationships.to_csv(output_path, index=False)

print(f"Relationships file saved at: {output_path}")
