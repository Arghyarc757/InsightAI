import os
import chromadb
from chromadb.utils import embedding_functions
from crewai import Agent, Task, Crew, LLM
from crewai.tools import tool
from dotenv import load_dotenv

load_dotenv()

# Initialize LLM for CrewAI 1.x formatting (Using Local Ollama Model!)
llm = LLM(
    model="ollama/qwen2.5:14b",
    base_url="http://localhost:11434",
    api_key="NA",
    temperature=0.1
)

# Initialize ChromaDB client and embeddings globally for the tool
DB_DIR = "./chroma_db"
OLLAMA_MODEL = "nomic-embed-text"

ollama_ef = embedding_functions.OllamaEmbeddingFunction(
    model_name=OLLAMA_MODEL,
    url="http://localhost:11434/api/embeddings"
)

client = chromadb.PersistentClient(path=DB_DIR)

# Retrieve the collection
try:
    collection = client.get_collection(name="customer_reviews", embedding_function=ollama_ef)
except Exception as e:
    collection = None
    print("Warning: Collection 'customer_reviews' not found. Ensure you run ingest_data.py first.")

def get_reviews(query: str, filters: dict = None) -> str:
    """Helper function to fetch a balanced mix of reviews (Top Matches + Critical Feedback)."""
    if collection is None:
        return "Database is not available or empty."
        
    try:
        where_filter = filters if filters else None
        
        # QUERY 1: Fetch Top 3 most relevant matches (usually positive in high-rated products)
        results_top = collection.query(
            query_texts=[query],
            n_results=3,
            where=where_filter
        )
        
        # QUERY 2: Specifically hunt for 1 or 2 star reviews to ensure "Weaknesses" are found
        # We merge the existing filters with a rating filter
        critical_filter = {"ReviewRating": {"$in": ["1", "2"]}}
        if where_filter:
            # If we already have filters (Manufacturer/Category), we $and them with the rating filter
            final_critical_filter = {"$and": [where_filter, critical_filter]}
        else:
            final_critical_filter = critical_filter
            
        results_critical = collection.query(
            query_texts=[query],
            n_results=2,
            where=final_critical_filter
        )
        
        # Combine results
        documents = results_top["documents"][0] + results_critical["documents"][0]
        metadatas = results_top["metadatas"][0] + results_critical["metadatas"][0]
        
        if not documents:
            return "No reviews found matching the query."
            
        formatted_results = []
        # Use a set to avoid showing the same review twice if it happened to be in both queries
        seen_texts = set()
        
        for i in range(len(documents)):
            doc = documents[i]
            if doc in seen_texts:
                continue
            seen_texts.add(doc)
            
            meta = metadatas[i]
            formatted_results.append(
                f"Review: {doc}\n"
                f"Rating: {meta['ReviewRating']}\n"
                f"Product: {meta['ProductModelName']}\n"
                "---"
            )
            
        return "\n".join(formatted_results)
    
    except Exception as e:
        return f"Error while searching database: {str(e)}"

def get_rating_distribution(query: str, filters: dict = None) -> dict:
    """Fetches up to 100 closest matching reviews to calculate Amazon-style global star distributions directly from the Database."""
    if collection is None:
        return {}
        
    try:
        where_filter = filters if filters else None
        results = collection.query(
            query_texts=[query],
            n_results=100, # Grab a huge sample size for the statistical distribution!
            where=where_filter
        )
        
        documents = results.get("documents", [[]])[0]
        metadatas = results.get("metadatas", [[]])[0]
        
        if not metadatas:
            return {}
            
        distribution = {"1": 0, "2": 0, "3": 0, "4": 0, "5": 0}
        reviews_by_star = {"1": [], "2": [], "3": [], "4": [], "5": []}
        
        total_rating = 0
        total_reviews = len(metadatas)
        
        for doc, meta in zip(documents, metadatas):
            stars = int(meta.get("ReviewRating", 0))
            if 1 <= stars <= 5:
                str_star = str(stars)
                distribution[str_star] += 1
                total_rating += stars
                # Store the raw text review and product name inside the specific star bin so the UI can render it.
                product_name = meta.get("ProductModelName", "Unknown Product")
                reviews_by_star[str_star].append({"product": product_name, "text": doc})
                
        avg_rating = round(total_rating / total_reviews, 1) if total_reviews > 0 else 0.0
        
        return {
            "average_rating": avg_rating,
            "total_reviews": total_reviews,
            "distribution": distribution,
            "reviews_by_star": reviews_by_star
        }
        
    except Exception as e:
        print(f"Error fetching distribution: {e}")
        return {}

