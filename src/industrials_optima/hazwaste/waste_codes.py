"""Hazardous waste codes requiring incineration and their descriptions."""

# Waste codes that typically require incineration (cannot be landfilled)
# Based on EPA RCRA regulations - Land Disposal Restrictions (LDR)

INCINERATION_WASTE_CODES = [
    # D-Listed Characteristic Wastes requiring incineration
    "D001",  # Ignitable waste
    "D003",  # Reactive waste

    # F-Listed Wastes (from non-specific sources) - many require incineration
    "F001",  # Spent halogenated solvents
    "F002",  # Spent halogenated solvents
    "F003",  # Spent non-halogenated solvents
    "F004",  # Spent non-halogenated solvents
    "F005",  # Spent non-halogenated solvents
    "F020",  # Dioxin-bearing wastes
    "F021",  # Dioxin-bearing wastes
    "F022",  # Dioxin-bearing wastes
    "F023",  # Dioxin-bearing wastes
    "F026",  # Dioxin-bearing wastes
    "F027",  # Dioxin-bearing wastes
    "F028",  # Dioxin-bearing wastes

    # K-Listed Wastes (from specific industries) requiring incineration
    "K019",  # Heavy ends from distillation
    "K020",  # Heavy ends from distillation
    "K024",  # Distillation bottoms
    "K030",  # Column bottoms
    "K083",  # Distillation bottoms
    "K085",  # Distillation bottoms
    "K086",  # Solvent washes

    # P-Listed Acute Hazardous Wastes (many require incineration)
    "P001",  # Warfarin
    "P002",  # Acetaldehyde
    "P003",  # Acrolein
    "P004",  # Aldrin
    "P005",  # Allyl alcohol
    "P010",  # Arsenic acid
    "P011",  # Arsenic pentoxide
    "P012",  # Arsenic trioxide
    "P022",  # Carbon disulfide
    "P023",  # Chloroacetaldehyde
    "P024",  # p-Chloroaniline
    "P030",  # Cyanides
    "P031",  # Cyanogen
    "P033",  # Cyanogen chloride
    "P036",  # Dichlorophenylarsine
    "P037",  # Dieldrin
    "P048",  # 2,4-Dinitrophenol
    "P050",  # Endosulfan
    "P051",  # Endrin
    "P054",  # Ethyleneimine
    "P056",  # Fluorine
    "P057",  # Fluoroacetamide
    "P058",  # Fluoroacetic acid
    "P059",  # Heptachlor
    "P060",  # Isodrin
    "P063",  # Hydrogen cyanide
    "P064",  # Isocyanic acid
    "P065",  # Mercury fulminate
    "P066",  # Methomyl
    "P067",  # 2-Methylaziridine
    "P068",  # Methyl hydrazine
    "P069",  # 2-Methyllactonitrile
    "P070",  # Aldicarb
    "P071",  # Methyl parathion
    "P072",  # 1-Naphthyl-2-thiourea
    "P073",  # Nickel carbonyl
    "P074",  # Nickel cyanide
    "P075",  # Nicotine
    "P076",  # Nitric oxide
    "P077",  # p-Nitroaniline
    "P078",  # Nitrogen dioxide
    "P081",  # Nitroglycerin
    "P082",  # N-Nitrosodimethylamine
    "P084",  # N-Nitrosomethylvinylamine
    "P085",  # Octamethylpyrophosphoramide
    "P087",  # Osmium tetroxide
    "P088",  # Endothall
    "P089",  # Parathion
    "P092",  # Phenylmercury acetate
    "P093",  # Phenylthiourea
    "P094",  # Phorate
    "P095",  # Phosgene
    "P096",  # Phosphine
    "P097",  # Famphur
    "P098",  # Potassium cyanide
    "P099",  # Potassium silver cyanide
    "P101",  # Ethyl cyanide
    "P102",  # Propargyl alcohol
    "P103",  # Selenourea
    "P104",  # Silver cyanide
    "P105",  # Sodium azide
    "P106",  # Sodium cyanide
    "P108",  # Strychnine
    "P109",  # Tetraethyldithiopyrophosphate
    "P110",  # Tetraethyl lead
    "P111",  # Tetraethylpyrophosphate
    "P112",  # Tetranitromethane
    "P113",  # Thallic oxide
    "P114",  # Thallium selenite
    "P115",  # Thallium sulfate
    "P116",  # Thiosemicarbazide
    "P118",  # Trichloromethanethiol
    "P119",  # Ammonium vanadate
    "P120",  # Vanadium pentoxide
    "P121",  # Zinc cyanide
    "P122",  # Zinc phosphide
    "P123",  # Toxaphene

    # U-Listed Toxic Wastes commonly requiring incineration
    "U001",  # Acetaldehyde
    "U002",  # Acetone
    "U003",  # Acetonitrile
    "U004",  # Acetophenone
    "U006",  # Acetyl chloride
    "U007",  # Acrylamide
    "U008",  # Acrylic acid
    "U009",  # Acrylonitrile
    "U011",  # Amitrole
    "U012",  # Aniline
    "U014",  # Auramine
    "U019",  # Benzene
    "U020",  # Benzenesulfonyl chloride
    "U021",  # Benzidine
    "U022",  # Benzo(a)pyrene
    "U028",  # Bis(2-chloroisopropyl)ether
    "U029",  # Bromomethane
    "U030",  # 4-Bromophenyl phenyl ether
    "U031",  # n-Butyl alcohol
    "U032",  # Calcium chromate
    "U033",  # Carbon oxyfluoride
    "U034",  # Chloral
    "U035",  # Chlorambucil
    "U036",  # Chlordane
    "U037",  # Chlorobenzene
    "U041",  # Epichlorohydrin
    "U042",  # 2-Chloroethyl vinyl ether
    "U043",  # Vinyl chloride
    "U044",  # Chloroform
    "U045",  # Chloromethane
    "U046",  # Chloromethyl methyl ether
    "U047",  # 2-Chloronaphthalene
    "U048",  # 2-Chlorophenol
    "U051",  # Creosote
    "U052",  # Cresol
    "U053",  # Crotonaldehyde
    "U055",  # Cumene
    "U056",  # Cyclohexane
    "U057",  # Cyclohexanone
    "U058",  # Cyclophosphamide
    "U059",  # Daunomycin
    "U060",  # DDD
    "U061",  # DDT
    "U062",  # Diallate
    "U063",  # Dibenz(a,h)anthracene
    "U064",  # Dibenzo(a,i)pyrene
    "U066",  # 1,2-Dibromo-3-chloropropane
    "U067",  # Ethylene dibromide
    "U068",  # Methylene bromide
    "U069",  # Dibutyl phthalate
    "U070",  # o-Dichlorobenzene
    "U071",  # m-Dichlorobenzene
    "U072",  # p-Dichlorobenzene
    "U073",  # 3,3'-Dichlorobenzidine
    "U074",  # 1,4-Dichloro-2-butene
    "U075",  # Dichlorodifluoromethane
    "U076",  # 1,1-Dichloroethane
    "U077",  # 1,2-Dichloroethane
    "U078",  # 1,1-Dichloroethylene
    "U079",  # 1,2-Dichloroethylene
    "U080",  # Methylene chloride
    "U081",  # 2,4-Dichlorophenol
    "U082",  # 2,6-Dichlorophenol
    "U083",  # 1,2-Dichloropropane
    "U084",  # 1,3-Dichloropropene
    "U085",  # 1,2:3,4-Diepoxybutane
    "U086",  # N,N-Diethylhydrazine
    "U087",  # O,O-Diethyl S-methyl dithiophosphate
    "U088",  # Diethyl phthalate
    "U089",  # Diethylstilbestrol
    "U090",  # Dihydrosafrole
    "U091",  # 3,3'-Dimethoxybenzidine
    "U092",  # Dimethylamine
    "U093",  # p-Dimethylaminoazobenzene
    "U094",  # 7,12-Dimethylbenz(a)anthracene
    "U095",  # 3,3'-Dimethylbenzidine
    "U096",  # alpha,alpha-Dimethylbenzyl hydroperoxide
    "U097",  # Dimethylcarbamoyl chloride
    "U098",  # 1,1-Dimethylhydrazine
    "U099",  # 1,2-Dimethylhydrazine
    "U101",  # 2,4-Dimethylphenol
    "U102",  # Dimethyl phthalate
    "U103",  # Dimethyl sulfate
    "U105",  # 2,4-Dinitrotoluene
    "U106",  # 2,6-Dinitrotoluene
    "U107",  # Di-n-octyl phthalate
    "U108",  # 1,4-Dioxane
    "U109",  # 1,2-Diphenylhydrazine
    "U110",  # Dipropylamine
    "U111",  # Di-n-propylnitrosamine
    "U112",  # Ethyl acetate
    "U113",  # Ethyl acrylate
    "U114",  # Ethylenebisdithiocarbamic acid
    "U115",  # Ethylene oxide
    "U116",  # Ethylene thiourea
    "U117",  # Ethyl ether
    "U118",  # Ethyl methacrylate
    "U119",  # Ethyl methanesulfonate
    "U120",  # Fluoranthene
    "U121",  # Trichloromonofluoromethane
    "U122",  # Formaldehyde
    "U123",  # Formic acid
    "U124",  # Furan
    "U125",  # Furfural
    "U126",  # Glycidylaldehyde
    "U127",  # Hexachlorobenzene
    "U128",  # Hexachlorobutadiene
    "U129",  # Lindane
    "U130",  # Hexachlorocyclopentadiene
    "U131",  # Hexachloroethane
    "U132",  # Hexachlorophene
    "U133",  # Hydrazine
    "U134",  # Hydrogen fluoride
    "U135",  # Hydrogen sulfide
    "U136",  # Cacodylic acid
    "U137",  # Indeno(1,2,3-cd)pyrene
    "U138",  # Iodomethane
    "U140",  # Isobutyl alcohol
    "U141",  # Isosafrole
    "U142",  # Kepone
    "U143",  # Lasiocarpine
    "U144",  # Lead acetate
    "U145",  # Lead phosphate
    "U146",  # Lead subacetate
    "U147",  # Maleic anhydride
    "U148",  # Maleic hydrazide
    "U149",  # Malononitrile
    "U150",  # Melphalan
    "U151",  # Mercury
    "U152",  # Methacrylonitrile
    "U153",  # Methanethiol
    "U154",  # Methanol
    "U155",  # Methapyrilene
    "U156",  # Methyl chlorocarbonate
    "U157",  # 3-Methylcholanthrene
    "U158",  # 4,4'-Methylenebis(2-chloroaniline)
    "U159",  # Methyl ethyl ketone
    "U160",  # Methyl ethyl ketone peroxide
    "U161",  # Methyl isobutyl ketone
    "U162",  # Methyl methacrylate
    "U163",  # N-Methyl-N'-nitro-N-nitrosoguanidine
    "U164",  # Methylthiouracil
    "U165",  # Naphthalene
    "U166",  # 1,4-Naphthoquinone
    "U167",  # 1-Naphthylamine
    "U168",  # 2-Naphthylamine
    "U169",  # Nitrobenzene
    "U170",  # p-Nitrophenol
    "U171",  # 2-Nitropropane
    "U172",  # N-Nitrosodi-n-butylamine
    "U173",  # N-Nitrosodiethanolamine
    "U174",  # N-Nitrosodiethylamine
    "U176",  # N-Nitroso-N-ethylurea
    "U177",  # N-Nitroso-N-methylurea
    "U178",  # N-Nitroso-N-methylurethane
    "U179",  # N-Nitrosopiperidine
    "U180",  # N-Nitrosopyrrolidine
    "U181",  # 5-Nitro-o-toluidine
    "U182",  # Paraldehyde
    "U183",  # Pentachlorobenzene
    "U184",  # Pentachloroethane
    "U185",  # Pentachloronitrobenzene
    "U186",  # 1,3-Pentadiene
    "U187",  # Phenacetin
    "U188",  # Phenol
    "U189",  # Phosphorus sulfide
    "U190",  # Phthalic anhydride
    "U191",  # 2-Picoline
    "U192",  # Pronamide
    "U193",  # 1,3-Propane sultone
    "U194",  # n-Propylamine
    "U196",  # Pyridine
    "U197",  # p-Benzoquinone
    "U200",  # Reserpine
    "U201",  # Resorcinol
    "U202",  # Saccharin
    "U203",  # Safrole
    "U204",  # Selenious acid
    "U205",  # Selenium disulfide
    "U206",  # Streptozotocin
    "U207",  # 1,2,4,5-Tetrachlorobenzene
    "U208",  # 1,1,1,2-Tetrachloroethane
    "U209",  # 1,1,2,2-Tetrachloroethane
    "U210",  # Tetrachloroethylene
    "U211",  # Carbon tetrachloride
    "U213",  # Tetrahydrofuran
    "U214",  # Thallium acetate
    "U215",  # Thallium carbonate
    "U216",  # Thallium chloride
    "U217",  # Thallium nitrate
    "U218",  # Thioacetamide
    "U219",  # Thiourea
    "U220",  # Toluene
    "U221",  # Toluenediamine
    "U223",  # Toluene diisocyanate
    "U225",  # Bromoform
    "U226",  # 1,1,1-Trichloroethane
    "U227",  # 1,1,2-Trichloroethane
    "U228",  # Trichloroethylene
    "U234",  # 1,3,5-Trinitrobenzene
    "U235",  # tris(2,3-Dibromopropyl)phosphate
    "U236",  # Trypan blue
    "U237",  # Uracil mustard
    "U238",  # Urethane
    "U239",  # Xylene
    "U240",  # 2,4-D
    "U243",  # Hexachloropropene
    "U244",  # Thiram
    "U246",  # Cyanogen bromide
    "U247",  # Methoxychlor
    "U248",  # Warfarin
    "U249",  # Zinc phosphide
]

