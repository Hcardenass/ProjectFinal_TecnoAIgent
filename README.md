# 🤖 TecnoAIgent: Asistente de IA con conexión a SAP


La solución consiste en un agente conversacional conectado directamente a SAP HANA, capaz de:

- Interpretar preguntas en lenguaje natural y traducirlas automáticamente a consultas SQL sobre las vistas comerciales y operativas.
- Entregar información actualizada de ventas, producción, despachos y facturación sin depender de reportes tradicionales ni procesos manuales de extracción o filtrado.
- Presentar resultados de manera clara, explicando los datos y sus implicancias de forma comprensible para usuarios de negocio.

# Requisitos Previos

Antes de ejecutar la solución, asegúrate de cumplir con los siguientes requisitos:

1.Registrar la IP de acceso en SAP HANA Cloud (SAP Datasphere)
Ingresa a la plataforma de administración de SAP HANA Cloud o SAP Datasphere y registra la dirección IP pública del servidor o PC desde donde se realizará la conexión ODBC.
Esto es necesario para que el firewall permita el acceso a la base de datos desde tu equipo.

2.Instalar SAP HANA Client
Descarga e instala el SAP HANA Client. Durante la instalación, selecciona el componente ODBC Driver.

3.Configurar la conexión ODBC
-Abre el Administrador de Orígenes de Datos ODBC de tu sistema operativo.
-Crea una nueva conexión (DSN) usando el driver de SAP HANA.
-Completa los siguientes datos:
            -Host
            -Puerto
            -Usuario
            -Contraseña

-Prueba la conexión para asegurarte de que funciona correctamente.

4.Credenciales de acceso
Asegúrate de tener un usuario habilitado y con los permisos necesarios para consultar las vistas analíticas en SAP HANA.

## 2. Arquitectura de solución

![Arquitectura de Agente SQL SAP](Arquitectura_AgentSQL_SAP.gif)
