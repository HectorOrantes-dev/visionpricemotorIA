import re
import unicodedata
from typing import List, Optional

from src.feature.extraction.domain.repositories import ICategoryClassifier

# Materiales que mapean directo a una categoría del catálogo de proveedores,
# sin importar en qué superficie estén.
CATEGORIA_DIRECTA = {
    "azulejo": "azulejo", "azulejos": "azulejo",
    "zoclo": "zoclo", "zoclos": "zoclo",
    "pegazulejo": "pegazulejo", "adhesivo": "pegazulejo",
    "cruceta": "cruceta", "crucetas": "cruceta",
    "boquilla": "boquilla",
    "pintura": "pintura",
    "impermeabilizante": "impermeabilizante",
    "sellador": "sellador",
    "cemento": "cemento",
    "mortero": "mortero",
    "yeso": "yeso",
    "tabique": "tabique",
    "block": "block",
    "grava": "grava",
    "arena": "arena",
}

# Materiales tipo "pieza" (loseta, porcelanato...): la categoría depende de si
# van en piso o en pared ("azulejo" en pared, "piso" en suelo).
MATERIALES_PIEZA = {
    "loseta", "losetas", "porcelanato", "ceramico", "ceramica",
    "mosaico", "mosaicos", "baldosa", "baldosas", "talavera", "tableta",
}

SURFACE_PISO = {"piso", "pisos", "suelo", "contrapiso", "loza"}
SURFACE_PARED = {"pared", "paredes", "muro", "muros", "fachada"}
SURFACE_TECHO = {"techo", "techos", "plafon"}

# El modelo BETO NO tiene una etiqueta de "acción/verbo" (solo COLOR, MATERIAL,
# SUPERFICIE, UBICACION). Si el usuario dice "pintar la pared" sin mencionar la
# palabra "pintura", BETO no detecta ningún MATERIAL. Estas regex son un
# respaldo determinístico para no perder la categoría en ese caso.
VERBOS_ACCION = (
    (re.compile(r"\bpintar\b"), "pintura"),
    (re.compile(r"\bimpermeabilizar\b"), "impermeabilizante"),
)


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _norm(s: Optional[str]) -> str:
    return _strip_accents(s.lower()) if s else ""


class KeywordCategoryClassifier(ICategoryClassifier):
    """
    Deriva la categoría de producto (piso, azulejo, zoclo, pegazulejo, cruceta,
    boquilla, pintura...) a partir del material y la superficie ya detectados
    por BETO, con un respaldo por verbo de acción para cuando BETO no marcó
    ningún material (ver VERBOS_ACCION). No hace NER propio: solo aplica reglas
    sobre las etiquetas y, como último recurso, sobre el texto crudo.
    """

    def classify(self, tipo_superficie: Optional[str], materiales: List[str], texto: str = "") -> Optional[str]:
        materiales_norm = [_norm(m) for m in materiales]

        # 1. Materiales que ya identifican su propia categoría (zoclo, pintura...).
        for m in materiales_norm:
            if m in CATEGORIA_DIRECTA:
                return CATEGORIA_DIRECTA[m]

        ts = _norm(tipo_superficie)

        # 2. Piezas (loseta/porcelanato/...) según en qué superficie van.
        if any(m in MATERIALES_PIEZA for m in materiales_norm):
            if ts in SURFACE_PARED:
                return "azulejo"
            return "piso"

        # 3. Sin material detectado por BETO: buscar el verbo de acción en el
        #    texto crudo antes de caer al default por superficie ("pintar la
        #    pared" debe dar "pintura", no "azulejo" solo por ser una pared).
        texto_norm = _norm(texto)
        for patron, categoria in VERBOS_ACCION:
            if patron.search(texto_norm):
                return categoria

        # 4. Sin material ni verbo de acción: usar la superficie como default.
        if ts in SURFACE_PISO:
            return "piso"
        if ts in SURFACE_PARED:
            return "azulejo"
        if ts in SURFACE_TECHO:
            return "techo"

        return None
