"""Dinamik cikti grid'i icin yardimci fonksiyonlar.

Bu modul kasitli olarak HAFIF tutulmustur: yalnizca `os` ve i18n'e baglidir
(torch/gradio/librosa YOK). Boylece processing.py'nin agir import zincirinden
bagimsiz olarak yerel ortamda test edilebilir.

- derive_label(stem_name): ham stem adindan kullaniciya gosterilecek etiket uretir.
- collect_outputs(output_dir, instruments): cikti klasorundeki ses dosyalarini
  (label, yol) listesine cevirir.
"""

import os
from assets.i18n.i18n import I18nAuto

i18n = I18nAuto()

# Bilinen stem adi -> i18n anahtari eslemesi (gui.py'deki etiketlerle ayni anahtarlar)
STEM_LABEL_KEYS = {
    "vocals": "vocals",
    "instrumental": "instrumental_output",
    "instrument": "instrumental_output",
    "phaseremix": "phase_remix",
    "instrumental_phaseremix": "phase_remix",
    "drums": "drums",
    "drum": "drums",
    "bass": "bass",
    "other": "other",
    "effects": "effects",
    "speech": "speech",
    "music": "music",
    "dry": "dry",
    "male": "male",
    "female": "female",
    "bleed": "bleed",
    "karaoke": "karaoke",
}


def derive_label(stem_name):
    """Ham stem adindan kullaniciya gosterilecek label uretir.

    Bilinen tip -> i18n cevirisi; bilinmeyen -> 'lead_vocal' -> 'Lead Vocal'.
    """
    if not stem_name:
        return "Output"
    key = str(stem_name).strip().lower()
    if key in STEM_LABEL_KEYS:
        return i18n(STEM_LABEL_KEYS[key])
    if key in ("mid", "side"):
        return key.capitalize()
    return str(stem_name).replace("_", " ").strip().title()


def collect_outputs(output_dir, instruments):
    """Cikti klasorundeki ses dosyalarini (label, yol) listesine cevirir.

    instruments: modelin config'inden gelen stem adlari (prefer_target_instrument).
    Inference cikti dosyasini '..._{instr}.{ext}' olarak yazar; bu yuzden her
    dosyanin stem'i, instruments listesindeki bir adin dosya adinda gecmesiyle
    tespit edilir. Listede olmayan ekstra ciktilar (orn. instrumental_phaseremix)
    dosya adinin son '_' parcasindan turetilir.
    """
    audio_exts = (".wav", ".flac", ".mp3", ".ogg", ".m4a", ".aac", ".aiff", ".ac3", ".opus")
    # Inference'in runtime'da ekleyebilecegi bilinen ekstralar + config instruments.
    candidates = list(instruments or []) + ["instrumental_phaseremix", "instrumental", "phaseremix"]
    # Tekillestir, UZUN adlari once dene (instrumental_phaseremix > instrumental)
    seen = set()
    ordered = []
    for name in sorted(candidates, key=len, reverse=True):
        low = str(name).strip().lower()
        if low and low not in seen:
            seen.add(low)
            ordered.append(low)

    results = []
    used_paths = set()
    files = sorted(
        f for f in os.listdir(output_dir)
        if f.lower().endswith(audio_exts)
    )

    # 1) Bilinen/aday instr'leri dosya adinda ara (uzun-once)
    for instr in ordered:
        for f in files:
            path = os.path.join(output_dir, f)
            if path in used_paths:
                continue
            if f"_{instr}" in f.lower():
                results.append((derive_label(instr), path))
                used_paths.add(path)
                break  # bu instr icin ilk eslesen dosya

    # 2) Hicbir adaya eslesemeyen ekstra dosyalar: ad son parcasindan turet
    for f in files:
        path = os.path.join(output_dir, f)
        if path in used_paths:
            continue
        base = os.path.splitext(f)[0]
        guessed = base.split("_")[-1] if "_" in base else base
        results.append((derive_label(guessed), path))
        used_paths.add(path)

    return results
