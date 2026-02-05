
from fastapi import FastAPI
from datetime import date
from dateutil.parser import parse
import requests

app = FastAPI(title="DeFi Education Simulator")

EXPONENT_API = "https://api.exponent.finance/markets"
LLAMA_API = "https://yields.llama.fi/pools"

def simulate_variable(principal, apy, years):
    return round(principal * ((1 + apy / 100) ** years), 2)

def simulate_fixed(principal, apy, maturity):
    maturity_date = parse(maturity).date()
    years = max((maturity_date - date.today()).days / 365, 0)
    return round(principal * (1 + apy / 100 * years), 2)

@app.get("/assets")
def assets():
    fixed, variable = [], []

    markets = requests.get(EXPONENT_API, timeout=10).json()
    for m in markets:
        s = m.get("symbol", "").lower()
        if any(x in s for x in ["onyc", "pst", "hyusd", "shyusd"]):
            fixed.append({
                "asset": m.get("symbol"),
                "apy": m.get("apy"),
                "maturity": m.get("maturityDate"),
                "yield_type": "fixed",
                "protocol": "Exponent"
            })

    pools = requests.get(LLAMA_API, timeout=10).json()["data"]
    for p in pools:
        if p.get("project") == "kamino" and any(x in p.get("symbol","").lower() for x in ["onyc","pst","hyusd","shyusd"]):
            variable.append({
                "asset": p.get("symbol"),
                "apy": p.get("apy"),
                "yield_type": "variable",
                "protocol": "Kamino"
            })

    return {"fixed": fixed, "variable": variable}

@app.post("/compare")
def compare(data: dict):
    amount = data["amount"]
    years = data["years"]
    assets = data["assets"]

    out = []
    for a in assets:
        if a["yield_type"] == "fixed":
            final = simulate_fixed(amount, a["apy"], a["maturity"])
        else:
            final = simulate_variable(amount, a["apy"], years)

        out.append({
            "asset": a["asset"],
            "protocol": a["protocol"],
            "apy": a["apy"],
            "final_value": final,
            "earnings": round(final - amount, 2)
        })

    return out
