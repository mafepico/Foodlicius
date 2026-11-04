import httpx
import sqlite3
import time

DB_NAME = "foodlicius.db"
POSTAL_CODE = "46001"
BASE_URL = f"https://tienda.mercadona.es/api/categories/?postal_code={POSTAL_CODE}"

def sync():
    print(" Conectando a la API de Mercadona...")
    with httpx.Client(timeout=30.0) as client:
        res = client.get(BASE_URL)
        if res.status_code != 200:
            print(f"❌ Error al consultar categorías principales: {res.status_code}")
            return
        
        root_data = res.json()
        categories = root_data.get("results", [])
        print(f" Encontradas {len(categories)} secciones raíz.")

        # Recolectar todos los IDs de subcategorías con productos
        subcat_ids = []
        for cat in categories:
            for sub in cat.get("categories", []):
                subcat_ids.append((sub.get("id"), f"{cat.get('name')} > {sub.get('name')}"))

        print(f" Total subcategorías a descargar: {len(subcat_ids)}")
        products_dict = {}

        for index, (sub_id, cat_path) in enumerate(subcat_ids, start=1):
            url = f"https://tienda.mercadona.es/api/categories/{sub_id}/?postal_code={POSTAL_CODE}"
            try:
                sub_res = client.get(url)
                if sub_res.status_code != 200:
                    continue
                
                sub_data = sub_res.json()
                for leaf in sub_data.get("categories", []):
                    for prod in leaf.get("products", []):
                        pid = str(prod.get("id"))
                        price_info = prod.get("price_instructions", {})
                        unit_price = price_info.get("unit_price")
                        
                        if pid and unit_price is not None:
                            products_dict[pid] = (
                                pid,
                                prod.get("display_name", ""),
                                float(unit_price),
                                price_info.get("reference_format", ""),
                                cat_path,
                                prod.get("thumbnail", "")
                            )
                print(f" [{index}/{len(subcat_ids)}] Sincronizada: {cat_path} (Acumulados: {len(products_dict)})")
                time.sleep(0.05)  # Breve pausa para no saturar la red
            except Exception as e:
                print(f"⚠️ Error en subcategoría {sub_id}: {e}")
                continue

    # Guardar en SQLite
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.executemany("""
    INSERT INTO products (id, name, price, packaging, category, image_url)
    VALUES (?, ?, ?, ?, ?, ?)
    ON CONFLICT(id) DO UPDATE SET
        price = excluded.price,
        packaging = excluded.packaging,
        category = excluded.category,
        image_url = excluded.image_url,
        updated_at = CURRENT_TIMESTAMP
    """, list(products_dict.values()))

    conn.commit()
    conn.close()
    print(f"\n ¡Catálogo completo actualizado con éxito! Total guardados: {len(products_dict)}")

if __name__ == "__main__":
    sync()