# 🤖 TecnoAIgent: Asistente de IA con conexión a SAP


La solución consiste en un agente conversacional conectado directamente a SAP HANA, capaz de:

- Interpretar preguntas en lenguaje natural y traducirlas automáticamente a consultas SQL sobre las vistas comerciales y operativas.
- Entregar información actualizada de ventas, producción, despachos y facturación sin depender de reportes tradicionales ni procesos manuales de extracción o filtrado.
- Presentar resultados de manera clara, explicando los datos y sus implicancias de forma comprensible para usuarios de negocio.

# Requisitos Previos

Antes de ejecutar la solución, asegúrate de cumplir con los siguientes requisitos:

1. Registrar la IP de acceso en SAP HANA Cloud (SAP Datasphere)  
Ingresa a la plataforma de administración de SAP HANA Cloud o SAP Datasphere y registra la dirección IP pública del servidor o PC desde donde se realizará la conexión ODBC.
Esto es necesario para que el firewall permita el acceso a la base de datos desde tu equipo.

2. Instalar SAP HANA Client
Descarga e instala el SAP HANA Client. Durante la instalación, selecciona el componente ODBC Driver.

3. Configurar la conexión ODBC
   - Abre el Administrador de Orígenes de Datos ODBC de tu sistema operativo.
   - Crea una nueva conexión (DSN) usando el driver de SAP HANA.
   - Completa los siguientes datos:
                        - Host
                        - Puerto
                        - Usuario
                        - Contraseña

   - Prueba la conexión para asegurarte de que funciona correctamente.

4. Credenciales de acceso
Asegúrate de tener un usuario habilitado y con los permisos necesarios para consultar las vistas analíticas en SAP HANA.

# Arquitectura de solución

![Arquitectura de Agente SQL SAP](Arquitectura_AgentSQL_SAP.gif)

El flujo de la solución es el siguiente:

 1.Inicio de sesión seguro
El usuario accede a la plataforma web desplegada en Vercel autenticándose con su cuenta de Google (Gmail).

 2.Selección de vista analítica
En el frontend, el usuario selecciona la vista analítica con la que desea interactuar (por ejemplo, Detalles de Pedidos o Ventas Comerciales) mediante un menú desplegable.

 3.Comunicación con backend empresarial
El frontend realiza una petición GET a la ruta /agent, la cual es gestionada por un servidor Microsoft IIS que hospeda la API desarrollada en Flask. Esta API integra LangChain para la gestión conversacional y orquestación de flujos.

 4.Acceso a datos empresariales y memoria contextual
El agente procesa la solicitud y consulta:.

- SAP HANA Cloud para acceder al conocimiento empresarial en tiempo real (vistas analíticas).
- PostgreSQL para gestionar la memoria conversacional y contexto del usuario.

 5.Generación y trazabilidad de respuestas
El modelo GPT‑4.1 de OpenAI interpreta la pregunta, genera la consulta SQL, analiza los datos obtenidos y produce la respuesta final. Toda la interacción es trazada con LangSmith para auditoría y mejora continua.

 6.Entrega de resultados claros y explicativos
La respuesta generada es devuelta al usuario en el frontend, presentando los datos solicitados junto con explicaciones claras, facilitando la toma de decisiones para los usuarios de negocio.
