"""
Financiële rapportage voor een ANBI-stichting.

Genereert:
  - Baten-en-lastenrekening (verlies-en-winstrekening voor NGO)
  - Balans (vereenvoudigd, kasboekbasis)
  - Projectoverzicht
  - ANBI-transparantieoverzicht
"""

import pandas as pd
import numpy as np
from typing import Optional


def _year_filter(df: pd.DataFrame, jaar: Optional[int]) -> pd.DataFrame:
    if jaar is None:
        return df
    return df[df["datum"].dt.year == jaar]


# ---------------------------------------------------------------------------
# Baten-en-lastenrekening
# ---------------------------------------------------------------------------

def baten_lasten(df: pd.DataFrame, jaar: Optional[int] = None) -> dict:
    """
    Retourneert dict met:
      baten       : DataFrame per categorie (bedrag, aantal_tx)
      lasten      : DataFrame per categorie (bedrag, aantal_tx)
      totaal_baten: float
      totaal_lasten: float
      resultaat   : float  (baten - lasten)
    """
    data = _year_filter(df, jaar)

    baten_df = _groepeer(data[data["type"] == "baten"])
    lasten_df = _groepeer(data[data["type"] == "lasten"])

    # Lasten als positief getal weergeven
    lasten_df["bedrag"] = lasten_df["bedrag"].abs()

    totaal_baten = baten_df["bedrag"].sum()
    totaal_lasten = lasten_df["bedrag"].sum()

    return {
        "baten": baten_df,
        "lasten": lasten_df,
        "totaal_baten": totaal_baten,
        "totaal_lasten": totaal_lasten,
        "resultaat": totaal_baten - totaal_lasten,
    }


def _groepeer(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["categorie", "subcategorie", "bedrag", "aantal_tx"])

    grouped = (
        df.groupby(["categorie", "subcategorie"], dropna=False)
        .agg(bedrag=("bedrag", "sum"), aantal_tx=("bedrag", "count"))
        .reset_index()
    )
    grouped = grouped.sort_values("categorie")
    return grouped


# ---------------------------------------------------------------------------
# Maandoverzicht
# ---------------------------------------------------------------------------

def maandoverzicht(df: pd.DataFrame, jaar: Optional[int] = None) -> pd.DataFrame:
    """Baten, lasten en resultaat per maand."""
    data = _year_filter(df, jaar).copy()
    data["maand"] = data["datum"].dt.to_period("M")

    baten = (
        data[data["type"] == "baten"]
        .groupby("maand")["bedrag"]
        .sum()
        .rename("baten")
    )
    lasten = (
        data[data["type"] == "lasten"]
        .groupby("maand")["bedrag"]
        .sum()
        .abs()
        .rename("lasten")
    )

    result = pd.DataFrame({"baten": baten, "lasten": lasten}).fillna(0)
    result["resultaat"] = result["baten"] - result["lasten"]
    result.index = result.index.astype(str)
    return result.reset_index().rename(columns={"maand": "periode"})


# ---------------------------------------------------------------------------
# Projectoverzicht
# ---------------------------------------------------------------------------

def projectoverzicht(df: pd.DataFrame, jaar: Optional[int] = None) -> pd.DataFrame:
    """Baten en lasten per project."""
    data = _year_filter(df, jaar)
    data = data[data["project"].fillna("").str.strip() != ""]

    if data.empty:
        return pd.DataFrame(
            columns=["project", "baten", "lasten", "resultaat", "aantal_tx"]
        )

    baten = (
        data[data["type"] == "baten"]
        .groupby("project")["bedrag"]
        .sum()
        .rename("baten")
    )
    lasten = (
        data[data["type"] == "lasten"]
        .groupby("project")["bedrag"]
        .sum()
        .abs()
        .rename("lasten")
    )
    aantallen = data.groupby("project")["bedrag"].count().rename("aantal_tx")

    result = pd.DataFrame({"baten": baten, "lasten": lasten, "aantal_tx": aantallen}).fillna(0)
    result["resultaat"] = result["baten"] - result["lasten"]
    return result.reset_index().sort_values("lasten", ascending=False)


