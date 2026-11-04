import sqlite3
import random

DB_NAME = "foodlicius.db"

def get_recipes_with_ingredients():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT id, name, meal_type FROM recipes")
    recipes = [dict(r) for r in cursor.fetchall()]

    cursor.execute("""
        SELECT ri.recipe_id, p.id as product_id, p.name as product_name, p.price
        FROM recipe_ingredients ri
        JOIN products p ON ri.product_id = p.id
    """)
    ing_rows = cursor.fetchall()
    conn.close()

    recipe_map = {r["id"]: {**r, "ingredients": []} for r in recipes}
    for row in ing_rows:
        if row["recipe_id"] in recipe_map:
            recipe_map[row["recipe_id"]]["ingredients"].append({
                "id": row["product_id"],
                "name": row["product_name"],
                "price": row["price"]
            })

    valid_recipes = [r for r in recipe_map.values() if len(r["ingredients"]) > 0]
    for r in valid_recipes:
        r["approx_cost"] = sum(i["price"] for i in r["ingredients"])

    valid_recipes.sort(key=lambda x: x["approx_cost"])
    return valid_recipes

def generate_weekly_menu(budget_max):
    recipes = get_recipes_with_ingredients()

    if not recipes:
        return None, "No hay recetas disponibles en la base de datos."

    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    mejor_plan = []
    cesta_compra = {}
    coste_acumulado = 0.0

    comidas_disponibles = recipes.copy()
    idx_dia = 0
    toma = "almuerzo"
    
    while idx_dia < 7:
        plato_elegido = None
        random.shuffle(comidas_disponibles)
        # Priorizar recetas que compartan ingredientes ya en la cesta
        comidas_disponibles.sort(
            key=lambda r: sum(i["price"] for i in r["ingredients"] if i["id"] not in cesta_compra)
        )

        for receta in comidas_disponibles:
            nuevos_costes = sum(
                i["price"] for i in receta["ingredients"] if i["id"] not in cesta_compra
            )
            if coste_acumulado + nuevos_costes <= budget_max:
                plato_elegido = receta
                coste_acumulado += nuevos_costes
                for i in receta["ingredients"]:
                    cesta_compra[i["id"]] = i
                break

        if not plato_elegido:
            break

        dia_actual = dias_nombres[idx_dia]
        if toma == "almuerzo":
            mejor_plan.append({
                "dia": dia_actual,
                "almuerzo": plato_elegido["name"],
                "cena": "Aprovechamiento de sobras / Despensa"
            })
            toma = "cena"
        else:
            mejor_plan[-1]["cena"] = plato_elegido["name"]
            toma = "almuerzo"
            idx_dia += 1

    # Si con 5 € no da para la receta más completa, se devuelve la más barata posible
    if not mejor_plan:
        receta_barata = recipes[0]
        cesta = {i["id"]: i for i in receta_barata["ingredients"]}
        coste_barata = round(sum(i["price"] for i in cesta.values()), 2)
        
        return {
            "budget_max": budget_max,
            "total_cost": coste_barata,
            "savings": round(budget_max - coste_barata, 2),
            "mensaje": f"Presupuesto ultra-ajustado: cubriendo comidas base esenciales.",
            "plan": [{"dia": "Lunes", "almuerzo": receta_barata["name"], "cena": "Aprovechamiento"}],
            "shopping_list": list(cesta.values())
        }, None

    return {
        "budget_max": budget_max,
        "total_cost": round(coste_acumulado, 2),
        "savings": round(budget_max - coste_acumulado, 2),
        "plan": mejor_plan,
        "shopping_list": list(cesta_compra.values())
    }, None
