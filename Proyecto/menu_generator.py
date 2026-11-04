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

    # Filtrar solo recetas que tengan ingredientes vinculados
    valid_recipes = [r for r in recipe_map.values() if len(r["ingredients"]) > 0]
    
    # Calcular coste estimado individual de cada plato
    for r in valid_recipes:
        r["approx_cost"] = sum(i["price"] for i in r["ingredients"])

    # Ordenar por las más baratas primero
    valid_recipes.sort(key=lambda x: x["approx_cost"])
    return valid_recipes

def generate_weekly_menu(budget_max):
    recipes = get_recipes_with_ingredients()

    if not recipes:
        return None, "No hay recetas disponibles en la base de datos."

    # Encontrar el producto/ingrediente más barato para validar umbral mínimo
    precio_minimo = min(r["approx_cost"] for r in recipes)
    if budget_max < min(i["price"] for r in recipes for i in r["ingredients"]):
        return None, f"El presupuesto de {budget_max} € es inferior al ingrediente más barato del supermercado."

    dias_nombres = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    
    mejor_plan = []
    cesta_compra = {}
    coste_acumulado = 0.0

    # Construir comidas de forma incremental hasta agotar el presupuesto
    comidas_disponibles = recipes.copy()
    
    # Intentar llenar hasta 7 días (almuerzo y cena = 14 tomas)
    idx_dia = 0
    toma = "almuerzo"
    
    while idx_dia < 7:
        plato_elegido = None
        
        # Buscar un plato cuyos NUEVOS ingredientes agregados no superen el presupuesto restante
        random.shuffle(comidas_disponibles)
        # Priorizar recetas que compartan ingredientes que ya estén en la cesta
        comidas_disponibles.sort(
            key=lambda r: sum(i["price"] for i in r["ingredients"] if i["id"] not in cesta_compra)
        )

        for receta in comidas_disponibles:
            # Calcular cuánto sumaría a la cesta agregar esta receta
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
            # Ya no alcanza el dinero para más comidas sin pasarse de presupuesto
            break

        # Registrar la comida en el plan
        dia_actual = dias_nombres[idx_dia]
        if toma == "almuerzo":
            mejor_plan.append({
                "dia": dia_actual,
                "almuerzo": plato_elegido["name"],
                "cena": "Aprovechamiento / Ayuno / Por planificar"
            })
            toma = "cena"
        else:
            mejor_plan[-1]["cena"] = plato_elegido["name"]
            toma = "almuerzo"
            idx_dia += 1

    if not mejor_plan:
        # Si ni siquiera entra un plato completo, devolvemos la receta más económica posible
        receta_barata = recipes[0]
        return {
            "budget_max": budget_max,
            "total_cost": round(receta_barata["approx_cost"], 2),
            "savings": round(budget_max - receta_barata["approx_cost"], 2),
            "mensaje": f"Presupuesto ajustado: se sugiere 1 plato base económico.",
            "plan": [{"dia": "Día 1", "almuerzo": receta_barata["name"], "cena": "Restos / Opcional"}],
            "shopping_list": receta_barata["ingredients"]
        }, None

    return {
        "budget_max": budget_max,
        "total_cost": round(coste_acumulado, 2),
        "savings": round(budget_max - coste_acumulado, 2),
        "total_comidas_cubiertas": len(mejor_plan) * 2 if mejor_plan[-1]["cena"] != "Aprovechamiento / Ayuno / Por planificar" else len(mejor_plan) * 2 - 1,
        "plan": mejor_plan,
        "shopping_list": list(cesta_compra.values())
    }, None

if __name__ == "__main__":
    for test_budget in [5.0, 15.0, 60.0]:
        print(f"\n================ PROBANDO CON {test_budget} € ================")
        res, err = generate_weekly_menu(test_budget)
        if err:
            print(f"❌ {err}")
        else:
            print(f" Coste Cesta: {res['total_cost']} € | Ahorro: {res['savings']} €")
            print(f" Comidas logradas: {len(res['plan'])} días")
            for p in res["plan"]:
                print(f"  - {p['dia']}: {p['almuerzo']} | {p['cena']}")
            print(f" Productos en la compra ({len(res['shopping_list'])}):")
            for prod in res["shopping_list"]:
                print(f"    * {prod['name']} ({prod['price']} €)")
            