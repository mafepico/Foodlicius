from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from menu_generator import generate_weekly_menu, get_recipes_with_ingredients
import sqlite3

app = FastAPI(
    title="Foodlicius API",
    description="API para generar menús semanales optimizados por presupuesto con precios reales de Mercadona.",
    version="1.0.0"
)

# Permitir conexiones desde cualquier origen (útil para conectar el frontend web)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def home():
    return {
        "app": "Foodlicius",
        "status": "online",
        "description": "API generadora de menús semanales inteligentes por presupuesto"
    }

@app.get("/recipes")
def list_recipes():
    """Devuelve el catálogo de recetas disponibles con sus ingredientes."""
    almuerzos, cenas = get_recipes_with_ingredients()
    return {
        "total_almuerzos": len(almuerzos),
        "total_cenas": len(cenas),
        "almuerzos": almuerzos,
        "cenas": cenas
    }

@app.get("/menu/generate")
def get_menu(budget: float = Query(60.0, ge=20.0, le=300.0, description="Presupuesto máximo en euros")):
    """Genera un menú semanal optimizado según el presupuesto solicitado."""
    resultado, error = generate_weekly_menu(budget)
    if error:
        raise HTTPException(status_code=400, detail=error)
    return resultado
