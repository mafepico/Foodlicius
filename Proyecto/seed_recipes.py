import sqlite3

DB_NAME = "foodlicius.db"

# Recetas con consumo por ración (portion_grams: en gramos o unidades)
RECETAS = [
    {
        "name": "Pasta con tomate y atún",
        "meal_type": "almuerzo",
        "ingredients": [
            {"kw": "plumas", "portion_grams": 100},
            {"kw": "tomate frito", "portion_grams": 100},
            {"kw": "atún claro en aceite de oliva", "portion_grams": 80}
        ]
    },
    {
        "name": "Pasta salteada con calabacín",
        "meal_type": "cena",
        "ingredients": [
            {"kw": "plumas", "portion_grams": 100},
            {"kw": "calabacín", "portion_grams": 150}
        ]
    },
    {
        "name": "Pasta con tomate y bacon",
        "meal_type": "almuerzo",
        "ingredients": [
            {"kw": "plumas", "portion_grams": 100},
            {"kw": "tomate frito", "portion_grams": 100},
            {"kw": "bacon en tiras", "portion_grams": 60}
        ]
    },
    {
        "name": "Arroz con tomate y huevos",
        "meal_type": "almuerzo",
        "ingredients": [
            {"kw": "arroz redondo", "portion_grams": 100},
            {"kw": "tomate frito", "portion_grams": 100},
            {"kw": "huevos grandes l", "portion_grams": 120}  # ~2 huevos
        ]
    },
    {
        "name": "Wok de arroz con carne y verduras",
        "meal_type": "almuerzo",
        "ingredients": [
            {"kw": "arroz redondo", "portion_grams": 100},
            {"kw": "cintas de lomo", "portion_grams": 150},
            {"kw": "brócoli", "portion_grams": 120},
            {"kw": "zanahoria", "portion_grams": 80},
            {"kw": "salsa de soja", "portion_grams": 20}
        ]
    },
    {
        "name": "Pollo a la plancha con patatas y verdura",
        "meal_type": "cena",
        "ingredients": [
            {"kw": "pechuga de pollo filetes", "portion_grams": 150},
            {"kw": "patatas", "portion_grams": 200},
            {"kw": "brócoli", "portion_grams": 120}
        ]
    },
    {
        "name": "Salteado de calabacín con lomo de cerdo",
        "meal_type": "cena",
        "ingredients": [
            {"kw": "calabacín", "portion_grams": 200},
            {"kw": "cintas de lomo", "portion_grams": 150}
        ]
    },
    {
        "name": "Lomo con patatas al horno",
        "meal_type": "almuerzo",
        "ingredients": [
            {"kw": "cintas de lomo", "portion_grams": 150},
            {"kw": "patatas", "portion_grams": 250}
        ]
    },
    {
        "name": "Lasaña de calabacín y carne",
        "meal_type": "cena",
        "ingredients": [
            {"kw": "calabacín", "portion_grams": 250},
            {"kw": "carne picada vacuno y cerdo", "portion_grams": 150},
            {"kw": "tomate frito", "portion_grams": 100},
            {"kw": "mozzarella rallada", "portion_grams": 50}
        ]
    },
    {
        "name": "Ensalada de pollo con tomate",
        "meal_type": "cena",
        "ingredients": [
            {"kw": "pechuga de pollo filetes", "portion_grams": 150},
            {"kw": "canónigos", "portion_grams": 50},
            {"kw": "tomate ensalada", "portion_grams": 150}
        ]
    }
]

def vincular():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    cursor.execute("DROP TABLE IF EXISTS recipe_ingredients")
    cursor.execute("DROP TABLE IF EXISTS recipes")

    cursor.execute("""
    CREATE TABLE recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        servings INTEGER DEFAULT 1
    )
    """)

    cursor.execute("""
    CREATE TABLE recipe_ingredients (
        recipe_id INTEGER,
        product_id TEXT,
        portion_grams REAL,
        PRIMARY KEY (recipe_id, product_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    print(" Registrando recetas con gramaje por ración...")

    for r in RECETAS:
        cursor.execute(
            "INSERT INTO recipes (name, meal_type, servings) VALUES (?, ?, 1)",
            (r["name"], r["meal_type"])
        )
        recipe_id = cursor.lastrowid
        print(f"\n Plato: {r['name']}")

        for ing in r["ingredients"]:
            kw = ing["kw"]
            terminos = kw.lower().split()
            where_clause = " AND ".join(["LOWER(name) LIKE ?"] * len(terminos))
            where_clause += " AND LOWER(name) NOT LIKE '%paté%' AND LOWER(name) NOT LIKE '%sabor%'"
            params = [f"%{t}%" for t in terminos]

            cursor.execute(f"SELECT id, name, price, packaging FROM products WHERE {where_clause} ORDER BY price ASC LIMIT 1", params)
            prod = cursor.fetchone()

            if not prod:
                cursor.execute(
                    "SELECT id, name, price, packaging FROM products WHERE LOWER(name) LIKE ? AND LOWER(name) NOT LIKE '%paté%' ORDER BY price ASC LIMIT 1",
                    (f"%{terminos[0]}%",)
                )
                prod = cursor.fetchone()

            if prod:
                prod_id, prod_name, prod_price, packaging = prod
                cursor.execute(
                    "INSERT OR IGNORE INTO recipe_ingredients (recipe_id, product_id, portion_grams) VALUES (?, ?, ?)",
                    (recipe_id, prod_id, ing["portion_grams"])
                )
                print(f"    {prod_name} ({prod_price} €) -> {ing['portion_grams']} g/ración")
            else:
                print(f"   ⚠️ No encontrado: {kw}")

    conn.commit()
    conn.close()
    print("\n Base de datos actualizada con gramajes.")

if __name__ == "__main__":
    vincular()