# Waste codes that can go to landfill (with treatment)
LANDFILL_WASTE_CODES = [
    "D002",  # Corrosive waste
    "D004",  # Arsenic
    "D005",  # Barium
    "D006",  # Cadmium
    "D007",  # Chromium
    "D008",  # Lead
    "D009",  # Mercury
    "D010",  # Selenium
    "D011",  # Silver
    "D012",  # Endrin
    "D013",  # Lindane
    "D014",  # Methoxychlor
    "D015",  # Toxaphene
    "D016",  # 2,4-D
    "D017",  # 2,4,5-TP (Silvex)
    "D018",  # Benzene
    "D019",  # Carbon tetrachloride
    "D020",  # Chlordane
    "D021",  # Chlorobenzene
    "D022",  # Chloroform
    "D023",  # o-Cresol
    "D024",  # m-Cresol
    "D025",  # p-Cresol
    "D026",  # Cresol
    "D027",  # 1,4-Dichlorobenzene
    "D028",  # 1,2-Dichloroethane
    "D029",  # 1,1-Dichloroethylene
    "D030",  # 2,4-Dinitrotoluene
    "D031",  # Heptachlor
    "D032",  # Hexachlorobenzene
    "D033",  # Hexachlorobutadiene
    "D034",  # Hexachloroethane
    "D035",  # Methyl ethyl ketone
    "D036",  # Nitrobenzene
    "D037",  # Pentachlorophenol
    "D038",  # Pyridine
    "D039",  # Tetrachloroethylene
    "D040",  # Trichloroethylene
    "D041",  # 2,4,5-Trichlorophenol
    "D042",  # 2,4,6-Trichlorophenol
    "D043",  # Vinyl chloride
]

