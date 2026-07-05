import re
from typing import List, Tuple

from src.feature.extraction.domain.entities import Dimensiones
from src.feature.extraction.domain.repositories import IDimensionExtractor

# Números en dígitos (1, 3.5, 3,5) o palabras comunes.
PALABRAS_NUM = {
    "un": 1, "uno": 1, "una": 1, "dos": 2, "tres": 3, "cuatro": 4, "cinco": 5,
    "seis": 6, "siete": 7, "ocho": 8, "nueve": 9, "diez": 10, "once": 11,
    "doce": 12, "quince": 15, "veinte": 20,
}
NUM = (r"(\d+(?:[.,]\d+)?|un[oa]?|dos|tres|cuatro|cinco|seis|siete|ocho|nueve|"
       r"diez|once|doce|quince|veinte)")

# Señales fuertes de que un "N por M" describe el tamaño de la PIEZA, no del área.
PIEZA_KW_FUERTE = ("mide", "miden", "pieza", "piezas", "tamaño", "tamano",
                   "medida", "medidas")

RE_AREA = re.compile(NUM + r"\s*(?:metros?|mts?|m)\s*(?:cuadrados?|²|2\b)")
RE_LADO = re.compile(NUM + r"\s*(?:metros?|mts?|m)?\s*de\s*(largo|ancho|alto)")
# Tolera unidad ("metros") y coma/punto entre el número y el conector.
# Ej: "2 metros, por 2 metros", "2 m x 2 m", "4 metros por 5 metros".
RE_PAR = re.compile(NUM + r"\s*(?:metros?|mts?|m)?\s*[,.]?\s*(?:x|×|por|\*)\s*" + NUM)


def _num(s: str) -> float:
    s = s.strip().lower()
    if s in PALABRAS_NUM:
        return float(PALABRAS_NUM[s])
    return float(s.replace(",", "."))


class RegexDimensionParser(IDimensionExtractor):
    """
    Extrae medidas del texto por reglas/regex (más fiable que NER para números).
    Distingue el área a cubrir del tamaño de la pieza (loseta) según el contexto.
    No hace cálculos de negocio: solo normaliza a metros.
    """

    def extract(self, text: str) -> Tuple[Dimensiones, List[str]]:
        t = " " + text.lower() + " "
        dim = Dimensiones()
        crudo: List[str] = []

        # 1. Área explícita: "N metros cuadrados", "N m2", "N m²"
        m = RE_AREA.search(t)
        if m:
            dim.area_m2 = _num(m.group(1))
            crudo.append(m.group(0).strip())

        # 2. Lados etiquetados: "N de largo/ancho/alto"
        for m in RE_LADO.finditer(t):
            lado = {"largo": "largo_m", "ancho": "ancho_m", "alto": "alto_m"}[m.group(2)]
            setattr(dim, lado, _num(m.group(1)))
            crudo.append(m.group(0).strip())

        # 3. Pares "N por M" / "N x M" → pieza o área según contexto y tamaño
        for m in RE_PAR.finditer(t):
            a, b = _num(m.group(1)), _num(m.group(2))
            ctx = t[max(0, m.start() - 25):m.start()]
            es_fuerte = any(k in ctx for k in PIEZA_KW_FUERTE)
            # Piezas típicas son pequeñas (<=1.2 m) y hay un área mayor ya detectada.
            es_chico = a <= 1.2 and b <= 1.2 and dim.area_m2 is not None and dim.area_m2 > a * b
            if es_fuerte or es_chico:
                dim.pieza_largo_m, dim.pieza_ancho_m = a, b
            else:
                if dim.largo_m is None:
                    dim.largo_m = a
                if dim.ancho_m is None:
                    dim.ancho_m = b
            crudo.append(m.group(0).strip())

        # 4. Si no se dijo el área pero sí largo y ancho → calcularla
        if dim.area_m2 is None and dim.largo_m and dim.ancho_m:
            dim.area_m2 = round(dim.largo_m * dim.ancho_m, 2)

        return dim, crudo
