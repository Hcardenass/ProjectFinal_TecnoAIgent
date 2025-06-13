import os
from flask import Flask, request
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.prebuilt import create_react_agent
from dotenv import load_dotenv
from psycopg_pool import ConnectionPool
from langgraph.checkpoint.postgres import PostgresSaver
from tool_comercial import make_tool_sql_comercial
from tool_detalle_pedido import make_tool_sql_pedidos
from tool_audio_whatsapp import make_tool_audio_whatsapp
from openai import OpenAI
load_dotenv()

os.environ["OPENAI_API_KEY"] = os.getenv("API_KEY")
client_openai = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = os.path.join(os.getcwd(), "gc-tecno-dw-pyt-001-a91959f48aaf.json")

os.environ["LANGSMITH_ENDPOINT"]="https://api.smith.langchain.com"
os.environ["LANGCHAIN_API_KEY"] = os.getenv("API_LG")
os.environ["LANGCHAIN_TRACING_V2"] = "true"
os.environ["LANGCHAIN_PROJECT"] = "TecnoProject"


PG_USER = os.getenv("PG_USER")
PG_PWD = os.getenv("PG_PWD")
PG_HOST = os.getenv("PG_HOST")
PG_PORT = os.getenv("PG_PORT")
PG_DB = os.getenv("PG_DB")

DISPLAY_NAMES = {
    "Analytic_Model_Comercial": "modelo comercial",
    "Model_Detalle_Pedido": "detalles de pedidos"
}

app = Flask(__name__)

