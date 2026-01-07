# Affaldshafhentning til Home Assistant

En simpel integration til at holde styr på dine skraldetømninger i Danmark. Denne integration beregner næste afhentningsdato baseret på dine intervaller og referenceuger, og viser pæne piktogrammer fra [affaldspiktogrammer.dk](https://www.affaldspiktogrammer.dk/).

## Funktioner
- 📅 Beregner næste tømning ud fra frekvens (f.eks. hver 2. uge).
- 🖼️ Viser officielle danske affaldspiktogrammer.
- 🔔 Automatisering klar: Attributter for `is_today` og `is_tomorrow`.
- 🛠️ Manuel overstyring af datoer (perfekt til helligdage).
- 🇩🇰 Dansksproget opsætning.

## Installation

### Via HACS (Anbefalet)
1. Gå til **HACS** i din Home Assistant.
2. Klik på de tre prikker i øverste højre hjørne og vælg **Custom repositories**.
3. Tilføj dette repository URL og vælg kategorien **Integration**.
4. Klik på **Install**.
5. Genstart Home Assistant.

### Manuel installation
1. Kopier mappen `custom_components/affaldshafhentning` til din `/config/custom_components/` mappe.
2. Genstart Home Assistant.

## Opsætning
1. Gå til **Indstillinger -> Enheder og tjenester**.
2. Klik på **Tilføj integration** og søg efter **Affaldshafhentning**.
3. Indtast dine detaljer (Type, dag, uge-interval og startuge).

## Automatisering (Notifikationer)
Integrationen gør det nemt at få besked, når det er tid til at sætte skraldespanden ud. Hver sensor har attributterne `is_today` og `is_tomorrow`.

**Eksempel på automatisering (besked dagen før):**
```yaml
alias: "Besked: Husk madaffald"
trigger:
  - platform: state
    entity_id: sensor.madaffald
    attribute: is_tomorrow
    to: true
condition:
  - condition: time
    after: "19:00:00" # Giv besked kl 19 aftenen før
action:
  - service: notify.mobile_app_din_telefon
    data:
      title: "Skraldebilen kommer i morgen!"
      message: "Husk at sætte madaffald ud til vejen."
```

## Håndtering af Helligdage
Hvis en afhentning flyttes pga. en helligdag, kan du nemt rette det:
1. Gå til integrationen under **Enheder og tjenester**.
2. Klik på **Konfigurer** på den ønskede affaldstype.
3. I feltet **Dato-flytninger** skriver du den gamle dato og den nye dato adskilt af kolon.
   - Format: `YYYY-MM-DD:YYYY-MM-DD`
   - Eksempel: `2024-12-24:2024-12-27` (flytter tømning fra juleaften til 27. dec).
   - Du kan tilføje flere ved at adskille dem med komma: `dato1:dato1_ny, dato2:dato2_ny`.

## Piktogrammer
Integrationen kigger efter nøgleord i din "Affaldstype" for at vælge det rigtige billede.
- **Madaffald**: Indeholder "mad"
- **Restaffald**: Indeholder "rest"
- **Plast**: Indeholder "plast"
- **Papir**: Indeholder "papir"
- **Pap**: Indeholder "pap"
- **Metal**: Indeholder "metal"
- **Glas**: Indeholder "glas"
- **Tekstil**: Indeholder "tekstil"
- **Karton**: Indeholder "karton"
- **Farligt**: Indeholder "farligt"
- **Hård plast**: Indeholder "hård plast"
- **Blød plast**: Indeholder "blød plast"
