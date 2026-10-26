RIFF = b"RIFF"
WAVE = b"WAVE"
FLAC = b"fLaC"
ID3 = b"ID3"
JPEG = b"\xff\xd8\xff"
PNG = b"\x89PNG\r\n\x1a\n"
WEBP = b"WEBP"
MPEG_SYNC_MASK = 0xE0
# Bytes del inicio que bastan para reconocer cualquiera de estas firmas.
HEADER_BYTES = 12


class FileSignature:
    """Reconozco el formato real por los primeros bytes, no por el nombre ni el tipo declarado."""

    @staticmethod
    def is_supported_audio(head: bytes) -> bool:
        is_wav = head.startswith(RIFF) and head[8:12] == WAVE
        # MP3: etiqueta ID3 o directamente un frame MPEG (11 bits de sincronía en 1), igual que el backend.
        is_mp3 = head.startswith(ID3) or (len(head) >= 2 and head[0] == 0xFF and head[1] & MPEG_SYNC_MASK == MPEG_SYNC_MASK)
        return is_wav or head.startswith(FLAC) or is_mp3

    @staticmethod
    def is_supported_image(head: bytes) -> bool:
        is_webp = head.startswith(RIFF) and head[8:12] == WEBP
        return head.startswith(JPEG) or head.startswith(PNG) or is_webp
