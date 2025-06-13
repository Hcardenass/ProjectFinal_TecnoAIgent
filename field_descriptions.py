# Definición de descripciones de campos para la vista
field_descriptions = {
    "AÑO": "Año en que se realizó el Pedido de Venta u Orden de Venta.",
    "MES": "Mes en que se realizó el Pedido de Venta u Orden de Venta, expresado como número (1 a 12, sin ceros a la izquierda).",
    "FAMILIA": "Categoría o grupo al que pertenece el material a producir.",
    "CLIENTE": "Nombre o identificador del cliente que realizó el pedido",
    "UDM": "Código que indica el tipo de registro: CF = Colocado, Fact. = Facturado, Ppto = Presupuesto.",
    "CANTI": "Cantidad del registro (depende de UDM: colocada, facturada o presupuesto), expresada SIEMPRE en toneladas métricas (TM).",
    "PREMIO": "Precio en dolares($) de la tonelada métrica.",
    "PAIS": "País de destino asociado al pedido u orden de venta.",
    "GEOGRAFIA": "Zona geográfica o region comercial asignada al cliente o al pedido.",
    "ESTATUS_MES": "Estatus del mes respecto a la fecha actual: 'REALIZADO' para meses ya concluidos, 'EN VENTA' para el mes en curso y 'POR VENDER' para meses futuros aún no alcanzados."
}