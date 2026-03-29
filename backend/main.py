from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import pandas as pd
import json

from agent import build_and_run_crew

app = FastAPI(title="Customer Review Analysis API")

# Setup CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # For development
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

CSV_PATH = "../Customer Review.csv"

class QueryRequest(BaseModel):
    query: str
    product_category: str = "All"
    manufacturer: str = "All"

@app.get("/api/categories")
def get_categories():
    try:
        df = pd.read_csv(CSV_PATH)
        categories = sorted(df["ProductCategory"].dropna().unique().tolist())
        return {"categories": ["All"] + categories}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/manufacturers")
def get_manufacturers():
    try:
        df = pd.read_csv(CSV_PATH)
        manufacturers = sorted(df["ManufacturerName"].dropna().unique().tolist())
        return {"manufacturers": ["All"] + manufacturers}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/analyze")
def analyze_reviews(req: QueryRequest):
    try:
        # Pass logic to the CrewAI Agent
        raw_result, dist_data = build_and_run_crew(
            query=req.query,
            product_category=req.product_category,
            manufacturer=req.manufacturer
        )
        
        # We need to parse the JSON string back into a dict for FastAPI transport
        clean_result = raw_result.strip()
        if clean_result.startswith("```json"):
            clean_result = clean_result.replace("```json", "", 1)
        if clean_result.endswith("```"):
            clean_result = clean_result[:-3]
        clean_result = clean_result.strip()
        
        data = json.loads(clean_result)
        
        return {
            "analysis": data,
            "statistics": dist_data
        }
        
    except json.JSONDecodeError:
        # Fallback if parsing fails
        return {
            "analysis": {
                "sentiment_label": "Mixed",
                "rating_overview": f"Raw Output (Failed to parse JSON): {raw_result}",
                "strengths": ["Could not parse strengths.", "", "", "", ""],
                "weaknesses": ["Could not parse weaknesses.", "", "", "", ""]
            },
            "statistics": dist_data if 'dist_data' in locals() else {}
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
