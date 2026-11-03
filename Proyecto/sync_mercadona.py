import httpx
import time
from database import init_db, save_products

def sincronizar_catalogo(codigo_postal="46001", limite_categorias=5):
    # 1. Asegurar que la tabla existe
    init_db()
    
    url_base = "https://tienda.mercadona.es/api/categories/"
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "Accept": "application/json",
    }
    
    print(f" Iniciando descarga del catálogo (CP: {codigo_postal})...")
    
    with httpx.Client(headers=headers, timeout=20.0) as client:
        # Obtener las categorías principales
        resp = client.get(f"{url_base}?postal_code={codigo_postal}")
        resp.raise_for_status()
        categorias_principales = resp.json().get("results", [])
        
        productos_totales = []
        contador = 0
        
        for cat in categorias_principales:
            nombre_cat_padre = cat.get("name")
            
            for sub in cat.get("categories", []):
                sub_id = sub.get("id")
                sub_nombre = sub.get("name")
                
                print(f"⏳ Descargando: {nombre_cat_padre} -> {sub_nombre}...")
                
                try:
                    url_sub = f"{url_base}{sub_id}/?postal_code={codigo_postal}"
                    sub_resp = client.get(url_sub)
                    sub_resp.raise_for_status()
                    sub_data = sub_resp.json()
                    
                    # Recorrer productos dentro de la subcategoría
                    for grupo in sub_data.get("categories", [sub_data]):
                        for prod in grupo.get("products", []):
                            precio_info = prod.get("price_instructions", {})
                            unit_price = precio_info.get("unit_price")
                            
                            if unit_price is not None:
                                productos_totales.append({
                                    "id": str(prod.get("id")),
                                    "name": prod.get("display_name"),
                                    "price": float(unit_price),
                                    "packaging": prod.get("packaging") or "ud",
                                    "category": f"{nombre_cat_padre} / {sub_nombre}",
                                    "image_url": prod.get("thumbnail")
                                })
                except Exception as e:
                    print(f" Error en subcategoría {sub_id}: {e}")
                
                # Pausa de cortesía para no saturar los servidores de Mercadona
                time.sleep(0.5)
            
            contador += 1
            # Límite inicial de categorías principales para que no tarde 15 minutos en la primera prueba
            if contador >= limite_categorias:
                break
        
        # Guardar en SQLite
        if productos_totales:
            save_products(productos_totales)
            print(f"\n ¡Completado! Se guardaron {len(productos_totales)} productos en la base de datos.")

if __name__ == "__main__":
    sincronizar_catalogo(limite_categorias=3)