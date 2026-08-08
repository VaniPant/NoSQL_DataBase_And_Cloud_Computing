from neo4j import GraphDatabase

# Initialize the Neo4j driver
driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "#Samsom1"))

# Function to process data in batches
def process_batches(batch_size, start_skip):
    with driver.session() as session:
        skip = start_skip  # Start from the row after the last processed row
        
        while True:
            query = f"""
            CALL {{
                LOAD CSV WITH HEADERS FROM "file:///Jaccard_Data.csv" AS row
                WITH row SKIP {skip} LIMIT {batch_size}
                MATCH (p1:Protein {{id: row.Protein1}})
                MATCH (p2:Protein {{id: row.Protein2}})
                MERGE (p1)-[r:SIMILAR_TO]->(p2)
                SET r.similarity = toFloat(row.Similarity)
                RETURN count(*) AS processed
            }}
            RETURN processed
            """
            
            result = session.run(query)

            # Check if rows were processed
            summary = result.single()
            processed_count = summary["processed"]

            if processed_count == 0:
                print(f"Finished processing at row {skip}.")
                break  # Stop when no more rows are processed
            
            print(f"Processed batch starting at row {skip}.")
            skip += batch_size  # Move to the next batch

# Execute the batch processor
if __name__ == "__main__":
    try:
        batch_size = 1000  # Set your desired batch size
        start_skip = 729000  # Start from the 729,000th row
        process_batches(batch_size, start_skip)
    finally:
        driver.close()  # Ensure the driver is closed properly