# ---------------------------------------------------------------------------
# Kasstroomoverzicht (kasbasis)
# ---------------------------------------------------------------------------

def kasstroomoverzicht(df: pd.DataFrame, jaar: Optional[int] = None) -> pd.DataFrame:
    """Lopende rekening kasstroom per kwartaal."""
    data = _year_filter(df, jaar).copy()
    data["kwartaal"] = data["datum"].dt.to_period("Q")

    instroom = (
        data[data["bedrag"] > 0]
        .groupby("kwartaal")["bedrag"]
        .sum()
        .rename("instroom")
    )
    uitstroom = (
        data[data["bedrag"] < 0]
        .groupby("kwartaal")["bedrag"]
        .sum()
        .abs()
        .rename("uitstroom")
    )

    result = pd.DataFrame({"instroom": instroom, "uitstroom": uitstroom}).fillna(0)
    result["netto"] = result["instroom"] - result["uitstroom"]
    result.index = result.index.astype(str)
    return result.reset_index().rename(columns={"kwartaal": "periode"})


# ---------------------------------------------------------------------------
# ANBI-transparantieoverzicht
# ---------------------------------------------------------------------------

def anbi_overzicht(df: pd.DataFrame, jaar: Optional[int] = None,
                   organisatienaam: str = "") -> dict:
    """
    Gegevens voor ANBI-publicatieplicht (art. 5b Wet IB):
    - Totaal ontvangen giften/subsidies
    - Totale bestedingen per doel
    - Beheerskosten / apparaatskosten
    - Ratio besteding aan doelstelling
    """
    data = _year_filter(df, jaar)

    baten = data[data["type"] == "baten"]
    lasten = data[data["type"] == "lasten"]

    giften_cats = ["Giften", "Donaties", "Subsidies", "Contributies", "Baten"]
    beheer_cats = ["Beheerkosten", "Administratie", "Kantoorkosten", "ICT",
                   "Communicatie", "Fundraising"]

    giften = baten[baten["categorie"].isin(giften_cats)]["bedrag"].sum()
    totaal_baten = baten["bedrag"].sum()

    beheer = abs(
        lasten[lasten["categorie"].str.contains(
            "|".join(beheer_cats), case=False, na=False
        )]["bedrag"]
        .sum()
    )
    totaal_lasten = abs(lasten["bedrag"].sum())
    doelbesteding = totaal_lasten - beheer

    ratio = (doelbesteding / totaal_lasten * 100) if totaal_lasten > 0 else 0

    lasten_per_doel = (
        lasten[~lasten["categorie"].str.contains(
            "|".join(beheer_cats), case=False, na=False
        )]
        .groupby("categorie")["bedrag"]
        .sum()
        .abs()
        .sort_values(ascending=False)
        .reset_index()
        .rename(columns={"bedrag": "bedrag_besteed"})
    )

    return {
        "organisatienaam": organisatienaam,
        "jaar": jaar,
        "totaal_baten": totaal_baten,
        "giften_en_subsidies": giften,
        "totaal_lasten": totaal_lasten,
        "doelbesteding": doelbesteding,
        "beheerkosten": beheer,
        "ratio_doelbesteding_pct": round(ratio, 1),
        "lasten_per_doel": lasten_per_doel,
    }


# ---------------------------------------------------------------------------
# Excel-export
# ---------------------------------------------------------------------------

