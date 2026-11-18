# Dota 2 patch 7.42 forklaret

Uofficiel forklaring på dansk af Dota 2-patchen 7.42. Siden viser de store ændringer med gammel værdi (rød, overstreget) og ny værdi (grøn) side om side, har små forsøg man kan prøve selv, og et opslag med alle helte, items, neutrale items, enchantments og creeps.

Alle tal kommer fra Valves officielle noter: https://www.dota2.com/patches/7.42

Længere beskrivelser, især af nye evner, er ikke kopieret ind. Tal og korte udsagn er med, og opslaget linker til Valves noter for resten.

## Kør lokalt

Siden er statisk HTML, CSS og JavaScript uden build.

```
python3 -m http.server 8000
```

Åbn derefter http://localhost:8000.

## Opbygning

- `index.html` - siden. Genereret af `tools/build_pages.py`.
- `styles.css`, `app.js` - udseende og de små værktøjer samt opslaget.
- `data.js` - alle helte, items, neutrale items, enchantments og creeps som data. Genereret af `tools/parse_notes.py`.
- `fonts/` - Archivo (SIL Open Font License).

## Opdatér data

Gem Valves noter som en tekstfil, og kør:

```
python3 tools/parse_notes.py noter.txt data.js
python3 tools/build_pages.py .
```

Teksterne i de forklarende afsnit står i `tools/build_pages.py`. Notefilen er ikke med i repoet.

## Udgiv som GitHub Pages

Settings, Pages, Deploy from a branch, vælg `main` og `/ (root)`.
