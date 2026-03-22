"""
ASFK – Financieel Dashboard NGO
Rabobank CSV  →  Mapping  →  Jaarrekening + Live Dashboard

Starten:
    streamlit run app.py
"""

import io
import os
import tempfile
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.parser import load_all_csvs, parse_csv
from src.mapper import load_mapping, apply_mapping, classification_summary
from src.reports import (
    baten_lasten,
    maandoverzicht,
    projectoverzicht,
    kasstroomoverzicht,
    anbi_overzicht,
    export_to_excel,
)

# ---------------------------------------------------------------------------
# Pagina-configuratie
# ---------------------------------------------------------------------------
st.set_page_config(
    page_title="ASFK Financieel Dashboard",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .metric-card {
        background: #f0f4ff;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin-bottom: 0.5rem;
    }
    .stDataFrame { font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------------------------
# Sidebar: bestanden uploaden / laden
# ---------------------------------------------------------------------------
with st.sidebar:
    st.title("📂 Bestanden")

    st.subheader("1. Bankafschriften (CSV)")
    uploaded_csvs = st.file_uploader(
        "Upload Rabobank CSV-bestand(en)",
        type=["csv"],
        accept_multiple_files=True,
        help="Exporteer via Rabobank Online → Betalen → Afschriften → Downloaden (CSV)",
    )

    st.subheader("2. Mapping")
    uploaded_mapping = st.file_uploader(
        "Upload mapping (Excel of CSV)",
        type=["xlsx", "xls", "csv"],
        help="Zie data/mapping_template.xlsx voor de structuur",
    )

    st.divider()

    # Optie: bestanden uit map laden (voor lokaal gebruik)
    use_local = st.checkbox(
        "Gebruik bestanden uit data/-map",
        value=not bool(uploaded_csvs),
        help="Zet CSV-bestanden in data/bankafschriften/ en mapping in data/mapping.xlsx",
    )

    st.divider()
    org_name = st.text_input("Organisatienaam", value="Stichting ASFK")

    st.subheader("Filter")
    jaar_optie = st.selectbox("Boekjaar", options=["Alles"] + list(range(2030, 2019, -1)))
    jaar = None if jaar_optie == "Alles" else int(jaar_optie)


# ---------------------------------------------------------------------------
# Data laden
# ---------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def _load_uploaded_csvs(files) -> pd.DataFrame:
    frames = []
    for f in files:
        tmp = tempfile.NamedTemporaryFile(suffix=".csv", delete=False)
        tmp.write(f.read())
        tmp.flush()
        try:
            frames.append(parse_csv(tmp.name))
        except Exception as e:
            st.warning(f"Fout bij {f.name}: {e}")
        finally:
            os.unlink(tmp.name)
    if not frames:
        return pd.DataFrame()
    df = pd.concat(frames, ignore_index=True)
    return df.drop_duplicates(
        subset=["datum", "bedrag", "tegenrekening_iban", "omschrijving"]
    ).sort_values("datum").reset_index(drop=True)


@st.cache_data(show_spinner=False)
def _load_mapping_file(f) -> pd.DataFrame:
    suffix = Path(f.name).suffix.lower()
    tmp = tempfile.NamedTemporaryFile(suffix=suffix, delete=False)
    tmp.write(f.read())
    tmp.flush()
    try:
        return load_mapping(tmp.name)
    finally:
        os.unlink(tmp.name)


# Transacties
transactions = pd.DataFrame()
with st.spinner("Transacties laden..."):
    if uploaded_csvs:
        transactions = _load_uploaded_csvs(uploaded_csvs)
    elif use_local:
        local_dir = Path("data/bankafschriften")
        if local_dir.exists():
            transactions = load_all_csvs(local_dir)

# Mapping
mapping_df = pd.DataFrame()
with st.spinner("Mapping laden..."):
    if uploaded_mapping:
        try:
            mapping_df = _load_mapping_file(uploaded_mapping)
        except Exception as e:
            st.error(f"Fout bij laden mapping: {e}")
    elif use_local:
        local_map = Path("data/mapping.xlsx")
        if local_map.exists():
            try:
                mapping_df = load_mapping(local_map)
            except Exception as e:
                st.warning(f"Mapping niet geladen: {e}")

# Mapping toepassen
if not transactions.empty and not mapping_df.empty:
    transactions = apply_mapping(transactions, mapping_df)
elif not transactions.empty:
    # Geen mapping: type afleiden van tekenbedrag
    transactions["categorie"] = "Niet geclassificeerd"
    transactions["subcategorie"] = ""
    transactions["type"] = transactions["bedrag"].apply(
        lambda x: "baten" if x > 0 else "lasten"
    )
    transactions["project"] = ""
    transactions["grootboek"] = ""


# ---------------------------------------------------------------------------
# Hoofdinhoud
# ---------------------------------------------------------------------------
st.title(f"📊 {org_name} – Financieel Dashboard")

if transactions.empty:
    st.info(
        "Upload bankafschriften (CSV) via de zijbalk om te beginnen, "
        "of zet bestanden in `data/bankafschriften/`."
    )

    # Toon template-download
    st.subheader("Aan de slag")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            """
            **Stap 1 – Bankafschrift exporteren**
            1. Log in op Rabobank Online Bankieren
            2. Ga naar *Betalen* → *Afschriften*
            3. Kies periode en exporteer als **CSV**
            4. Upload hier via de zijbalk

            **Verwacht Rabobank CSV-formaat**
            Kolommen: IBAN/BBAN, Munt, BIC, Volgnr, Datum, Bedrag, Saldo,
            Tegenrekening, Naam tegenpartij, Omschrijving...
            """
        )
    with col2:
        st.markdown(
            """
            **Stap 2 – Mapping maken**

            De mapping bepaalt hoe elke transactie wordt ingedeeld.
            Download de template hieronder, vul in, en upload.

            | veld | patroon | categorie | type | project | grootboek |
            |------|---------|-----------|------|---------|-----------|
            | naam_tegenpartij | Belastingdienst | Subsidies | baten | | 8000 |
            | omschrijving | salaris | Personeelskosten | lasten | | 4010 |
            | alle | intern | Neutraal | neutraal | | |
            """
        )

    # Download mapping-template
    template_path = Path("data/mapping_template.xlsx")
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "⬇️ Download mapping template (Excel)",
                data=f.read(),
                file_name="mapping_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
    st.stop()


# ---------------------------------------------------------------------------
# Filters op jaartal
# ---------------------------------------------------------------------------
jaren = sorted(transactions["datum"].dt.year.dropna().unique().astype(int), reverse=True)
if jaar and jaar not in jaren:
    st.warning(f"Geen transacties gevonden voor {jaar}.")

data = transactions[transactions["datum"].dt.year == jaar] if jaar else transactions


# ---------------------------------------------------------------------------
# KPI-blok bovenaan
# ---------------------------------------------------------------------------
bl = baten_lasten(transactions, jaar)
cl = classification_summary(data)

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric("Totaal baten", f"€ {bl['totaal_baten']:,.2f}")
with col2:
    st.metric("Totaal lasten", f"€ {bl['totaal_lasten']:,.2f}")
with col3:
    delta_color = "normal" if bl["resultaat"] >= 0 else "inverse"
    st.metric(
        "Resultaat",
        f"€ {bl['resultaat']:,.2f}",
        delta=f"{'+ ' if bl['resultaat'] >= 0 else ''}{bl['resultaat']:,.2f}",
        delta_color=delta_color,
    )
with col4:
    st.metric("Aantal transacties", len(data))
with col5:
    st.metric(
        "Geclassificeerd",
        f"{cl['percentage']}%",
        delta=f"{cl['geclassificeerd']}/{cl['totaal']}",
    )

st.divider()

# ---------------------------------------------------------------------------
# Tabs
# ---------------------------------------------------------------------------
tab_bl, tab_mnd, tab_proj, tab_anbi, tab_tx, tab_export = st.tabs([
    "📋 Baten & Lasten",
    "📅 Maandoverzicht",
    "🏗️ Projecten",
    "🏛️ ANBI",
    "🔍 Transacties",
    "⬇️ Export",
])

# ---- Tab: Baten & Lasten ----
with tab_bl:
    col_b, col_l = st.columns(2)

    with col_b:
        st.subheader("Baten")
        if not bl["baten"].empty:
            st.dataframe(
                bl["baten"].style.format({"bedrag": "€ {:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.pie(
                bl["baten"],
                values="bedrag",
                names="categorie",
                title="Baten per categorie",
                color_discrete_sequence=px.colors.sequential.Blues_r,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Geen baten gevonden.")

    with col_l:
        st.subheader("Lasten")
        if not bl["lasten"].empty:
            st.dataframe(
                bl["lasten"].style.format({"bedrag": "€ {:,.2f}"}),
                use_container_width=True,
                hide_index=True,
            )
            fig = px.pie(
                bl["lasten"],
                values="bedrag",
                names="categorie",
                title="Lasten per categorie",
                color_discrete_sequence=px.colors.sequential.Reds_r,
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("Geen lasten gevonden.")

    # Samenvatting
    st.subheader("Samenvatting")
    samenvatting = pd.DataFrame(
        {
            "Post": ["Totaal baten", "Totaal lasten", "Resultaat boekjaar"],
            "Bedrag": [bl["totaal_baten"], -bl["totaal_lasten"], bl["resultaat"]],
        }
    )
    st.dataframe(
        samenvatting.style.format({"Bedrag": "€ {:,.2f}"}).applymap(
            lambda v: "color: green" if v > 0 else ("color: red" if v < 0 else ""),
            subset=["Bedrag"],
        ),
        use_container_width=True,
        hide_index=True,
    )


# ---- Tab: Maandoverzicht ----
with tab_mnd:
    mnd = maandoverzicht(transactions, jaar)
    kas = kasstroomoverzicht(transactions, jaar)

    st.subheader("Baten en lasten per maand")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=mnd["periode"], y=mnd["baten"], name="Baten",
                         marker_color="#2196F3"))
    fig.add_trace(go.Bar(x=mnd["periode"], y=mnd["lasten"], name="Lasten",
                         marker_color="#F44336"))
    fig.add_trace(go.Scatter(x=mnd["periode"], y=mnd["resultaat"],
                             name="Resultaat", mode="lines+markers",
                             line=dict(color="#4CAF50", width=2)))
    fig.update_layout(barmode="group", xaxis_title="Periode",
                      yaxis_title="Bedrag (€)", legend_title="")
    st.plotly_chart(fig, use_container_width=True)

    st.dataframe(
        mnd.style.format({"baten": "€ {:,.2f}", "lasten": "€ {:,.2f}",
                          "resultaat": "€ {:,.2f}"}),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Kasstroom per kwartaal")
    fig2 = go.Figure()
    fig2.add_trace(go.Bar(x=kas["periode"], y=kas["instroom"], name="Instroom",
                          marker_color="#4CAF50"))
    fig2.add_trace(go.Bar(x=kas["periode"], y=kas["uitstroom"], name="Uitstroom",
                          marker_color="#FF5722"))
    fig2.add_trace(go.Scatter(x=kas["periode"], y=kas["netto"], name="Netto",
                              mode="lines+markers",
                              line=dict(color="#9C27B0", width=2)))
    fig2.update_layout(barmode="group")
    st.plotly_chart(fig2, use_container_width=True)


# ---- Tab: Projecten ----
with tab_proj:
    proj = projectoverzicht(transactions, jaar)
    st.subheader("Overzicht per project")
    if proj.empty:
        st.info(
            "Geen projecten gevonden. Voeg een 'project'-kolom toe in je mapping "
            "om transacties aan projecten te koppelen."
        )
    else:
        st.dataframe(
            proj.style.format(
                {"baten": "€ {:,.2f}", "lasten": "€ {:,.2f}",
                 "resultaat": "€ {:,.2f}"}
            ),
            use_container_width=True,
            hide_index=True,
        )
        fig = px.bar(
            proj,
            x="project",
            y=["baten", "lasten"],
            barmode="group",
            title="Baten vs. lasten per project",
            color_discrete_map={"baten": "#2196F3", "lasten": "#F44336"},
        )
        st.plotly_chart(fig, use_container_width=True)


# ---- Tab: ANBI ----
with tab_anbi:
    anbi = anbi_overzicht(transactions, jaar, org_name)
    st.subheader("ANBI Transparantieoverzicht")
    st.caption(
        "Op grond van art. 5b Wet IB 2001 zijn ANBI-instellingen verplicht "
        "bepaalde financiële informatie openbaar te maken."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Totaal baten", f"€ {anbi['totaal_baten']:,.2f}")
        st.metric("Giften & subsidies", f"€ {anbi['giften_en_subsidies']:,.2f}")
    with col2:
        st.metric("Totaal lasten", f"€ {anbi['totaal_lasten']:,.2f}")
        st.metric("Doelbesteding", f"€ {anbi['doelbesteding']:,.2f}")
    with col3:
        st.metric("Beheerkosten", f"€ {anbi['beheerkosten']:,.2f}")
        st.metric(
            "Ratio doelbesteding",
            f"{anbi['ratio_doelbesteding_pct']}%",
            help="Streefwaarde voor ANBI: >90%",
        )

    # Gauge voor ratio
    fig_gauge = go.Figure(
        go.Indicator(
            mode="gauge+number",
            value=anbi["ratio_doelbesteding_pct"],
            title={"text": "Besteding aan doelstelling (%)"},
            gauge={
                "axis": {"range": [0, 100]},
                "bar": {"color": "#2196F3"},
                "steps": [
                    {"range": [0, 70], "color": "#FFCDD2"},
                    {"range": [70, 90], "color": "#FFF9C4"},
                    {"range": [90, 100], "color": "#C8E6C9"},
                ],
                "threshold": {
                    "line": {"color": "green", "width": 4},
                    "thickness": 0.75,
                    "value": 90,
                },
            },
        )
    )
    st.plotly_chart(fig_gauge, use_container_width=True)

    if not anbi["lasten_per_doel"].empty:
        st.subheader("Bestedingen per doelstelling")
        st.dataframe(
            anbi["lasten_per_doel"].style.format({"bedrag_besteed": "€ {:,.2f}"}),
            use_container_width=True,
            hide_index=True,
        )


# ---- Tab: Transacties ----
with tab_tx:
    st.subheader("Transactielijst")

    # Filteropties
    with st.expander("Filters", expanded=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            cats = ["Alle"] + sorted(data["categorie"].unique().tolist())
            sel_cat = st.selectbox("Categorie", cats)
        with col2:
            types = ["Alle", "baten", "lasten", "neutraal"]
            sel_type = st.selectbox("Type", types)
        with col3:
            zoek = st.text_input("Zoek in omschrijving of naam")

    filtered = data.copy()
    if sel_cat != "Alle":
        filtered = filtered[filtered["categorie"] == sel_cat]
    if sel_type != "Alle":
        filtered = filtered[filtered["type"] == sel_type]
    if zoek:
        mask = (
            filtered["omschrijving"].str.contains(zoek, case=False, na=False)
            | filtered["naam_tegenpartij"].str.contains(zoek, case=False, na=False)
        )
        filtered = filtered[mask]

    # Kleurcodering op type
    def _kleur(row):
        if row["type"] == "baten":
            return ["background-color: #e8f5e9"] * len(row)
        elif row["type"] == "lasten":
            return ["background-color: #ffebee"] * len(row)
        return [""] * len(row)

    display_cols = [
        "datum", "naam_tegenpartij", "omschrijving", "bedrag",
        "categorie", "subcategorie", "type", "project",
    ]
    show_df = filtered[[c for c in display_cols if c in filtered.columns]]

    st.dataframe(
        show_df.style.apply(_kleur, axis=1).format({"bedrag": "€ {:,.2f}"}),
        use_container_width=True,
        height=500,
    )

    st.caption(f"{len(filtered)} transacties weergegeven van {len(data)} totaal")

    # Classificatieproblemen
    niet_geclassificeerd = data[data["categorie"] == "Niet geclassificeerd"]
    if not niet_geclassificeerd.empty:
        with st.expander(
            f"⚠️ {len(niet_geclassificeerd)} niet-geclassificeerde transacties"
        ):
            st.dataframe(
                niet_geclassificeerd[
                    [c for c in display_cols if c in niet_geclassificeerd.columns]
                ],
                use_container_width=True,
                hide_index=True,
            )
            st.info(
                "Voeg regels toe aan je mapping om deze transacties te classificeren."
            )


# ---- Tab: Export ----
with tab_export:
    st.subheader("Exporteer jaarrekening")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("**Excel – volledige jaarrekening**")
        if st.button("Genereer Excel", type="primary"):
            with st.spinner("Excel genereren..."):
                with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
                    tmp_path = tmp.name
                export_to_excel(transactions, jaar, tmp_path, org_name)
                with open(tmp_path, "rb") as f:
                    st.download_button(
                        "⬇️ Download jaarrekening.xlsx",
                        data=f.read(),
                        file_name=f"jaarrekening_{jaar or 'totaal'}_{org_name.replace(' ', '_')}.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    )
                os.unlink(tmp_path)

    with col2:
        st.markdown("**CSV – alle (gefilterde) transacties**")
        csv_data = data.to_csv(index=False, sep=";", decimal=",")
        st.download_button(
            "⬇️ Download transacties.csv",
            data=csv_data.encode("utf-8-sig"),
            file_name=f"transacties_{jaar or 'totaal'}.csv",
            mime="text/csv",
        )

    st.divider()
    st.markdown("**Mapping template**")
    template_path = Path("data/mapping_template.xlsx")
    if template_path.exists():
        with open(template_path, "rb") as f:
            st.download_button(
                "⬇️ Download mapping_template.xlsx",
                data=f.read(),
                file_name="mapping_template.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )

    st.subheader("Statistieken verwerking")
    cl2 = classification_summary(data)
    st.json(cl2)
    st.caption(
        f"Periode: {data['datum'].min().date()} t/m {data['datum'].max().date()}"
        if not data.empty and data["datum"].notna().any() else ""
    )