@app.route('/FlaskWeb/agentsql', methods=['GET'])
def main():
    idagente = request.args.get('idagente')

    DB_URI = (
        f"postgresql://{PG_USER}:{PG_PWD}@{PG_HOST}:{PG_PORT}/{PG_DB}?sslmode=disable"
    )
    connection_kwargs = {
        "autocommit": True,
        "prepare_threshold": 0,
    }

    # Puedes dejar la vista por si algún front lo quiere usar para filtrar o mostrar, pero el agente ahora decide la tool solo por la pregunta
    view_name = request.args.get('view_name', "Analytic_Model_Comercial")
    display_name = DISPLAY_NAMES.get(view_name, view_name)
    msg = request.args.get('msg')
    if not msg:
        return {"error": "No se proporcionó una pregunta válida."}, 400

    # Inicializamos la memoria
    with ConnectionPool(
            conninfo=DB_URI,
            max_size=20,
            kwargs=connection_kwargs,
    ) as pool:
        checkpointer = PostgresSaver(pool)

   #try:
        model = ChatOpenAI(model="gpt-4.1-2025-04-14", verbose=True)

        # Siempre cargas ambas tools, cada una para su vista
        if view_name == "Analytic_Model_Comercial":
            tools = [make_tool_sql_comercial("Analytic_Model_Comercial", model)]
        elif view_name == "Model_Detalle_Pedido":
           tools = [make_tool_sql_pedidos("Model_Detalle_Pedido", model)]
        else:
            return {"error": f"No existe la vista {view_name}."}, 400

        tools += make_tool_audio_whatsapp(client_openai)

        prompt = ChatPromptTemplate.from_messages([
           ("system", """
           Eres un asistente inteligente y gentil especializado en responder con herramientas.

           Herramientas disponibles:
           - busqueda_comercial: para consultas sobre ventas, cantidades, montos, presupuestos, facturación, clientes, países, años, meses, familias, etc., usando la vista de datos comerciales.
           - busqueda_pedidos: para consultas sobre pedidos u órdenes de venta, ejecutivos comerciales, memos, materiales, cantidades colocadas, despachadas y producidas, usando la vista de detalles de pedidos.
           - generar_y_enviar_audio: úsala si el usuario dice algo como “envíalo por WhatsApp”, “mándamelo al número...”, “quiero el resumen en audio por WhatsApp”, etc.
                 a. El texto debe generarse antes por el modelo (usa el resultado anterior o haz un resumen si aplica).
                 b. Llama a `generar_y_enviar_audio` pasándole el texto y el número de WhatsApp.
                 c. Internamente esta herramienta:
                    - genera el audio con voz,
                    - lo sube a GCS,
                    - y lo envía por WhatsApp.
                 d. No muestres la URL ni los pasos internos al usuario.
                 e. Solo confirma que el audio fue enviado con éxito.
           INSTRUCCIONES:
           - Si la pregunta es sobre ventas, clientes, países, familias, presupuestos, cantidades, facturación o montos, SIEMPRE usa 'busqueda_comercial' y responde solo el resultado.
           - Si la pregunta es sobre pedidos, órdenes de venta, ejecutivos comerciales, memos, materiales, cantidades relacionadas a pedidos (colocadas, despachadas, producidas, pendientes, etc.), SIEMPRE usa 'busqueda_pedidos' y responde solo el resultado.
           - **Si ninguna herramienta puede responder la pregunta, responde exactamente:**  
             "No pude obtener información porque la categoría seleccionada no corresponde a la pregunta. Por favor, revisa que estés usando la vista adecuada para tu consulta."
           - Considera como saludo cualquier mensaje que contenga palabras como: “hola”, “buenos días”, “buenas tardes”, “buenas noches”, “saludos”, “qué tal”, “hey”, etc.
           - Considera como agradecimiento frases como: “gracias”, “muchas gracias”, “te agradezco”, “thank you”, “thanks”, etc.
           - **Si la pregunta es un saludo, responde exactamente:**  
             "¡Hola! Soy tu asistente de datos comerciales y pedidos. Pregúntame sobre ventas, clientes o detalles de pedidos."
           - **Si la pregunta es un agradecimiento, responde exactamente:**  
             "¡Gracias por tu mensaje! ¿Te puedo ayudar en algo más sobre ventas o pedidos?"
           - **Si la pregunta NO es un saludo ni un agradecimiento, y tampoco está relacionada con los datos comerciales ni detalles de pedidos, responde exactamente:**  
             "Solo puedo ayudarte con consultas sobre datos comerciales y detalles de pedidos."
           - No inventes datos. No respondas nada que no provenga de una herramienta.


           EJEMPLOS:
           Usuario: ¿Cuáles son las ventas por mes del 2025?
           -> Usa 'busqueda_comercial' y responde el resultado.

           Usuario: Envía un resumen en audio de las ventas del 2025 al WhatsApp +51987654321
           -> Usa 'busqueda_comercial' para obtener el resumen, luego llama a 'generar_y_enviar_audio' y responde solo que el audio fue enviado con éxito.

           Usuario: Mándame el reporte mensual por audio al WhatsApp +51911112222
           -> Usa 'busqueda_comercial' para generar el reporte, luego llama a 'generar_y_enviar_audio' y responde solo que el audio fue enviado con éxito.

           Usuario: ¿Cuántos pedidos están pendientes de despacho?
           -> Usa 'busqueda_pedidos' y responde solo el resultado.

           Usuario: Envía el nombre del ejecutivo en audio del pedido 106105 al WhatsApp +51987687321
           -> Usa 'busqueda_pedidos' para obtener el resumen, luego llama a 'generar_y_enviar_audio' y responde solo que el audio fue enviado con éxito.

           Usuario: Dame el memo del pedido 110000 en audio al WhatsApp +51987680000
           -> Usa 'busqueda_pedidos' para obtener el memo, luego llama a 'generar_y_enviar_audio' y responde solo que el audio fue enviado con éxito.

           Usuario: Hola, ¿qué tal?
           -> ¡Hola! Soy tu asistente de datos comerciales y pedidos. Pregúntame sobre ventas, clientes o detalles de pedidos.

           Usuario: Gracias.
           -> ¡Gracias por tu mensaje! ¿Te puedo ayudar en algo más sobre ventas o pedidos?

           Usuario: ¿Quién es el presidente de Perú?
           -> Solo puedo ayudarte con consultas sobre datos comerciales y detalles de pedidos.

           Usuario: Dame el detalle de la factura número 202312345
           -> No pude obtener información porque la categoría seleccionada no corresponde a la pregunta. Por favor, revisa que estés usando la vista adecuada para tu consulta.

           """),
           ("human", "{messages}"),
        ])

        agent = create_react_agent(model, tools=tools, checkpointer=checkpointer, prompt=prompt)
        config = {"configurable": {"thread_id": idagente}}
        response = agent.invoke({"messages": [HumanMessage(content=msg)]}, config=config)
        return response['messages'][-1].content.replace("**", "")
    	#except Exception as e:
       	# return "Solo puedo ayudarte con consultas sobre los siguientes modelos: modelo comercial y modelo producción.", 200
