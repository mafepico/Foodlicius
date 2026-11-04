import sqlite3
import random

DB_NAME = "foodlicius.db"

def get_recipes_with_ingredients():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Obtener recetas
    cursor.execute("SELECT id, name, meal_type FROM recipes")
    recipes = [dict(r) for r in cursor.fetchall()]

    # Obtener ingredientes asociados por receta
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

    almuerzos = [r for r in recipe_map.values() if r["meal_type"] == "almuerzo"]
    cenas = [r for r in recipe_map.values() if r["meal_type"] == "cena"]
    return almuerzos, cenas

def generate_weekly_menu(budget_max):
    almuerzos, cenas = get_recipes_with_ingredients()

    if not almuerzos or not cenas:
        return None, "Faltan recetas en la base de datos."

    dias = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
    mejor_plan = None
    mejor_coste = float("inf")
    mejor_cesta = {}

    for _ in range(1000):
        plan_semanal = []
        productos_semana = {}
        ultimo_almuerzo = None
        ultima_cena = None

        for dia in dias:
            # Seleccionar almuerzo sin repetir el del día previo
            opc_almuerzo = [a for a in almuerzos if a["id"] != ultimo_almuerzo]
            almuerzo = random.choice(opc_almuerzo)

            # Seleccionar cena sin repetir la del día previo
            opc_cena = [c for c in cenas if c["id"] != ultima_cena]
            cena = random.choice(opc_cena)

            # Registrar ingredientes necesarios en la cesta común
            for ing in almuerzo["ingredients"] + cena["ingredients"]:
                productos_semana[ing["id"]] = ing

            plan_semanal.append({
                "dia": dia,
                "almuerzo": almuerzo["name"],
                "cena": cena["name"]
            })

            ultimo_almuerzo = almuerzo["id"]
            ultima_cena = cena["id"]

        # Coste real sumando cada producto del supermercado una sola vez
        coste_total_cesta = round(sum(p["price"] for p in productos_semana.values()), 2)

        if coste_total_cesta <= budget_max and coste_total_cesta < mejor_coste:
            mejor_coste = coste_total_cesta
            mejor_plan = plan_semanal
            mejor_cesta = productos_semana

    if not mejor_plan:
        return None, f"No se encontró un menú que entre en {budget_max} €. La cesta base mínima ronda un valor más alto. Prueba con 70 € o 75 €."

    return {
        "budget_max": budget_max,
        "total_cost": mejor_coste,
        "savings": round(budget_max - mejor_coste, 2),
        "plan": mejor_plan,
        "shopping_list": list(mejor_cesta.values())
    }, None

if __name__ == "__main__":
    presupuesto = 60.0
    resultado, error = generate_weekly_menu(presupuesto)

    if error:
        print(f"❌ {error}")
    else:
        print(f"\n Menú Semanal Generado (Tope: {resultado['budget_max']} €)")
        print(f" Coste Total Cesta: {resultado['total_cost']} € | Ahorro: {resultado['savings']} €\n")
        print(f"{'Día':<12} | {'Almuerzo':<35} | {'Cena':<35}")
        print("-" * 85)
        for d in resultado["plan"]:
            print(f"{d['dia']:<12} | {d['almuerzo']:<35} | {d['cena']:<35}")

        print(f"\n Lista de la compra Mercadona ({len(resultado['shopping_list'])} productos):")
        print("-" * 65)
        for item in resultado["shopping_list"]:
            print(f"- {item['name']:<50} | {item['price']} €")
