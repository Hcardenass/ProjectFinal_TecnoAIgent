import re
from field_descriptions import field_descriptions
from field_descriptions_pedidos import field_descriptions_pedidos
from sqlalchemy import create_engine, inspect
from langchain_community.utilities.sql_database import SQLDatabase
from urllib.parse import quote_plus
import os
from dotenv import load_dotenv

load_dotenv()

def build_uribd():
    user      = os.getenv("HANA_USER")
    pwd       = os.getenv("HANA_PWD")
    host      = os.getenv("HANA_HOST")
    port      = os.getenv("HANA_PORT")
    schema    = os.getenv("HANA_SCHEMA")
    user_enc = quote_plus(user)
    pwd_enc = quote_plus(pwd)
    return f"hana+hdbcli://{user_enc}:{pwd_enc}@{host}:{port}/?currentSchema={schema}", schema

def get_schema(vs) -> str:
    uribd, schema = build_uribd()
    from sqlalchemy import create_engine, inspect
    engine = create_engine(uribd)
    inspector = inspect(engine)
    if isinstance(vs, dict) and "view_name" in vs:
        view = vs["view_name"]
    elif isinstance(vs, dict):
        view = vs.get("view_name", "Analytic_Model_Comercial")
    else:
        view = str(vs)

    try:
        cols = inspector.get_columns(view, schema=schema)
        lines = []
        for c in cols:
            name_columns = c["name"].upper()
            description_columns = field_descriptions.get(name_columns, "Descripción no disponible")
            lines.append(f"- {name_columns}: {description_columns}")
        return "\n".join(lines)
    except Exception:
        return f"Error: No se pudo obtener el esquema de la vista {view}"

def run_query(query: str):
    uribd, _ = build_uribd()
    db_data = SQLDatabase.from_uri(uribd)
    query = re.sub(r'^```(?:sql)?\s*', '', query, flags=re.IGNORECASE)
    query = re.sub(r'```$', '', query)
    query = re.sub(r'^"""{0,1}sql\s*', '', query, flags=re.IGNORECASE)
    query = re.sub(r'"""$', '', query)
    query = query.replace("`", '"')
    clean_sql = query.strip()
    return db_data.run(clean_sql)

def get_field_desc(vs):
    if isinstance(vs, dict) and "view_name" in vs:
        view = vs["view_name"]
    elif isinstance(vs, dict):
        view = vs.get("view_name", "Analytic_Model_Comercial")
    else:
        view = str(vs)

    # Asume nombres consistentes
    if view in ["Analytic_Model_Comercial"]:
        descriptions = field_descriptions
    elif view in ["Model_Detalle_Pedido"]:
        descriptions = field_descriptions_pedidos
    else:
        # Default a comercial si no reconoce la vista
        descriptions = field_descriptions

    lines = []
    for col, desc in descriptions.items():
        lines.append(f"- {col}: {desc}")
    return "\n".join(lines)
