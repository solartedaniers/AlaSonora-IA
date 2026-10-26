import os
import sys
import tempfile
import types
from datetime import datetime

import ai_edge_litert.interpreter as litert_interpreter
import librosa
import numpy as np
import soundfile as sf

# Registro LiteRT como "tflite_runtime" antes de importar birdnetlib; si no, carga TensorFlow completo (~180 MB más).
sys.modules.setdefault("tflite_runtime", types.ModuleType("tflite_runtime"))
sys.modules.setdefault("tflite_runtime.interpreter", litert_interpreter)

from birdnetlib import Recording
from birdnetlib.analyzer import Analyzer

from app.audio_preprocessing import AudioPreprocessor
from app.audio_quality import AudioQualityAnalyzer
from app.config import settings
from app.schemas import ClassificationCandidate

# Clases de "no-evento" del modelo BirdNET_GLOBAL_6K_V2.4 (revisadas contra sus labels el 2026-09-16).
# Si cambio de versión del modelo, vuelvo a revisar esta lista.
NON_EVENT_LABELS = frozenset({
    "Dog",
    "Engine",
    "Environmental",
    "Fireworks",
    "Gun",
    "Human non-vocal",
    "Human vocal",
    "Human whistle",
    "Noise",
    "Power tools",
    "Siren",
})


class BirdNetClassifier:
    """Envuelvo BirdNET-Analyzer; lo cargo una sola vez y lo reutilizo en cada petición."""

    def __init__(self) -> None:
        self._analyzer = Analyzer()
        self._preprocessor = AudioPreprocessor(highpass_cutoff_hz=settings.audio_highpass_cutoff_hz)
        self._quality_analyzer = AudioQualityAnalyzer(
            flatness_threshold=settings.audio_noise_flatness_threshold,
            bird_band_energy_ratio_threshold=settings.audio_bird_band_energy_ratio_threshold,
        )

    def classify(
        self,
        audio_path: str,
        recorded_at: datetime | None,
        min_confidence: float,
        max_results: int,
        latitude: float | None = None,
        longitude: float | None = None,
    ) -> list[ClassificationCandidate]:
        # Conservo la frecuencia de muestreo original y paso el estéreo a mono.
        samples, sample_rate = librosa.load(audio_path, sr=None, mono=True)
        cleaned_samples = self._preprocessor.clean(samples, sample_rate)

        # Si el audio no sirve, lanzo el error de calidad y el endpoint lo responde con su código.
        self._quality_analyzer.assert_quality(cleaned_samples, sample_rate)

        cleaned_path = self._write_temp_wav(cleaned_samples, sample_rate)
        try:
            # Solo paso lat/lon si vienen del GPS real: BirdNET descarta las especies que no esperaría ahí.
            recording = Recording(
                self._analyzer,
                cleaned_path,
                date=recorded_at,
                min_conf=min_confidence,
                lat=latitude,
                lon=longitude,
            )
            recording.analyze()
        finally:
            os.remove(cleaned_path)

        return rank_candidates(recording.detections, max_results)

    def _write_temp_wav(self, samples: np.ndarray, sample_rate: int) -> str:
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp_file:
            cleaned_path = tmp_file.name
        sf.write(cleaned_path, samples, sample_rate)
        return cleaned_path


def rank_candidates(detections: list[dict], max_results: int) -> list[ClassificationCandidate]:
    """BirdNET puntúa fragmentos de 3 s: me quedo con la mejor confianza de cada especie y las ordeno.
    La dejo como función pura para probarla sin cargar el modelo."""
    best_by_species: dict[str, ClassificationCandidate] = {}
    for detection in detections:
        scientific_name = detection["scientific_name"]
        if scientific_name in NON_EVENT_LABELS:
            # Descarto lo que no es ave (voz, ruido, sirena); si solo quedaba eso, el resultado sale vacío.
            continue
        confidence = float(detection["confidence"])
        existing = best_by_species.get(scientific_name)
        if existing is None or confidence > existing.confidence:
            best_by_species[scientific_name] = ClassificationCandidate(
                scientific_name=scientific_name,
                common_name=detection["common_name"],
                confidence=confidence,
            )

    ranked = sorted(best_by_species.values(), key=lambda c: c.confidence, reverse=True)
    return ranked[:max_results]
