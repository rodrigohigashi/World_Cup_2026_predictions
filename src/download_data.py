"""
Download data from both sources:
- Fjelstul World Cup database (GitHub) — historical matches 1930-2022
- Kaggle FIFA World Cup 2026 dataset — current squads + live results
"""

import subprocess
import sys
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).parent.parent
DATA_FJELSTUL = ROOT / "data" / "fjelstul"
DATA_KAGGLE = ROOT / "data" / "kaggle_2026"

# Fjelstul raw CSV base URL
FJELSTUL_BASE = (
    "https://raw.githubusercontent.com/jfjelstul/worldcup/master/data-csv"
)

FJELSTUL_FILES = [
    "matches.csv",
    "goals.csv",
    "teams.csv",
    "tournaments.csv",
    "team_appearances.csv",
]


def download_fjelstul():
    print("=== Baixando Fjelstul (histórico 1930-2022) ===")
    DATA_FJELSTUL.mkdir(parents=True, exist_ok=True)
    for fname in FJELSTUL_FILES:
        dest = DATA_FJELSTUL / fname
        if dest.exists():
            print(f"  [ok] {fname} já existe")
            continue
        url = f"{FJELSTUL_BASE}/{fname}"
        print(f"  Baixando {fname}...")
        urllib.request.urlretrieve(url, dest)
        print(f"  [ok] {fname} salvo")


def download_kaggle(dataset_slug: str = "die9origephit/fifa-world-cup-2022-and-2026"):
    """
    dataset_slug examples (update if needed):
      - 'die9origephit/fifa-world-cup-2022-and-2026'
      - 'piterfm/2022-world-cup-predictions' (backup)
    """
    print("\n=== Baixando Kaggle 2026 ===")
    DATA_KAGGLE.mkdir(parents=True, exist_ok=True)

    result = subprocess.run(
        [
            sys.executable, "-m", "kaggle",
            "datasets", "download",
            "-d", dataset_slug,
            "-p", str(DATA_KAGGLE),
            "--unzip",
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode == 0:
        print("  [ok] Dataset Kaggle baixado e descompactado")
        print(result.stdout)
    else:
        print("  [ERRO] Falha no download Kaggle:")
        print(result.stderr)
        print("\n  -> Verifique se kaggle.json está em C:\\Users\\<user>\\.kaggle\\")
        print("  -> Ou baixe manualmente e extraia em data/kaggle_2026/")


if __name__ == "__main__":
    download_fjelstul()
    download_kaggle()
    print("\nDone! Próximo passo: rode 'python src/build_dataset.py'")