# Define the Agent without tools
sentiment_analyzer = Agent(
    role="Customer Sentiment Analyst",
    goal="Analyze customer reviews and extract actionable insights, strengths, and weaknesses accurately without hallucination.",
    backstory="""You are a strict, senior data analyst working for a retail corporation. 
    You synthesize summaries but you NEVER hallucinate facts. You rely strictly on provided context.""",
    verbose=True,
    allow_delegation=False,
    llm=llm
)

def build_and_run_crew(query: str, product_category: str = None, manufacturer: str = None):
    """Function triggered by the FastAPI endpoint to run the analysis."""
    
    # We construct the chromadb filter dictionary if needed
    raw_filters = {}
    if product_category and product_category.lower() != "all":
        raw_filters["ProductCategory"] = product_category
    if manufacturer and manufacturer.lower() != "all":
        raw_filters["ManufacturerName"] = manufacturer
        
    filters = None
    if len(raw_filters) == 1:
        filters = raw_filters
    elif len(raw_filters) > 1:
        filters = {"$and": [{k: v} for k, v in raw_filters.items()]}
        
    # Fetch reviews directly in Python
    reviews_content = get_reviews(query, filters)
    
    # Fetch the deep analytics for the React Frontend Bar Charts
    distribution_analytics = get_rating_distribution(query, filters)

    expected_output_format = """
    A valid JSON object matching this schema exactly without markdown wrapping:
    {
      "sentiment_label": "Positive", // Must be "Positive", "Negative", or "Mixed".
      "rating_overview": "A 2-3 sentence summary of the general sentiment and average rating.",
      "strengths": ["string", "string", "string", "string", "string"],
      "weaknesses": ["string", "string", "string", "string", "string"]
    }
    """
    
    analysis_task = Task(
        description=f"""
        Investigate customer sentiment regarding the following search query: '{query}'.
        
        GLOBAL DATABASE STATISTICS (Use this for your rating_overview and sentiment_label):
        - Total Matching Reviews: {distribution_analytics.get('total_reviews', 0)}
        - Average Rating: {distribution_analytics.get('average_rating', 0)} out of 5
        - 5-Star Count: {distribution_analytics.get('distribution', {}).get('5', 0)} reviews
        - 1-Star Count: {distribution_analytics.get('distribution', {}).get('1', 0)} reviews
        
        SPECIFIC WRITTEN REVIEWS (A balanced sample of Top Relevant + Critical Feedback):
        {reviews_content}
        
        Procedure:
        1. Analyze the 'GLOBAL DATABASE STATISTICS' to understand the overall sentiment, and assign a 'sentiment_label' of exactly 'Positive', 'Negative', or 'Mixed'.
        2. Identify the core rating overview by blending the global stats and the written reviews. 
        3. Extract the TOP 5 strengths (what people loved).
        4. Extract the TOP 5 weaknesses (what people hated or had issues with).
        
        CRITICAL RULES TO PREVENT HALLUCINATION:
        - BRAND CONSISTENCY: Only extract strengths and weaknesses for products that match the brand in the query (e.g., if searching for 'Dell', do NOT include 'HP' or 'Surface' findings).
        - NO IMAGINARY DATA: DO NOT invent weaknesses or strengths that are not explicitly stated in the reviews. For instance, do NOT mention "battery life" if no one complains about it.
        - PERFECT ARRAYS: If there are fewer than 5 real strengths or weaknesses, place an empty string `""` in the remaining slots to perfectly fill the 5 string array.
        - REASONING: "It's an Apple product" is not a weakness, but "The software is restrictive" could be. Read accurately!
        
        Ensure your final output is strictly in the requested JSON format, containing exactly 5 items per category.
        """,
        expected_output=expected_output_format,
        agent=sentiment_analyzer
    )
    
    crew = Crew(
        agents=[sentiment_analyzer],
        tasks=[analysis_task],
        verbose=True
    )
    
    result = crew.kickoff()
    return result.raw, distribution_analytics
