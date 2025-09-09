"""
Промежуточная версия с FastAPI для тестирования
"""
import os
from fastapi import FastAPI

# FastAPI app
app = FastAPI(title="AI Bot FastAPI", description="FastAPI version for testing")

@app.get("/")
async def health_check():
    """Health check endpoint for Cloud Run"""
    return {"status": "ok", "message": "AI Bot FastAPI is running"}

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "healthy"}

@app.post("/webhook")
async def webhook():
    """Webhook endpoint for testing"""
    return {"ok": True, "message": "Webhook endpoint working"}

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8080))
    print(f"Starting FastAPI server on port {port}")
    uvicorn.run(app, host="0.0.0.0", port=port)