def export_to_excel(
    df: pd.DataFrame,
    jaar: Optional[int],
    filepath: str,
    organisatienaam: str = "Organisatie",
) -> None:
    """Exporteer volledige jaarrekening naar Excel."""
    bl = baten_lasten(df, jaar)
    mnd = maandoverzicht(df, jaar)
    proj = projectoverzicht(df, jaar)
    anbi = anbi_overzicht(df, jaar, organisatienaam)

    with pd.ExcelWriter(filepath, engine="xlsxwriter") as writer:
        wb = writer.book
        header_fmt = wb.add_format(
            {"bold": True, "bg_color": "#003366", "font_color": "white",
             "border": 1}
        )
        money_fmt = wb.add_format({"num_format": "€#,##0.00", "border": 1})
        pct_fmt = wb.add_format({"num_format": "0.0%", "border": 1})

        # --- Baten-en-lastenrekening ---
        ws = wb.add_worksheet("Baten-Lasten")
        writer.sheets["Baten-Lasten"] = ws
        row = 0
        ws.write(row, 0, f"BATEN-EN-LASTENREKENING {jaar or 'alle jaren'}", header_fmt)
        ws.write(row, 1, organisatienaam, header_fmt)
        row += 2

        ws.write(row, 0, "BATEN", header_fmt)
        row += 1
        for _, r in bl["baten"].iterrows():
            ws.write(row, 0, r["categorie"])
            ws.write(row, 1, r.get("subcategorie", ""))
            ws.write(row, 2, r["bedrag"], money_fmt)
            ws.write(row, 3, int(r["aantal_tx"]))
            row += 1
        ws.write(row, 0, "Totaal baten")
        ws.write(row, 2, bl["totaal_baten"], money_fmt)
        row += 2

        ws.write(row, 0, "LASTEN", header_fmt)
        row += 1
        for _, r in bl["lasten"].iterrows():
            ws.write(row, 0, r["categorie"])
            ws.write(row, 1, r.get("subcategorie", ""))
            ws.write(row, 2, r["bedrag"], money_fmt)
            ws.write(row, 3, int(r["aantal_tx"]))
            row += 1
        ws.write(row, 0, "Totaal lasten")
        ws.write(row, 2, bl["totaal_lasten"], money_fmt)
        row += 2

        ws.write(row, 0, "RESULTAAT")
        ws.write(row, 2, bl["resultaat"], money_fmt)
        ws.set_column(0, 0, 35)
        ws.set_column(1, 1, 25)
        ws.set_column(2, 2, 15)
        ws.set_column(3, 3, 12)

        # --- Maandoverzicht ---
        mnd.to_excel(writer, sheet_name="Maandoverzicht", index=False)

        # --- Projecten ---
        if not proj.empty:
            proj.to_excel(writer, sheet_name="Projecten", index=False)

        # --- Alle transacties ---
        filtered = _year_filter(df, jaar)
        filtered.to_excel(writer, sheet_name="Transacties", index=False)

        # --- ANBI ---
        ws_anbi = wb.add_worksheet("ANBI")
        writer.sheets["ANBI"] = ws_anbi
        ws_anbi.write(0, 0, "ANBI TRANSPARANTIEOVERZICHT", header_fmt)
        ws_anbi.write(0, 1, f"{organisatienaam} – {jaar or 'alle jaren'}", header_fmt)
        items = [
            ("Organisatienaam", anbi["organisatienaam"]),
            ("Boekjaar", str(anbi["jaar"])),
            ("Totaal baten", anbi["totaal_baten"]),
            ("Giften & subsidies", anbi["giften_en_subsidies"]),
            ("Totaal lasten", anbi["totaal_lasten"]),
            ("Doelbesteding", anbi["doelbesteding"]),
            ("Beheerkosten", anbi["beheerkosten"]),
            ("Ratio doelbesteding", f"{anbi['ratio_doelbesteding_pct']}%"),
        ]
        for i, (label, value) in enumerate(items, start=2):
            ws_anbi.write(i, 0, label)
            ws_anbi.write(i, 1, value)
        ws_anbi.set_column(0, 0, 30)
        ws_anbi.set_column(1, 1, 20)
