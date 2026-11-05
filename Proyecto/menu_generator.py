import sqlite3
<<<<<<< Updated upstream
import re
=======
import random
from pathlib import Path
>>>>>>> Stashed changes

DB_NAME = str(Path(__file__).resolve().parent / "foodlicius.db")

def parse_weight_in_grams(packaging_str, default_weight=500.0):
    if not packaging_str:
        return default_weight

    text = packaging_str.lower().replace(",", ".")

    match_kg = re.search(r"(\d+(?:\.\d+)?)\s*kg", text)
    if match_kg:
        return float(match_kg.group(1)) * 1000.0

    match_g = re.search(r"(\d+(?:\.\d+)?)\s*g", text)
    if match_g:
        return float(match_g.group(1))

    match_uds = re.search(r"(\d+)\s*(?:uds|unidades)", text)
    if match_uds:
        return float(match_uds.group(1)) * 60.0

    return default_weight

def get_recipes_data():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, meal_type FROM recipes")
    recipes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT ri.recipe_id, ri.portion_grams, p.id as product_id, p.name as product_name, p.price, p.packaging
        FROM recipe_ingredients ri
        JOIN products p ON ri.product_id = p.id
    """)
    rows = cursor.fetchall()
    conn.close()

    recipe_map = {r["id"]: {**r, "ingredients": []} for r in recipes}
    for row in rows:
        total_grams = parse_weight_in_grams(row["packaging"])
        recipe_map[row["recipe_id"]]["ingredients"].append({
            "id": row["product_id"],
            "name": row["product_name"],
            "price": row["price"],
            "packaging": row["packaging"],
            "portion_grams": row["portion_grams"],
            "pack_grams": total_grams
        })

    return [r for r in recipe_map.values() if len(r["ingredients"]) > 0]

def generate_weekly_menu(budget_max):
    recipes = get_recipes_data()
    if not recipes:
        return None, "No hay recetas disponibles en la base de datos."

    dias_semana = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    pantry = {}
    
    slots = []
    for d in dias_semana:
        slots.append((d, "almuerzo"))
        slots.append((d, "cena"))

    current_day_plan = {}

    for day, slot_type in slots:
        candidatas = []
        for r in recipes:
            coste_adicional = 0.0
            packs_a_sumar = {}

            for ing in r["ingredients"]:
                pid = ing["id"]
                needed = ing["portion_grams"]
                stock = pantry[pid]["grams_left"] if pid in pantry else 0.0

                if stock < needed:
                    coste_adicional += ing["price"]
                    packs_a_sumar[pid] = ing["pack_grams"]

            coste_actual = sum(item["price"] * item["packs"] for item in pantry.values())
            if coste_actual + coste_adicional <= budget_max:
                candidatas.append({
                    "recipe": r,
                    "added_cost": coste_adicional,
                    "packs_needed": packs_a_sumar
                })

        if not candidatas:
            break

        candidatas.sort(key=lambda c: (c["added_cost"], c["recipe"]["meal_type"] != slot_type))
        elegida = candidatas[0]
        receta_obj = elegida["recipe"]

        for ing in receta_obj["ingredients"]:
            pid = ing["id"]
            if pid not in pantry:
                pantry[pid] = {
                    "id": pid,
                    "name": ing["name"],
                    "price": ing["price"],
                    "packaging": ing["packaging"],
                    "grams_left": ing["pack_grams"],
                    "packs": 1
                }
            elif ing["portion_grams"] > pantry[pid]["grams_left"]:
                pantry[pid]["packs"] += 1
                pantry[pid]["grams_left"] += ing["pack_grams"]

            pantry[pid]["grams_left"] -= ing["portion_grams"]

        if day not in current_day_plan:
            current_day_plan[day] = {"dia": day, "almuerzo": "-", "cena": "-"}
        current_day_plan[day][slot_type] = receta_obj["name"]

    coste_final = round(sum(p["price"] * p["packs"] for p in pantry.values()), 2)
    plan_resultado = list(current_day_plan.values())

    shopping_list = [
        {
            "id": p["id"],
            "name": p["name"],
            "price": p["price"],
            "packs": p["packs"],
            "subtotal": round(p["price"] * p["packs"], 2),
            "stock_remanente": f"Quedan ~{int(p['grams_left'])} g"
        }
        for p in pantry.values()
    ]

    return {
        "budget_max": budget_max,
        "total_cost": coste_final,
        "savings": round(budget_max - coste_final, 2),
        "total_comidas_cubiertas": sum(1 for d in plan_resultado for t in ["almuerzo", "cena"] if d[t] != "-"),
        "plan": plan_resultado,
        "shopping_list": shopping_list
    }, None
