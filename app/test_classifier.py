"""Pruebo el filtrado de clases que no son aves con rank_candidates(), sin cargar el modelo.
Lo ejecuto con: python -m app.test_classifier"""

from app.classifier import rank_candidates


def _detection(scientific_name: str, common_name: str, confidence: float) -> dict:
    return {"scientific_name": scientific_name, "common_name": common_name, "confidence": confidence}


def demo() -> None:
    # Si solo pasaron no-eventos, queda vacío y no "Human vocal" como especie.
    only_human_voice = [
        _detection("Human vocal", "Human vocal", 0.92),
        _detection("Noise", "Noise", 0.4),
    ]
    assert rank_candidates(only_human_voice, max_results=3) == []

    # Devuelvo la especie real aunque "Human vocal" tenga más puntaje.
    mixed = [
        _detection("Human vocal", "Human vocal", 0.95),
        _detection("Luscinia megarhynchos", "Common Nightingale", 0.6),
        _detection("Dog", "Dog", 0.3),
    ]
    ranked = rank_candidates(mixed, max_results=3)
    assert len(ranked) == 1
    assert ranked[0].scientific_name == "Luscinia megarhynchos"

    # Sin no-eventos, dejo una entrada por especie con su mejor confianza.
    normal = [
        _detection("Bubo virginianus", "Great Horned Owl", 0.5),
        _detection("Bubo virginianus", "Great Horned Owl", 0.7),
        _detection("Streptopelia decaocto", "Eurasian Collared-Dove", 0.65),
    ]
    ranked = rank_candidates(normal, max_results=3)
    assert [c.scientific_name for c in ranked] == ["Bubo virginianus", "Streptopelia decaocto"]
    assert ranked[0].confidence == 0.7

    # max_results corta después de ordenar: quedan las especies con mejor confianza.
    ranked = rank_candidates(normal, max_results=1)
    assert [c.scientific_name for c in ranked] == ["Bubo virginianus"]

    # Sin detecciones (nada superó min_confidence) el resultado es vacío, no un error.
    assert rank_candidates([], max_results=3) == []

    print("classifier self-check: OK")


if __name__ == "__main__":
    demo()
