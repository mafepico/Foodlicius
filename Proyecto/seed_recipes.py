import sqlite3

DB_NAME = "foodlicius.db"

# Lista de recetas base
RECETAS = [
    {"name": "Pasta con tomate y atún", "meal_type": "almuerzo", "keywords": ["macarrones", "tomate frito", "atún"]},
    {"name": "Pasta con tomate y bacon", "meal_type": "almuerzo", "keywords": ["macarrones", "tomate frito", "bacon"]},
    {"name": "Lasaña tradicional de carne", "meal_type": "almuerzo", "keywords": ["lasaña", "carne picada", "tomate frito", "mozzarella"]},
    {"name": "Wok de arroz con carne y verduras", "meal_type": "almuerzo", "keywords": ["arroz", "carne", "brócoli", "zanahoria", "soja"]},
    {"name": "Lomo con manzana y puré de patata", "meal_type": "almuerzo", "keywords": ["lomo", "manzana", "patata"]},
    {"name": "Ensalada de pollo y mozzarella", "meal_type": "cena", "keywords": ["pechuga", "canónigos", "tomate", "mozzarella"]},
    {"name": "Lasaña de calabacín y carne", "meal_type": "cena", "keywords": ["calabacín", "carne picada", "tomate frito", "mozzarella"]},
    {"name": "Salmón con soja y verduras salteadas", "meal_type": "cena", "keywords": ["salmón", "soja", "brócoli", "zanahoria"]},
    {"name": "Pollo a la plancha con patatas y verdura", "meal_type": "cena", "keywords": ["pechuga", "patata", "brócoli", "zanahoria"]},
    {"name": "Pescado con ensalada y patatas", "meal_type": "cena", "keywords": ["merluza", "canónigos", "tomate", "patata"]},
]

def vincular_recetas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()

    # 1. Asegurar que las tablas de recetas existen
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        meal_type TEXT NOT NULL,
        servings INTEGER DEFAULT 2
    )
    """)

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS recipe_ingredients (
        recipe_id INTEGER,
        product_id TEXT,
        quantity_needed REAL,
        PRIMARY KEY (recipe_id, product_id),
        FOREIGN KEY (recipe_id) REFERENCES recipes(id),
        FOREIGN KEY (product_id) REFERENCES products(id)
    )
    """)

    print(" Registrando recetas base...")

    for r in RECETAS:
        # 2. Insertar receta evitando duplicados
        cursor.execute("SELECT id FROM recipes WHERE name = ?", (r["name"],))
        existe = cursor.fetchone()

        if existe:
            recipe_id = existe[0]
        else:
            cursor.execute(
                "INSERT INTO recipes (name, meal_type, servings) VALUES (?, ?, 2)",
                (r["name"], r["meal_type"])
            )
            recipe_id = cursor.lastrowid

        print(f"\n Plato: {r['name']} (ID: {recipe_id})")

        # 3. Intentar asociar ingredientes buscando por palabra clave
        for kw in r["keywords"]:
            cursor.execute(
                "SELECT id, name, price FROM products WHERE name LIKE ? LIMIT 1",
                (f"%{kw}%",)
            )
            prod = cursor.fetchone()

            if prod:
                prod_id, prod_name, prod_price = prod
                cursor.execute(
                    "INSERT OR IGNORE INTO recipe_ingredients (recipe_id, product_id, quantity_needed) VALUES (?, ?, ?)",
                    (recipe_id, prod_id, 1.0)
                )
                print(f"    Ingrediente: {prod_name} ({prod_price} €)")
            else:
                print(f"   ⚠️ No encontrado: '{kw}'")

    conn.commit()
    conn.close()
    print("\n ¡Proceso completado!")

if __name__ == "__main__":
    vincular_recetas()
