import pandas as pd
import chromadb
from chromadb.utils import embedding_functions
import os

DB_DIR = "./chroma_db"
CSV_PATH = "../Customer Review.csv"
OLLAMA_MODEL = "nomic-embed-text"

def main():
    print(f"Loading data from {CSV_PATH}...")
    df = pd.read_csv(CSV_PATH)
    
    # Fill NaN values with empty string to avoid errors
    df.fillna("", inplace=True)
    
    print("Initialize ChromaDB...")
    client = chromadb.PersistentClient(path=DB_DIR)
    
    # Use Ollama locally for embeddings
    ollama_ef = embedding_functions.OllamaEmbeddingFunction(
        model_name=OLLAMA_MODEL,
        url="http://localhost:11434/api/embeddings" 
    )
    
    # Get or create collection
    collection = client.get_or_create_collection(
        name="customer_reviews",
        embedding_function=ollama_ef
    )
    
    # Convert data into lists for ChromaDB batch addition
    docs = []
    metadatas = []
    ids = []
    
    batch_size = 100
    
    print(f"Processing and embedding {len(df)} reviews...")
    for idx, row in df.iterrows():
        # Text to be embedded
        docs.append(row["ReviewText"])
        
        # Meta-data 
        meta = {
            "ProductModelName": row["ProductModelName"],
            "ProductCategory": row["ProductCategory"],
            "ManufacturerName": row["ManufacturerName"],
            "ReviewRating": str(row["ReviewRating"])
        }
        metadatas.append(meta)
        
        # ID
        # UserID might not be perfectly unique, adding index to ensure uniqueness
        ids.append(f"{row['UserID']}_{idx}")
        
        # Ingest in batches format
        if len(docs) >= batch_size:
            print(f"Adding batch of {len(docs)} up to index {idx}...")
            collection.add(
                documents=docs,
                metadatas=metadatas,
                ids=ids
            )
            docs = []
            metadatas = []
            ids = []
            
    # Add remaining docs
    if len(docs) > 0:
        print(f"Adding final batch of {len(docs)}...")
        collection.add(
            documents=docs,
            metadatas=metadatas,
            ids=ids
        )
        
    print("Ingestion complete.")
    print(f"Total entries in DB: {collection.count()}")

if __name__ == "__main__":
    main()
