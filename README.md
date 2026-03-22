# ASFK – Financieel Dashboard NGO

Transparant financieel dashboard voor een ANBI-stichting op basis van Rabobank bankafschriften.

## Functionaliteiten

- **Baten-en-lastenrekening** per jaar, met uitsplitsing per categorie
- **Maandoverzicht** en kasstroomoverzicht per kwartaal
- **Projectoverzicht** – koppel transacties aan projecten/fondsen
- **ANBI-transparantieoverzicht** – ratio doelbesteding, bestedingen per doelstelling
- **Transactielijst** met filters en kleurcodering
- **Excel-export** – volledige jaarrekening in één klik
- **Mapping-engine** – flexibele classificatie via Excel/CSV zonder code te wijzigen

## Snel starten

```bash
pip install -r requirements.txt
streamlit run app.py
```

## Werkwijze

### 1. Bankafschrift exporteren vanuit Rabobank

1. Log in op Rabobank Online Bankieren
2. Ga naar **Betalen → Afschriften**
3. Selecteer de gewenste periode
4. Exporteer als **CSV**
5. Zet het bestand in `data/bankafschriften/` of upload via de zijbalk

### 2. Mapping instellen

De mapping bepaalt hoe elke transactie wordt gecategoriseerd:

| Kolom | Uitleg |
|-------|--------|
| `veld` | Welk veld matchen: `naam_tegenpartij`, `tegenrekening_iban`, `omschrijving`, `code`, of `alle` |
| `patroon` | Tekst of reguliere expressie (hoofdletterongevoelig) |
| `categorie` | Naam van de categorie |
| `subcategorie` | Optionele uitsplitsing |
| `type` | `baten`, `lasten`, of `neutraal` |
| `project` | Koppeling aan project/fonds |
| `grootboek` | Grootboekrekeningnummer |

Download de template via het dashboard of gebruik `data/mapping_template.xlsx`.

Regels worden van boven naar beneden geëvalueerd – de **eerste match** wint.

### 3. Genereer jaarrekening

- Open het dashboard op `http://localhost:8501`
- Upload je CSV-bestanden en mapping
- Selecteer het boekjaar
- Exporteer de jaarrekening als Excel via de **Export**-tab

## Projectstructuur

```
ASFK/
├── app.py                          # Streamlit dashboard
├── requirements.txt
├── create_template.py              # Eenmalig: genereer mapping template
├── src/
│   ├── parser.py                   # Rabobank CSV inlezen (nieuw + oud formaat)
│   ├── mapper.py                   # Categorisering via mapping
│   └── reports.py                  # Baten/lasten, ANBI, Excel-export
└── data/
    ├── bankafschriften/            # Zet hier je CSV-bestanden
    │   └── voorbeeld_2024.csv      # Voorbeelddata
    └── mapping_template.xlsx       # Mapping template
```

## ANBI-transparantie

Het dashboard berekent automatisch:
- Totaal baten en giften/subsidies
- Doelbesteding vs. beheerkosten
- **Ratio doelbesteding** (streefwaarde: >90%)
- Uitsplitsing bestedingen per doelstelling

Deze cijfers kun je direct gebruiken voor de ANBI-publicatieplicht op je website.
