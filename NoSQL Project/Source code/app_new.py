from flask import Flask, render_template, request, jsonify
from py2neo import Graph
from flask_pymongo import PyMongo

app = Flask(__name__)

# Connect to MongoDB
app.config["MONGO_URI"] = "mongodb://localhost:27017/Protein_Database"
mongo = PyMongo(app)

# Connect to Neo4j
graph = Graph("bolt://localhost:7687", auth=("neo4j", "#Samsom1"))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/search', methods=['POST'])
def search_protein():
    protein_entry = request.form.get('protein_entry')

    # Search MongoDB for protein details
    protein = mongo.db.Domain_in_One.find_one({"Entry": protein_entry})

    if protein:
        protein_details = {
            "Entry": protein['Entry'],
            "Entry Name": protein['Entry Name'],
            "Protein Names": protein['Protein names'],
            "Gene Names": protein['Gene Names'],
            "Organism": protein['Organism'],
            "EC number": protein.get('EC number', 'N/A'),
            "InterPro": protein['InterPro'],
            "Sequence": protein.get('Sequence', 'N/A')
        }
    else:
        protein_details = "Protein not found in MongoDB."

    # Query Neo4j for the graph data
    query = """
        MATCH (p:Protein {id:$protein_entry})-[r1:SIMILAR_TO]->(neighbor:Protein)
        RETURN p, r1, neighbor
        LIMIT 20
    """
    results = graph.run(query, protein_entry=protein_entry).data()

    nodes_dict = {}
    edges = []

    for record in results:
        # Extract proteins and relationships
        p = record['p']
        neighbor = record['neighbor']
        r1 = record['r1']

        # Add nodes
        for protein in [p, neighbor]:
            if protein['id'] not in nodes_dict:
                nodes_dict[protein['id']] = {
                    "data": {
                        "id": protein['id'],
                        "label": protein['id'],
                        "entry_name": protein.get('entry_name', 'N/A'),
                        "gene_names": protein.get('gene_name', 'N/A'),
                        "organism": protein.get('organism', 'N/A'),
                        "ec_number": protein.get('ec_number', 'N/A'),
                        "sequence": protein.get('sequence', 'N/A'),
                    }
                }

        # Add edges
        edges.append({
            "data": {
                "source": p['id'],
                "target": neighbor['id'],
                "id": r1['elementId'],
                "weight": r1.get('similarity', 1.0),
                "type": "SIMILAR_TO"
            }
        })

    # Convert nodes_dict to a list
    nodes = list(nodes_dict.values())

    return render_template('index.html', protein_details=protein_details, nodes=nodes, edges=edges)

#Statistics Route
@app.route('/statistics')
def show_statistics():
    # Query MongoDB for labeled and unlabeled proteins
    labeled_count_mongo = mongo.db.Domain_in_One.count_documents({"EC number": {"$ne": None}})
    unlabeled_count_mongo = mongo.db.Domain_in_One.count_documents({"EC number": None})
    total_proteins_mongo = mongo.db.Domain_in_One.count_documents({})  # Total proteins in MongoDB

    # Query Neo4j for isolated proteins
    query_isolated = "MATCH (p:Protein) WHERE NOT (p)-[:SIMILAR_TO]-() RETURN COUNT(p) AS isolated_count"
    isolated_count = graph.run(query_isolated).data()[0]['isolated_count']

    # Total proteins in Neo4j
    query_total_proteins = "MATCH (p:Protein) RETURN COUNT(p) AS total_proteins"
    total_proteins_neo4j = graph.run(query_total_proteins).data()[0]['total_proteins']

    # Labeled and unlabeled proteins in Neo4j
    query_labeled_ec = "MATCH (p:Protein) WHERE p.ec_number IS NOT NULL RETURN COUNT(p) AS labeled_ec_count"
    labeled_ec_count = graph.run(query_labeled_ec).data()[0]['labeled_ec_count']

    query_null_ec = "MATCH (p:Protein) WHERE p.ec_number IS NULL RETURN COUNT(p) AS null_ec_count"
    null_ec_count = graph.run(query_null_ec).data()[0]['null_ec_count']

    # Most common EC number in MongoDB
    most_common_ec = mongo.db.Domain_in_One.aggregate([
        {"$match": {"EC number": {"$ne": None}}},
        {"$group": {"_id": "$EC number", "count": {"$sum": 1}}},
        {"$sort": {"count": -1}},
        {"$limit": 1}
    ])
    most_common_ec_result = list(most_common_ec)
    most_common_ec_number = most_common_ec_result[0]['_id'] if most_common_ec_result else "N/A"

    # Average similarity in Neo4j
    query_avg_similarity = "MATCH ()-[r:SIMILAR_TO]->() RETURN avg(r.similarity) AS avg_similarity"
    avg_similarity_result = graph.run(query_avg_similarity).data()
    avg_similarity = avg_similarity_result[0]['avg_similarity'] if avg_similarity_result else 0

    # Pass statistics to the template
    stats = {
        "MongoDB": {
            "Labeled Proteins": labeled_count_mongo,
            "Unlabeled Proteins": unlabeled_count_mongo,
            "Total Proteins": total_proteins_mongo
        },
        "Neo4j": {
            "Labeled Proteins": labeled_ec_count,
            "Unlabeled Proteins": null_ec_count,
            "Total Proteins": total_proteins_neo4j,
            "Isolated Proteins": isolated_count,
            "Average Similarity": avg_similarity
        },
        "Most Common EC Number": most_common_ec_number
    }

    return render_template('statistics.html', stats=stats)

#Annotation Route
@app.route('/annotation')
def annotation():
    # Query to fetch proteins shown in the graph
    query = """
    MATCH (p:Protein)-[rel:SIMILAR_TO]->(neighbor:Protein)
    WHERE p.ec_number IS NOT NULL
    RETURN p.id AS protein_id, 
           p.ec_number AS assigned_ec, 
           neighbor.id AS similar_protein_id
    """
    results = graph.run(query).data()

    # Get protein IDs from the graph (optional: pre-filter graph nodes here if needed)
    graph_proteins = {record["protein_id"] for record in results}

    # Filter only proteins shown in the graph
    annotations = [
        {
            "protein_id": record["protein_id"],
            "assigned_ec": record["assigned_ec"],
            "similar_protein_id": record["similar_protein_id"]
        }
        for record in results
        if record["protein_id"] in graph_proteins
    ]

    # Render the template
    return render_template('annotation.html', annotations=annotations)

if __name__ == '__main__':
    app.run(debug=True, port=5001)
