"""
Categorie-mapping engine.

De mapping is een Excel- of CSV-bestand met regels die bepalen hoe een
transactie wordt ingedeeld. Elke regel bevat:

  veld        : welk veld te matchen (naam_tegenpartij / tegenrekening_iban /
                omschrijving / code / alle)
  patroon     : tekst of regex om op te matchen (hoofdletterongevoelig)
  categorie   : bijv. "Personeelskosten"
  subcategorie: bijv. "Salarissen"
  type        : "baten" of "lasten" (of "neutraal" voor interne overboekingen)
  project     : optioneel projectlabel
  grootboek   : optioneel grootboekrekeningnummer

Regels worden top-down geëvalueerd; de eerste match wint.
Transacties zonder match krijgen categorie "Niet geclassificeerd".
"""

import re
import pandas as pd
from pathlib import Path


REQUIRED_COLUMNS = ["veld", "patroon", "categorie", "type"]


def load_mapping(filepath: str | Path) -> pd.DataFrame:
    """Laad mapping-bestand (Excel of CSV)."""
    filepath = Path(filepath)
    if filepath.suffix.lower() in (".xlsx", ".xls"):
        df = pd.read_excel(filepath, dtype=str)
    else:
        df = pd.read_csv(filepath, dtype=str, sep=None, engine="python")

    df.columns = [c.lower().strip().replace(" ", "_") for c in df.columns]

    for col in REQUIRED_COLUMNS:
        if col not in df.columns:
            raise ValueError(
                f"Mappingbestand mist verplichte kolom '{col}'. "
                f"Aanwezig: {list(df.columns)}"
            )

    # Optionele kolommen met standaardwaarden
    for col, default in [
        ("subcategorie", ""),
        ("project", ""),
        ("grootboek", ""),
        ("notitie", ""),
    ]:
        if col not in df.columns:
            df[col] = default

    # Verwijder lege regels
    df = df.dropna(subset=["patroon", "categorie"]).reset_index(drop=True)
    return df


def _match_row(tx: pd.Series, rule: pd.Series) -> bool:
    """Controleer of een transactie voldoet aan een mappingregel."""
    veld = str(rule.get("veld", "alle")).lower().strip()
    patroon = str(rule.get("patroon", "")).strip()
    if not patroon:
        return False

    def _check(text: str) -> bool:
        try:
            return bool(re.search(patroon, text, re.IGNORECASE))
        except re.error:
            return patroon.lower() in text.lower()

    if veld == "alle":
        return any(
            _check(str(tx.get(f, "")))
            for f in ["naam_tegenpartij", "tegenrekening_iban", "omschrijving", "code"]
        )
    elif veld in tx.index:
        return _check(str(tx.get(veld, "")))
    return False


def apply_mapping(transactions: pd.DataFrame, mapping: pd.DataFrame) -> pd.DataFrame:
    """
    Voeg categoriekolommen toe aan het transactie-DataFrame.

    Nieuwe kolommen: categorie, subcategorie, type, project, grootboek
    """
    result = transactions.copy()

    # Standaardwaarden
    result["categorie"] = "Niet geclassificeerd"
    result["subcategorie"] = ""
    result["type"] = _guess_type(result)
    result["project"] = ""
    result["grootboek"] = ""

    for idx, tx in result.iterrows():
        for _, rule in mapping.iterrows():
            if _match_row(tx, rule):
                result.at[idx, "categorie"] = str(rule.get("categorie", "")).strip()
                result.at[idx, "subcategorie"] = str(rule.get("subcategorie", "")).strip()
                result.at[idx, "type"] = str(rule.get("type", "")).lower().strip()
                result.at[idx, "project"] = str(rule.get("project", "")).strip()
                result.at[idx, "grootboek"] = str(rule.get("grootboek", "")).strip()
                break  # eerste match wint

    return result


def _guess_type(df: pd.DataFrame) -> pd.Series:
    """
    Initiële schatting van type op basis van teken bedrag.
    Wordt overschreven door de mapping waar van toepassing.
    """
    types = []
    for _, row in df.iterrows():
        try:
            bedrag = float(row.get("bedrag", 0))
            types.append("baten" if bedrag > 0 else "lasten")
        except (ValueError, TypeError):
            types.append("lasten")
    return pd.Series(types, index=df.index)


def classification_summary(transactions: pd.DataFrame) -> dict:
    """Geef een overzicht van classificatiestatus terug."""
    total = len(transactions)
    classified = (transactions["categorie"] != "Niet geclassificeerd").sum()
    return {
        "totaal": total,
        "geclassificeerd": int(classified),
        "niet_geclassificeerd": int(total - classified),
        "percentage": round(classified / total * 100, 1) if total else 0,
    }
