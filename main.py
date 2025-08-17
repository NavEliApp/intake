import os, json
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
from openai import OpenAI

# --- ENV ---
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# --- APP SETUP ---
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten to your domains later
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- HEALTH ROUTE ---
@app.get("/")
def health():
    return {"ok": True, "message": "NavEli Intake is running 🚀"}

# --- MODELS ---
class Attachment(BaseModel):
    type: str
    name: Optional[str] = None
    notes: Optional[str] = None

class Details(BaseModel):
    date: Optional[str] = None
    time_window: Optional[str] = ""
    guest_count: Optional[int] = 0
    location_pref: Optional[str] = ""
    budget_currency: Optional[str] = "USD"
    budget_amount: Optional[float] = 0
    preferences: List[str] = []
    donts: List[str] = []
    targets: List[str] = []
    deliverables: List[str] = []
    special_notes: Optional[str] = ""

class Ticket(BaseModel):
    category: str
    task_type: str
    summary: str
    details: Details
    contact: dict
    attachments: List[Attachment] = []
    sla: str = "standard"
    scope_check: dict
    routing: dict

# --- ENDPOINT ---
@app.post("/intake")
def intake(payload: dict):
    user_msg = (payload or {}).get("message", "")
    system_prompt = (
        "You are NavEli Intake AI. Ask only for missing info. "
        "When enough info is gathered, output ONLY the Ticket JSON "
        "per the schema. If out-of-scope, return a short refusal."
    )

    resp = client.chat.completions.create(
        model="gpt-4o-mini",
        temperature=0.3,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_msg},
            {"role": "system", "content": "Emit strictly valid JSON only."},
        ],
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        ticket = Ticket(**json.loads(raw))
        return {
            "ok": True,
            "ticket": {
                "id": f"TCK-{os.urandom(4).hex()}",
                "queue": ticket.routing.get("queue"),
            },
        }
    except Exception as e:
        return {"ok": False, "error": str(e), "raw": raw}