# Descriptions for common waste codes
WASTE_CODE_DESCRIPTIONS = {
    "D001": "Ignitable Waste",
    "D002": "Corrosive Waste",
    "D003": "Reactive Waste",
    "D004": "Arsenic",
    "D005": "Barium",
    "D006": "Cadmium",
    "D007": "Chromium",
    "D008": "Lead",
    "D009": "Mercury",
    "D010": "Selenium",
    "D011": "Silver",
    "F001": "Spent Halogenated Solvents (Tetrachloroethylene, etc.)",
    "F002": "Spent Halogenated Solvents (Chlorobenzene, etc.)",
    "F003": "Spent Non-halogenated Solvents (Xylene, etc.)",
    "F004": "Spent Non-halogenated Solvents (Cresols, etc.)",
    "F005": "Spent Non-halogenated Solvents (Benzene, etc.)",
    "F006": "Electroplating Wastewater Sludge",
    "F007": "Spent Cyanide Plating Solutions",
    "F008": "Plating Bath Residues from Cyanide Plating",
    "F009": "Spent Stripping Solutions from Electroplating",
    "F010": "Quenching Bath Residues",
    "F011": "Spent Cyanide Solutions from Metal Heat Treating",
    "F012": "Quenching Wastewater Treatment Sludges",
    "F019": "Wastewater Treatment Sludge from Chemical Conversion Coating",
    "F020": "Wastes from Production of Tri/Pentachlorophenol (Dioxin)",
    "F021": "Wastes from Production of Tri/Pentachlorophenol (Dioxin)",
    "F022": "Wastes from Production of Tri/Pentachlorophenol (Dioxin)",
    "F023": "Wastes from Production of Tri/Pentachlorophenol (Dioxin)",
    "F024": "Wastes from Chlorinated Aliphatic Production",
    "F025": "Condensed Light Ends from Chlorinated Aliphatic Production",
    "F026": "Wastes from Production of Materials on Dioxin List",
    "F027": "Discarded Formulations Containing Tri/Pentachlorophenol",
    "F028": "Residues from Incineration of Dioxin-Containing Wastes",
    "K001": "Bottom Sediment Sludge from Wood Preserving",
    "K048": "Dissolved Air Flotation Float from Petroleum Refining",
    "K049": "Slop Oil Emulsion Solids from Petroleum Refining",
    "K050": "Heat Exchanger Bundle Cleaning Sludge from Petroleum Refining",
    "K051": "API Separator Sludge from Petroleum Refining",
    "K052": "Tank Bottoms from Petroleum Refining",
}


def get_waste_code_info(code: str) -> dict:
    """Get information about a waste code."""
    is_incineration = code in INCINERATION_WASTE_CODES
    is_landfill = code in LANDFILL_WASTE_CODES
    description = WASTE_CODE_DESCRIPTIONS.get(code, f"Waste Code {code}")

    disposal_methods = []
    if is_incineration:
        disposal_methods.append("Incineration")
    if is_landfill:
        disposal_methods.append("Landfill (with treatment)")
    if not disposal_methods:
        disposal_methods.append("Various (consult regulations)")

    return {
        "code": code,
        "description": description,
        "requires_incineration": is_incineration and not is_landfill,
        "can_landfill": is_landfill,
        "disposal_methods": disposal_methods,
    }
