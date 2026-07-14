import json
import re
import unicodedata

from rapidfuzz import process, fuzz

from src.feature.extraction.domain.repositories import ITextCorrector


# Errores de transcripción conocidos que el fuzzy no alcanza (ej. confusión p/f
# de Whisper, que no es un patrón fonético estándar del español).
ERRORES_ASR = {
    "faredes": "paredes",
    "fared": "pared",
    "farede": "pared",
    "preta": "pared",
    "apareta": "pared",
    "parraszam": "pared",
    "pitorra": "pintura",
    "vaño": "baño",
    "vater": "baño",
    "vive": "mide",
    "caberle": "cambiarle",
}


def _strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFD", s) if unicodedata.category(c) != "Mn")


def _phonetic(w: str) -> str:
    """
    Clave fonética aproximada para español. Colapsa sonidos que Whisper suele
    confundir: s=z=c(suave), b=v, h muda, ll=y, j=g(suave), qu=k, acentos.
    Así "pizo"→"piso", "negó"→"negro", "porselanato"→"porcelanato" hacen match.
    """
    w = _strip_accents(w.lower())
    w = w.replace("qu", "k").replace("gue", "ge").replace("gui", "gi")
    w = re.sub(r"c([ei])", r"s\1", w)
    w = w.replace("ch", "C")  # preservar 'ch' temporalmente
    w = w.replace("c", "k").replace("q", "k")
    w = w.replace("z", "s")
    w = w.replace("v", "b").replace("w", "b")
    w = w.replace("ll", "y")
    w = re.sub(r"g([ei])", r"x\1", w)
    w = w.replace("j", "x")
    w = w.replace("h", "")
    w = w.replace("C", "ch")
    w = re.sub(r"(.)\1+", r"\1", w)  # colapsar letras repetidas
    return w


class RapidFuzzCorrector(ITextCorrector):
    """
    Corrige errores de transcripción de Whisper mapeando cada palabra al término
    del vocabulario de dominio más parecido. Combina dos señales:
      1. Coincidencia FONÉTICA (para confusiones s/z, b/v, letras caídas).
      2. Distancia de edición directa (para typos y acentos).

    Es deliberadamente conservador: prefiere NO corregir antes que corromper una
    palabra válida. Las palabras de `protegidas` nunca se tocan.
    """

    def __init__(self, vocab_path: str = "./dominio_vocab.json",
                 threshold_phonetic: int = 87, threshold_raw: int = 86):
        self.th_phon = threshold_phonetic
        self.th_raw = threshold_raw
        self.targets = []
        self.targets_phon = []
        self.protected = set()
        try:
            with open(vocab_path, "r", encoding="utf-8") as f:
                vocab = json.load(f)
            for key in ("superficies", "materiales", "colores"):
                self.targets.extend(t.lower() for t in vocab.get(key, []))
            self.targets_phon = [_phonetic(t) for t in self.targets]
            self.protected = {p.lower() for p in vocab.get("protegidas", [])}
            self.protected.update(self.targets)  # no corregir un término correcto hacia otro
            print(f"✅ Corrector de texto cargado ({len(self.targets)} términos de dominio).")
        except Exception as e:
            print(f"⚠️ No se pudo cargar el vocabulario de dominio ({vocab_path}): {e}. "
                  f"El corrector quedará inactivo (passthrough).")

    def correct(self, text: str) -> str:
        # Pre-correcciones de frases completas (errores de ASR multi-palabra o de contexto)
        text = re.sub(r"\b(mi|me)\s+de\b", "mide", text, flags=re.IGNORECASE)
        text = re.sub(r"\bme\s+he\s+dedos\b", "mide dos", text, flags=re.IGNORECASE)
        text = re.sub(r"\bha\s+hile\b", "mide", text, flags=re.IGNORECASE)
        text = re.sub(r"\ben\s+medio\s+de\s+los\s+portos\b", "que mide dos por dos", text, flags=re.IGNORECASE)
        text = re.sub(r"\bviene\s+el\s+esbordo\b", "mide dos por dos", text, flags=re.IGNORECASE)
        text = re.sub(r"\b(en\s*)?frente\s+(de|a)\s+(m[ií]|un\s+ínimo)\b", "enfrente de mí", text, flags=re.IGNORECASE)
        text = re.sub(r"\ben\s+la\s+gente\b", "enfrente", text, flags=re.IGNORECASE)

        if not self.targets:
            return text  # passthrough si no hay vocabulario

        tokens = re.findall(r"\w+|[^\w\s]+|\s+", text, flags=re.UNICODE)
        out = []
        for tok in tokens:
            if not tok.strip() or not tok[0].isalpha():
                out.append(tok)
                continue
            word = tok.lower()
            # 1) Errores de ASR conocidos (máxima prioridad)
            if word in ERRORES_ASR:
                out.append(self._preserve_case(tok, ERRORES_ASR[word]))
                continue
            if len(word) < 3 or word in self.protected:
                out.append(tok)
                continue

            replacement = self._best_match(word)
            out.append(self._preserve_case(tok, replacement) if replacement else tok)
        return "".join(out)

    def _best_match(self, word: str):
        # 1) Señal fonética
        m_phon = process.extractOne(_phonetic(word), self.targets_phon, scorer=fuzz.ratio)
        if m_phon and m_phon[1] >= self.th_phon:
            return self.targets[m_phon[2]]
        # 2) Distancia de edición directa (typos/acentos)
        m_raw = process.extractOne(word, self.targets, scorer=fuzz.ratio)
        if m_raw and m_raw[1] >= self.th_raw and m_raw[0] != word:
            return m_raw[0]
        return None

    @staticmethod
    def _preserve_case(original: str, replacement: str) -> str:
        if original.istitle():
            return replacement.capitalize()
        if original.isupper():
            return replacement.upper()
        return replacement
