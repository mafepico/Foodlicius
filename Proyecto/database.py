import sqlite3

DB_NAME = "foodlicius.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Tabla para almacenar el catálogo de productos de Mercadona
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS products (
        id TEXT PRIMARY KEY,
        name TEXT NOT NULL,
        price REAL NOT NULL,
        packaging TEXT,
        category TEXT,
        image_url TEXT,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)
    
    conn.commit()
    conn.close()
    print(" Base de datos inicializada con éxito (foodlicius.db).")

def save_products(products_list):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Insertar o actualizar si ya existe el producto (upsert)
    cursor.executemany("""
    INSERT INTO products (id, name, price, packaging, category, image_url)
    VALUES (:id, :name, :price, :packaging, :category, :image_url)
    ON CONFLICT(id) DO UPDATE SET
        price = excluded.price,
        packaging = excluded.packaging,
        category = excluded.category,
        image_url = excluded.image_url,
        updated_at = CURRENT_TIMESTAMP
    """, products_list)
    
    conn.commit()
    total = cursor.rowcount
    conn.close()
    return total

if __name__ == "__main__":
    init_db()