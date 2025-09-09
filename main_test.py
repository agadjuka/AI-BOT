"""
Простая тестовая версия для проверки деплоя
"""
import os
from fastapi import FastAPI

# FastAPI app
app = FastAPI(title="AI Bot Test", description="Test version for deployment")

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "ok", "message": "AI Bot Test is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
