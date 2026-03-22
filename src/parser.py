"""
Rabobank CSV parser.

Rabobank exporteert twee CSV-varianten:
  - Nieuw formaat (2019+): 26 kolommen, eerste rij = kolomnamen
  - Oud formaat: 18 kolommen, geen header

Beide worden herkend en genormaliseerd naar een uniform DataFrame.
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


# Kolomnamen nieuw Rabobank-formaat (2019+)
RABO_COLUMNS_NEW = [
    "iban",
    "munt",
    "bic",
    "volgnr",
    "datum",
    "rentedatum",
    "bedrag",
    "saldo",
    "tegenrekening_iban",
    "naam_tegenpartij",
    "naam_uiteindelijke_partij",
    "naam_initierende_partij",
    "bic_tegenpartij",
    "code",
    "batch_id",
    "transactiereferentie",
    "machtigingskenmerk",
    "incassant_id",
    "betalingskenmerk",
    "omschrijving_1",
    "omschrijving_2",
    "omschrijving_3",
    "reden_retour",
    "oorspr_bedrag",
    "oorspr_munt",
    "koers",
]

# Kolomnamen oud Rabobank-formaat
RABO_COLUMNS_OLD = [
    "rekeningnummer",
    "munt",
    "rentedatum",
    "bedrag",
    "saldo",
    "datum",
    "valutadatum",
    "intern_code",
    "globale_code",
    "volgnr",
    "betalingskenmerk",
    "naam_tegenpartij",
    "tegenrekening_iban",
    "omschrijving_1",
    "omschrijving_2",
    "omschrijving_3",
    "omschrijving_4",
    "omschrijving_5",
]


def _omschrijving(row: pd.Series) -> str:
    """Plak alle omschrijvingskolommen samen."""
    parts = []
    for col in ["omschrijving_1", "omschrijving_2", "omschrijving_3",
                "omschrijving_4", "omschrijving_5"]:
        if col in row.index and pd.notna(row[col]) and str(row[col]).strip():
            parts.append(str(row[col]).strip())
    return " | ".join(parts)


def _detect_and_load(filepath: Path) -> pd.DataFrame:
    """Detecteer formaat en laad CSV."""
    # Probeer eerst met header (nieuw formaat)
    try:
        df = pd.read_csv(
            filepath,
            sep=",",
            encoding="utf-8",
            dtype=str,
            on_bad_lines="skip",
        )
        # Nieuw formaat: eerste kolom heet IBAN/BBAN of vergelijkbaar
        first_col = df.columns[0].lower().replace("/", "").replace(" ", "")
        if "iban" in first_col or "bban" in first_col or len(df.columns) >= 20:
            df.columns = [c.lower().strip().replace(" ", "_").replace("/", "_")
                          for c in df.columns]
            # Hernoem naar interne namen
            rename_map = {
                "iban_bban": "iban",
                "volgnr": "volgnr",
                "naam_tegenpartij": "naam_tegenpartij",
                "naam_uiteindelijke_partij": "naam_uiteindelijke_partij",
                "naam_initierende_partij": "naam_initierende_partij",
                "tegenrekening_iban_bban": "tegenrekening_iban",
                "omschrijving-1": "omschrijving_1",
                "omschrijving-2": "omschrijving_2",
                "omschrijving-3": "omschrijving_3",
                "saldo_na_trn": "saldo",
                "oorspr_bedrag": "oorspr_bedrag",
                "oorspr_munt": "oorspr_munt",
            }
            df = df.rename(columns=rename_map)
            return df, "new"
    except Exception:
        pass

    # Oud formaat: geen header
    df = pd.read_csv(
        filepath,
        sep=",",
        encoding="utf-8",
        header=None,
        dtype=str,
        on_bad_lines="skip",
    )
    cols = RABO_COLUMNS_OLD[: len(df.columns)]
    df.columns = cols
    return df, "old"


def parse_csv(filepath: str | Path) -> pd.DataFrame:
    """
    Laad een Rabobank CSV-bestand en retourneer een genormaliseerd DataFrame met:
      datum, bedrag (float, negatief=uitgave), saldo, iban, tegenrekening_iban,
      naam_tegenpartij, omschrijving, code, munt, bestand
    """
    filepath = Path(filepath)
    df, fmt = _detect_and_load(filepath)

    # Verwijder lege rijen
    df = df.dropna(how="all")

    # Datum
    for datecol in ["datum", "date"]:
        if datecol in df.columns:
            df["datum"] = pd.to_datetime(df[datecol], dayfirst=True, errors="coerce")
            break

    # Bedrag: vervang komma door punt, verwijder valutasymbolen
    if "bedrag" in df.columns:
        df["bedrag"] = (
            df["bedrag"]
            .astype(str)
            .str.replace(r"[^\d,.\-\+]", "", regex=True)
            .str.replace(",", ".", regex=False)
        )
        df["bedrag"] = pd.to_numeric(df["bedrag"], errors="coerce")

    # Saldo
    if "saldo" in df.columns:
        df["saldo"] = (
            df["saldo"]
            .astype(str)
            .str.replace(r"[^\d,.\-\+]", "", regex=True)
            .str.replace(",", ".", regex=False)
        )
        df["saldo"] = pd.to_numeric(df["saldo"], errors="coerce")

    # Omschrijving samenvoegen
    df["omschrijving"] = df.apply(_omschrijving, axis=1)

    # IBAN eigen rekening
    if "iban" not in df.columns and "rekeningnummer" in df.columns:
        df["iban"] = df["rekeningnummer"]

    # Naam tegenpartij fallback
    for col in ["naam_tegenpartij", "naam_uiteindelijke_partij"]:
        if col not in df.columns:
            df[col] = ""

    # Code (type transactie: ba, bc, id, etc.)
    if "code" not in df.columns:
        df["code"] = ""

    # Munt
    if "munt" not in df.columns:
        df["munt"] = "EUR"

    # Broninformatie
    df["bestand"] = filepath.name

    # Selecteer en hernoem naar uniforme kolommen
    output_cols = [
        "datum", "bedrag", "saldo", "iban", "tegenrekening_iban",
        "naam_tegenpartij", "omschrijving", "code", "munt", "bestand",
    ]
    for col in output_cols:
        if col not in df.columns:
            df[col] = ""

    result = df[output_cols].copy()
    result = result[result["datum"].notna() & result["bedrag"].notna()]
    result = result.sort_values("datum").reset_index(drop=True)
    return result


def load_all_csvs(folder: str | Path) -> pd.DataFrame:
    """Laad alle CSV-bestanden in een map en combineer ze."""
    folder = Path(folder)
    files = list(folder.glob("*.csv")) + list(folder.glob("*.CSV"))
    if not files:
        return pd.DataFrame()

    frames = []
    for f in files:
        try:
            df = parse_csv(f)
            frames.append(df)
        except Exception as e:
            print(f"Fout bij inlezen {f.name}: {e}")

    if not frames:
        return pd.DataFrame()

    combined = pd.concat(frames, ignore_index=True)
    # Verwijder exacte duplicaten (zelfde datum+bedrag+tegenrekening)
    combined = combined.drop_duplicates(
        subset=["datum", "bedrag", "tegenrekening_iban", "omschrijving"]
    )
    return combined.sort_values("datum").reset_index(drop=True)
