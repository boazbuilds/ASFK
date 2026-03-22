"""Eenmalig script om de mapping-template te genereren."""
import pandas as pd
from pathlib import Path

mapping_data = [
    # veld, patroon, categorie, subcategorie, type, project, grootboek, notitie
    ("naam_tegenpartij", "Ministerie|ministerie", "Subsidies", "Rijkssubsidies", "baten", "", "8000", "Rijkssubsidies"),
    ("naam_tegenpartij", "Gemeente", "Subsidies", "Gemeentelijke subsidies", "baten", "Buurtproject", "8010", "Gemeentelijke subsidies"),
    ("naam_tegenpartij", "Stichting Fonds", "Subsidies", "Fondsenwerving", "baten", "", "8020", "Fondsbijdragen"),
    ("omschrijving", "[Dd]onati|[Gg]ift|[Cc]ollecte|[Ss]ponsor", "Giften & donaties", "Particuliere giften", "baten", "", "8100", "Giften van particulieren en bedrijven"),
    ("omschrijving", "[Cc]ontributie", "Giften & donaties", "Contributies", "baten", "", "8110", "Lidmaatschapsbijdragen"),
    ("omschrijving", "[Ss]alaris|[Ll]oon", "Personeelskosten", "Salarissen", "lasten", "", "4010", "Bruto salarissen personeel"),
    ("naam_tegenpartij", "KPN|T-Mobile|Vodafone|Ziggo", "Bedrijfskosten", "Telefoon & internet", "lasten", "", "4200", "Telecom abonnementen"),
    ("naam_tegenpartij", "NS Zakelijk|Arriva|OV-chipkaart", "Bedrijfskosten", "Reiskosten", "lasten", "", "4210", "Openbaar vervoer medewerkers"),
    ("naam_tegenpartij", "Accountant|Notaris|Juridisch", "Bedrijfskosten", "Professionele diensten", "lasten", "", "4300", "Accountants en juridisch advies"),
    ("omschrijving", "[Kk]antoor|[Pp]rint|papier|[Bb]enodigdheden", "Bedrijfskosten", "Kantoorkosten", "lasten", "", "4220", "Kantoorbenodigdheden"),
    ("omschrijving", "[Dd]rukwerk|[Ff]lyer|[Bb]rochure|[Jj]aarverslag", "Communicatie", "Drukwerk", "lasten", "", "4400", "Drukwerk en publicaties"),
    ("omschrijving", "[Cc]ater|[Ee]vent|[Bb]ijeenkomst|[Aa]ctiviteit", "Activiteiten", "Evenementen", "lasten", "", "4500", "Kosten bijeenkomsten en events"),
    ("naam_tegenpartij", "Verzeker|ANWB|AON", "Bedrijfskosten", "Verzekeringen", "lasten", "", "4230", "Zakelijke verzekeringen"),
    ("omschrijving", "intern|eigen rekening|spaarrekening", "Neutraal", "Interne overboekingen", "neutraal", "", "9000", "Interne overboekingen"),
]

df = pd.DataFrame(
    mapping_data,
    columns=["veld", "patroon", "categorie", "subcategorie", "type",
             "project", "grootboek", "notitie"],
)

output_path = Path("data/mapping.xlsx")
output_path.parent.mkdir(exist_ok=True)

with pd.ExcelWriter(output_path, engine="xlsxwriter") as writer:
    df.to_excel(writer, sheet_name="Mapping", index=False)

    wb = writer.book
    ws = writer.sheets["Mapping"]

    header_fmt = wb.add_format(
        {"bold": True, "bg_color": "#003366", "font_color": "white",
         "border": 1, "text_wrap": True}
    )
    cell_fmt = wb.add_format({"border": 1, "text_wrap": True})
    baten_fmt = wb.add_format({"border": 1, "bg_color": "#C8E6C9"})
    lasten_fmt = wb.add_format({"border": 1, "bg_color": "#FFCDD2"})
    neutraal_fmt = wb.add_format({"border": 1, "bg_color": "#FFF9C4"})

    for col_num, col_name in enumerate(df.columns):
        ws.write(0, col_num, col_name, header_fmt)

    for row_num, row in df.iterrows():
        fmt = cell_fmt
        if row["type"] == "baten":
            fmt = baten_fmt
        elif row["type"] == "lasten":
            fmt = lasten_fmt
        elif row["type"] == "neutraal":
            fmt = neutraal_fmt
        for col_num, val in enumerate(row):
            ws.write(row_num + 1, col_num, str(val) if val else "", fmt)

    ws.set_column(0, 0, 20)   # veld
    ws.set_column(1, 1, 40)   # patroon
    ws.set_column(2, 2, 30)   # categorie
    ws.set_column(3, 3, 25)   # subcategorie
    ws.set_column(4, 4, 12)   # type
    ws.set_column(5, 5, 20)   # project
    ws.set_column(6, 6, 12)   # grootboek
    ws.set_column(7, 7, 40)   # notitie

    # Instructietab
    ws_info = wb.add_worksheet("Instructies")
    ws_info.set_column(0, 0, 20)
    ws_info.set_column(1, 1, 60)
    info_header = wb.add_format({"bold": True, "bg_color": "#003366",
                                  "font_color": "white"})
    info_items = [
        ("Kolom", "Uitleg"),
        ("veld", "Welk veld te matchen: naam_tegenpartij / tegenrekening_iban / omschrijving / code / alle"),
        ("patroon", "Zoektekst of reguliere expressie (hoofdletterongevoelig). Bijv: 'salaris' of 'Salar.*2024'"),
        ("categorie", "Naam van de categorie, bijv. 'Personeelskosten' of 'Subsidies'"),
        ("subcategorie", "Optionele uitsplitsing binnen categorie"),
        ("type", "baten (inkomsten), lasten (uitgaven), of neutraal (interne overboekingen)"),
        ("project", "Optioneel: koppel aan een project/fonds"),
        ("grootboek", "Optioneel: grootboekrekeningnummer"),
        ("notitie", "Interne toelichting"),
        ("", ""),
        ("Volgorde", "Regels worden van boven naar beneden gecontroleerd. De EERSTE match wint."),
        ("Tip", "Zet specifieke regels bovenaan, algemene regels onderaan."),
        ("Tip", "Test je mapping door het dashboard te openen en de tab 'Transacties' te bekijken."),
    ]
    ws_info.write(0, 0, "Kolom", info_header)
    ws_info.write(0, 1, "Uitleg", info_header)
    for i, (col, uitleg) in enumerate(info_items[1:], start=1):
        ws_info.write(i, 0, col)
        ws_info.write(i, 1, uitleg)

# Maak ook een template-kopie
import shutil
shutil.copy(output_path, "data/mapping_template.xlsx")

print(f"Mapping aangemaakt: {output_path}")
print(f"Template aangemaakt: data/mapping_template.xlsx")
