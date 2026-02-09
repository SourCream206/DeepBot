import re

COMMON_FIXES = {
    "impecator": "imperator",
    "impecatar": "imperator",
    "imperat0r": "imperator",
    "kyrsieger": "kyrsedge",
    "kyrstrez": "kyrsedge",
    "yrsedge": "kyrsedge",
    "darkstee": "darksteel",
}

def normalize_line(line: str) -> str:
    line = line.lower()

    # replace fancy quotes
    line = line.replace("’", "'")

    # remove symbols and junk
    line = re.sub(r"[\[\]\|\!\?\=\%\_\-]", " ", line)

    # remove numbers
    line = re.sub(r"\d+", " ", line)

    # collapse repeated characters (llll → l)
    line = re.sub(r"(.)\1{2,}", r"\1", line)

    # keep only letters + spaces
    line = re.sub(r"[^a-z'\s]", " ", line)

    # normalize spaces
    line = re.sub(r"\s+", " ", line).strip()

    # fix common OCR mistakes
    for bad, good in COMMON_FIXES.items():
        line = line.replace(bad, good)

    return line
