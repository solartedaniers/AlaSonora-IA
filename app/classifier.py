from birdnetlib.analyzer import Analyzer


class BirdNetClassifier:
    """Wraps birdnetlib's BirdNET-Analyzer model.

    The model is loaded once (in __init__) and reused for every request —
    reloading it per request would be wasteful, since it's the same
    interpreter/weights regardless of which recording is being analyzed.
    """

    def __init__(self) -> None:
        self._analyzer = Analyzer()
