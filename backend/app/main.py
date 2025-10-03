from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
app = FastAPI(title="Logistics POC API")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"], allow_credentials=True)

@app.get('/health')
def health():
    return {"ok": True}

@app.get('/warehouses')
def warehouses():
    return [
      {"id":"W-BRAMPTON-DC","name":"Martin Brower Brampton DC","lat":43.7505,"lon":-79.6773},
      {"id":"W-OSHAWA-DC","name":"Martin Brower Oshawa DC","lat":43.9537,"lon":-78.8690}
    ]