from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough
from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from utils import get_schema, run_query, get_field_desc

def make_tool_sql_comercial(view_name,model):
    schema_data = get_schema({"view_name": view_name})
    field_desc = get_field_desc({"view_name": view_name})

    promptsql = ChatPromptTemplate.from_template("""
    Actúa como un experto en SQL para SAP HANA especializado en la vista **Analytic_Model_Comercial**. 
    Solo responde a preguntas relacionadas con:
    - ventas,
    - cantidades,
    - montos,
    - presupuestos,
    - facturación,
    - clientes,
    - países,
    - años,
    - meses,
    - familias,
    - cualquier otra consulta puramente comercial.
    
    **IMPORTANTE:**  
    - Si la pregunta es sobre pedidos, órdenes de venta, ejecutivos comerciales, memos, materiales, cantidades colocadas/despachadas/producidas/pedidos pendientes, o cualquier tema que NO sea estrictamente comercial, responde exactamente:
      "La pregunta no corresponde a la categoría comercial. Por favor, consulta solo sobre ventas, presupuestos, facturación, clientes, familias, etc."
    - No inventes equivalencias entre “pedidos” y campos comerciales. Si la pregunta es sobre pedidos, **no intentes responderla**.
    
    A continuación tienes:
    - **Vista**: {view_name}
    - **Esquema de columnas**: {view_schema}
    - **Descripción de campos**: {field_desc}
    - **Pregunta**: {question}
    
    
    **Instrucciones**:
    1. Si la pregunta es relevante, genera solo el SQL necesario. Si no, responde el mensaje de advertencia anterior.
    2. Usa SOLO los nombres de campos especificados en la descripción de campos ({field_desc}). No inventes nombres de campos basándote en la pregunta.
    3. El campo "UDM" indica el tipo de registro:
        - 'CF': Cantidad colocada
        - 'Fact.': Cantidad facturada
        - 'Ppto': Cantidad presupuestada
    4. Si la pregunta menciona “colocado” (o similar), usa el campo "CANTI" y filtra por "UDM" = 'CF'.
    5. Si menciona “facturado” (o similar, como “cantidad facturada”), usa el campo "CANTI" y filtra por "UDM" = 'Fact.'.
    6. Si menciona “presupuesto” (o similar), usa el campo "CANTI" y filtra por "UDM" = 'Ppto'.
    7. Si la pregunta menciona “ventas en dólares” (o "monto de ventas", "ventas en USD", etc.), calcula el monto total como SUM("PREMIO" * "CANTI") con "UDM" = 'CF' y expresa el resultado en dólares.
    8. Si la pregunta menciona “ventas en toneladas” (o "toneladas vendidas", "cantidad vendida en toneladas", etc.), calcula el total solo como SUM("CANTI") con "UDM" = 'CF' y expresa el resultado en toneladas métricas. NO multipliques por "PREMIO".
    9. Si la pregunta solicita un detalle por mes, por año, por cliente, por familia, o por país, agrega una cláusula GROUP BY solo para los campos que se mencionan explícitamente en la pregunta.
        - Ejemplo: Si la pregunta es “por país”, agrupa solo por "PAIS". Si es “por mes”, agrupa solo por "MES" y "AÑO".
        - No agregues otros campos de agrupación a menos que la pregunta los mencione claramente.
    10. Si la pregunta menciona solo “ventas” y NO especifica si es en dólares o toneladas, devuelve ambos resultados: 
        - Suma de "CANTI" (toneladas)
        - Suma de "PREMIO" * "CANTI" (dólares)
        Incluye ambos valores en el SELECT y, si hay agrupamiento (por ejemplo, por mes), aplica el GROUP BY correspondiente.
    11. Para comparaciones entre tipos (por ejemplo, “presupuesto vs facturado”), usa WHERE "UDM" IN (...).
    12. NO agrupes por "CLIENTE", "FAMILIA" u otros campos a menos que la pregunta lo pida explícitamente.
    13. Usa comillas dobles (") para esquemas, tablas y columnas.
    14. Normaliza texto con UPPER() en condiciones de búsqueda (por ejemplo, UPPER("CLIENTE") = 'ACME').
    15. Devuelve solo la consulta SQL, sin punto y coma ni texto adicional.
    16. Si la pregunta menciona un cliente y el nombre no es exactamente igual al de la base de datos, utiliza una condición con LIKE e ignora mayúsculas/minúsculas, por ejemplo: UPPER("CLIENTE") LIKE '%[nombre_cliente]%'
    17. Si la consulta es sobre ventas agrupadas por meses y años, **usa el campo "ESTATUS_MES"** para diferenciar el estado de cada mes y asegúrate de que esté presente en los resultados.
    """)

    sql_chain = (
        RunnablePassthrough.assign(
            view_name=lambda _: view_name,
            view_schema=lambda _: schema_data,
            field_desc=lambda _: field_desc
        )
        | promptsql
        | model.bind(stop=["\nSQLResult:"])
        | StrOutputParser()
    )

    promptnl = ChatPromptTemplate.from_template("""
    Explica los resultados de la siguiente consulta SQL en lenguaje natural, de forma detallada y ordenada:
    - **Pregunta**: {question}
    - **Resultados**: {response}
    - **Lista de campos y descripciones**: {field_desc}

    **Instrucciones**:  
    - Para cada mes, utiliza el campo "ESTATUS_MES" para guiar la explicación, pero **NUNCA muestres ni la palabra 'estatus' ni el valor literal del campo** ("REALIZADO", "EN VENTA", "POR VENDER").
    - Si "ESTATUS_MES" es "REALIZADO", indica que las ventas ya han sido realizadas y concretadas en ese mes.
    - Si "ESTATUS_MES" es "EN VENTA", indica que corresponde al mes actual, y las ventas pueden estar en proceso o en curso.
    - Si "ESTATUS_MES" es "POR VENDER", indica que la cantidad corresponde a ventas programadas o pedidos aún no concretados.
    - Nunca pongas “estatus:”, ni pongas el valor entre paréntesis ni en mayúsculas.
    - No interpretes ni asumas el estatus; SIEMPRE guía la explicación según el valor de "ESTATUS_MES" que viene en los datos.
    - Expresa las cantidades SIEMPRE en toneladas métricas (TM) y los montos en dólares (USD).
    - Si la pregunta es de “ventas en toneladas” (o similares), expresa el resultado en toneladas métricas y no lo confundas con monto en dólares.
    - Si la pregunta es de “ventas en dólares” (o similares), explica que es el monto total (PREMIO * CANTI) y expresa el resultado en dólares.
    - Si la respuesta muestra ambos valores (cantidad y monto), indica claramente que la cantidad es en toneladas métricas y el monto en dólares.
    - Proporciona solo el dato solicitado con una contextualización mínima, sin mencionar la vista, el SQL generado, ni el valor de UDM (como 'CF', 'Fact.', o 'Ppto').
    - Evita detalles técnicos o explicaciones innecesarias.
    """)

    full_chain = (
        RunnablePassthrough.assign(query=sql_chain)
        .assign(
            response=lambda vs: run_query(vs["query"]),  # Ejecuta SQL
            view_name=lambda _: view_name,
            view_schema=lambda _: schema_data,
            field_desc=lambda _: field_desc
        )
        | promptnl
        | model
    )


    return full_chain.as_tool(
        name="busqueda_comercial",
        description=(
            f"Genera y ejecuta consultas SQL sobre la vista {view_name}, "
            "usando su esquema y descripciones de campos, "
            "y explica los resultados en lenguaje natural de forma detallada."
        )
    )
