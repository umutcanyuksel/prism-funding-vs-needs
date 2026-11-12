"""DG ECHO's Forgotten Crisis Assessment lists, 2021-2026, one row per crisis.

Transcribed from the General Guidelines on Operational Priorities for
Humanitarian Aid (GGOPHA), Commission staff working documents:
  2021 SWD(2020) 253, 2022 SWD(2021) 312, 2023 SWD(2022) 352,
  2024 SWD(2023) 354, 2025 SWD(2024) 257;
2026 from DG ECHO's forgotten-crises page (last updated 7 October 2025).
Crisis names are kept as ECHO wrote them; iso3 maps each to countries and
mapping_note records the judgement calls.
"""
import csv

from common import RAW

L = {
2021: [("Afghanistan regional crisis (incl. Afghan refugees in Iran and Pakistan)", "AFG IRN PAK"),
       ("Myanmar: conflict and displacement in Kachin and Northern Shan States", "MMR"),
       ("Pakistan food crisis", "PAK"), ("Philippines: armed conflict in Mindanao", "PHL"),
       ("Rohingya regional crisis", "BGD MMR"), ("Sahrawi refugees in Algeria", "DZA"),
       ("Burundi regional refugee crisis", "BDI"), ("Central African Republic regional crisis (CAR, Cameroon, Chad)", "CAF CMR TCD"),
       ("Conflicts and violence in the Sahel (Burkina Faso, Mali, Mauritania, Niger)", "BFA MLI MRT NER"),
       ("Conflict and violence in the North West/South West regions of Cameroon", "CMR"),
       ("Sudan: food and nutrition crises, internal conflict", "SDN"), ("Southern Africa regional crisis", ""),
       ("Colombia: internal armed conflict", "COL"), ("Haiti: food and nutrition crisis", "HTI"),
       ("Central America: Food insecurity and violence (El Salvador, Guatemala, Honduras, Mexico)", "SLV GTM HND MEX"),
       ("Venezuelan and Haitian refugee crisis in the Caribbean", ""), ("Conflict in Ukraine", "UKR")],
2022: [("Cameroon: Conflict and violence in the north-west/south-west regions", "CMR"),
       ("Central African Republic (CAR) regional crisis (CAR, Cameroon, Chad)", "CAF CMR TCD"),
       ("Democratic Republic of the Congo: Complex crisis", "COD"), ("Burundi: regional Refugee crisis", "BDI"),
       ("South Sudan", "SSD"), ("Madagascar: Drought", "MDG"), ("Algeria: Sahrawi Crisis", "DZA"), ("Somalia", "SOM"),
       ("Pakistan: Food crisis", "PAK"), ("Myanmar: Conflict and displacement in Kachin and Northern Shan States", "MMR"),
       ("Rohingya regional crisis", "BGD MMR"), ("Philippines: Armed conflict in Mindanao", "PHL"),
       ("Colombia: Internal armed conflict", "COL"), ("Haiti", "HTI"),
       ("Central America: Food insecurity and violence (El Salvador, Guatemala, Honduras, Mexico)", "SLV GTM HND MEX"),
       ("Ukraine: Conflict", "UKR")],
2023: [("Complex crisis in DRC", "COD"), ("Complex crisis in Cameroon", "CMR"), ("Complex crisis in Burundi", "BDI"),
       ("Complex crisis in South Sudan", "SSD"), ("Violence West Darfur", "SDN"),
       ("Complex crisis in Central African Republic (CAR)", "CAF"), ("Refugee crisis in Sudan", "SDN"),
       ("CAR refugees in Chad", "TCD"), ("Northwest banditry in Nigeria", "NGA"), ("Saharawi crisis in Algeria", "DZA"),
       ("Rohingya refugee crisis in Bangladesh", "BGD"), ("Socio-economic crisis in Lebanon", "LBN"),
       ("Displacement of Venezuelans in Ecuador", "ECU"), ("Displacement of Venezuelans in Peru", "PER"),
       ("Complex crisis in Colombia", "COL")],
2024: [("Complex crisis in DRC", "COD"), ("Displacement crisis in Uganda", "UGA"), ("Conflict in Burkina Faso", "BFA"),
       ("Crisis in Northwest and Southwest regions of Cameroon", "CMR"), ("Banditry and intercommunity violence in Northwest Nigeria", "NGA"),
       ("Complex crisis in South Sudan", "SSD"), ("Complex crisis in Mali", "MLI"), ("Sahrawi crisis in Algeria", "DZA"),
       ("Rohingya refugee crisis in Bangladesh", "BGD"), ("Complex crisis in Myanmar (including displacement crisis in the region)", "MMR"),
       ("Conflict in Philippines - Mindanao", "PHL"), ("Multiple crises in Iraq", "IRQ"), ("Socio-economic crisis in Lebanon", "LBN"),
       ("Complex crisis in Haiti", "HTI"), ("Multiple crises in Central America", "SLV GTM HND")],
2025: [("Sahrawi refugees in Algeria", "DZA"), ("Conflict in Burkina Faso", "BFA"), ("Complex crisis in Burundi", "BDI"),
       ("Multiple crises in Cameroon", "CMR"), ("Complex crisis in DRC", "COD"),
       ("Multiple crises in Mozambique (incl. Cabo Delgado insurgency)", "MOZ"), ("Crisis in Northwest Nigeria", "NGA"),
       ("Complex crisis in South Sudan", "SSD"), ("Displacement in Uganda", "UGA"), ("Multiple crises in Iraq", "IRQ"),
       ("Syrian refugees in Jordan", "JOR"), ("Socio-economic crisis in Lebanon", "LBN"), ("Mindanao conflict in Philippines", "PHL"),
       ("Conflict in Yemen", "YEM"), ("Complex crisis in Colombia", "COL"), ("Complex crisis in Honduras", "HND"),
       ("Multiple crises in Mexico", "MEX"), ("Complex crisis in Venezuela", "VEN")],
2026: [("Complex crisis in Afghanistan", "AFG"), ("Sahrawi refugees in Algeria", "DZA"), ("Rohingya refugee crisis", "BGD"),
       ("Complex crisis in Burundi", "BDI"), ("Multiple crises in Cameroon", "CMR"), ("Complex crisis in CAR", "CAF"),
       ("Complex crisis in CAM (Guatemala, El Salvador, Honduras)", "GTM SLV HND"),
       ("Complex crisis in Central Sahel (Mali, Niger and Burkina Faso)", "MLI NER BFA"),
       ("Complex crisis in Colombia and Venezuela displacement in Colombia", "COL"), ("Complex crisis in Haiti", "HTI"),
       ("Multiple crises (Conflict and Syrian and Palestinian refugees in Iraq)", "IRQ"), ("Syrian refugees in Jordan", "JOR"),
       ("Mixed migration flows in Libya", "LBY"), ("Cabo Delgado Islamist Insurgency", "MOZ"), ("Mindanao conflict", "PHL"),
       ("Complex crisis in Somalia", "SOM"), ("Complex crisis in South Sudan", "SSD"), ("Refugee crisis - International displacement", "UGA"),
       ("Venezuela Complex crisis", "VEN"), ("Conflict in Yemen", "YEM")],
}
SRC = {2021: "SWD(2020) 253", 2022: "SWD(2021) 312", 2023: "SWD(2022) 352", 2024: "SWD(2023) 354", 2025: "SWD(2024) 257",
       2026: "DG ECHO forgotten crises page, updated 7 Oct 2025"}
NOTE = {"Southern Africa regional crisis": "countries not named; not mapped",
        "Venezuelan and Haitian refugee crisis in the Caribbean": "countries not named; not mapped",
        "Multiple crises in Central America": "countries not named in 2024; mapped to the three named in 2021, 2022 and 2026 (Mexico left out)",
        "Burundi regional refugee crisis": "host countries not named; mapped to Burundi",
        "Burundi: regional Refugee crisis": "host countries not named; mapped to Burundi"}
with open(RAW / "echo_forgotten_crises_2021_2026.csv", "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["year", "crisis_name", "iso3", "source", "mapping_note"])
    for y, items in L.items():
        for name, iso in items:
            w.writerow([y, name, iso, SRC[y], NOTE.get(name, "")])
print(sum(len(v) for v in L.values()), "crises")
