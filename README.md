# AlaSonora AI Engine

Decoupled bioacoustic microservice: FastAPI + BirdNET (via `birdnetlib`),
called only by the Spring Boot backend over the internal network.

## Setup

```bash
cd ai-engine
python -m venv .venv
.venv/Scripts/activate       # Windows
pip install -r requirements.txt
cp .env.example .env         # set INTERNAL_API_KEY
```
