#!/usr/bin/env python3
"""Writes index.html for the 7.42 explainer from curated copy + data.js (parsed from Valve's notes)."""
import html, json, re, sys

REPO = sys.argv[1] if len(sys.argv) > 1 else "/home/claude/dota_patchnotes"
src = open(f"{REPO}/data.js", encoding="utf-8").read()
D = json.loads(src[len("window.PATCH="):].rstrip().rstrip(";"))
old_index = open(f"{REPO}/index.html", encoding="utf-8").read()

e = html.escape


def dk(n):
    """Danish thousands separator."""
    return f"{n:,}".replace(",", ".")


def vals(old, new, text=False):
    if old is None and new is None:
        return ""
    if old is None:
        return f'<span class="sr">Nu: </span><ins>{e(new)}</ins>'
    return f'<span class="sr">Før: </span><del>{e(old)}</del><span class="sr"> Nu: </span><ins>{e(new)}</ins>'


def row(label, old=None, new=None, text="", link=None, as_text=False, extra=""):
    k = f'<a href="{link}">{e(label)}</a>' if link else e(label)
    cls = "diff__v diff__v--text" if as_text else "diff__v"
    return (
        '        <li class="diff__row">\n'
        f'          <div class="diff__k">{k}</div>\n'
        f'          <div class="{cls}">{extra}{vals(old, new)}</div>\n'
        f'          <p class="diff__p">{text}</p>\n'
        "        </li>\n"
    )


def rows(*rs):
    return '      <ul class="diff">\n' + "".join(rs) + "      </ul>\n"


def facts(items):
    out = '      <ul class="facts">\n'
    for label, text, link in items:
        k = f'<a href="{link}" data-hero="{e(label)}">{e(label)}</a>' if link else e(label)
        out += f'        <li class="facts__row"><div class="facts__k">{k}</div><p class="facts__p">{text}</p></li>\n'
    return out + "      </ul>\n"


def section(id_, title, lede, body):
    return (
        f'  <section class="sec" id="{id_}">\n    <div class="wrap">\n'
        f'      <h2 class="sec__title">{title}</h2>\n'
        f'      <p class="sec__lede">{lede}</p>\n\n{body}'
        "    </div>\n  </section>\n\n"
    )


# ---------- data-driven pieces ----------
items = {i["n"]: i for i in D["items"]}
illusion_items = []
for i in D["items"]:
    if any("x" in l and re.search(r"illusion", l["x"], re.I) and "works with illusions" in l["x"] for l in i["ls"]):
        illusion_items.append(i["n"])
removed = [i["n"] for i in D["items"] if any(l.get("x") == "Item removed from the game" for l in i["ls"])]
recipe_changed = [i["n"] for i in D["items"] if any(l.get("x") == "Recipe changed" for l in i["ls"])]
new_items = [i["n"] for i in D["items"] if any(l.get("x") == "New Item" for l in i["ls"])]
art_out = [a["n"] for a in D["artifacts"] if any(l.get("x") == "Item Cycled Out" for l in a["ls"])]
art_new = [(a["n"], l["x"]) for a in D["artifacts"] for l in a["ls"] if re.match(r"New Tier \d Artifact", l.get("x", ""))]
print("illusion items:", illusion_items)
print("removed:", removed, "| recipe changed:", len(recipe_changed), "| new:", new_items)
print("artifacts out:", len(art_out), art_out, "| new:", art_new)

# ---------- charts ----------
SCALE = 200


def dumb(label, lo, hi, new):
    a = lo / SCALE * 100
    w = max((hi - lo) / SCALE * 100, 0.9)
    mid = (lo + hi) / 2 / SCALE * 100
    n = new / SCALE * 100
    l, r = min(mid, n), max(mid, n)
    old_txt = f"{lo}" if lo == hi else f"{lo}-{hi}"
    return (
        '        <li class="dumb__row">\n'
        f'          <span class="dumb__k">{e(label)}</span>\n'
        '          <span class="dumb__plot" aria-hidden="true">'
        f'<span class="dumb__link" style="left:{l:.2f}%;width:{r - l:.2f}%"></span>'
        f'<span class="dumb__old" style="left:{a:.2f}%;width:{w:.2f}%"></span>'
        f'<span class="dumb__new" style="left:{n:.2f}%"></span></span>\n'
        f'          <span class="dumb__v"><span class="sr">Før: </span><del>{old_txt}</del><span class="sr"> Nu: </span><ins>{new}</ins></span>\n'
        "        </li>\n"
    )


def dumb_chart(title, data, hint):
    axis = "".join(f'<span style="left:{v / SCALE * 100}%">{v}</span>' for v in (0, 50, 100, 150, 200))
    return (
        f'      <h3 class="sec__sub">{title}</h3>\n'
        f'      <p class="caption caption--top">{hint}</p>\n'
        '      <div class="dumb">\n'
        f'        <div class="dumb__axis" aria-hidden="true"><span></span><span class="dumb__scale">{axis}</span><span></span></div>\n'
        '        <ul class="dumb__list">\n' + "".join(dumb(*d) for d in data) + "        </ul>\n      </div>\n"
    )


last_hit = [
    ("Tier 1-tårn", 110, 130, 100),
    ("Tier 2-tårn", 130, 150, 125),
    ("Tier 3-tårn", 150, 170, 150),
    ("Tier 4-tårn", 170, 190, 175),
    ("Barakker", 90, 135, 100),
]
per_player = [
    ("Tier 1-tårn", 90, 90, 75),
    ("Tier 2-tårn", 110, 110, 100),
    ("Tier 4-tårn", 145, 145, 150),
    ("Melee-barakker", 155, 155, 125),
    ("Ranged-barakker", 90, 90, 100),
    ("Roshan", 135, 135, 125),
]

# price bars
prices = D["prices"]
maxd = max(abs(p["b"] - p["a"]) for p in prices)
price_rows = ""
for p in prices:
    d = p["b"] - p["a"]
    price_rows += (
        '        <li class="hbar__row">\n'
        f'          <span class="hbar__k">{e(p["n"])}</span>\n'
        f'          <span class="hbar__track" aria-hidden="true"><span class="hbar__fill" style="width:{abs(d) / maxd * 100:.1f}%"></span></span>\n'
        f'          <span class="hbar__v"><span class="sr">Før: </span><del>{dk(p["a"])}</del><span class="sr"> Nu: </span><ins>{dk(p["b"])}</ins></span>\n'
        "        </li>\n"
    )

# most changed heroes
top = sorted(D["heroes"], key=lambda h: -h["c"])[:10]
topmax = top[0]["c"]
top_rows = ""
for h in top:
    top_rows += (
        '        <li class="hbar__row">\n'
        f'          <a class="hbar__k" href="#slaa-op" data-hero="{e(h["n"])}">{e(h["n"])}</a>\n'
        f'          <span class="hbar__track" aria-hidden="true"><span class="hbar__fill hbar__fill--ink" style="width:{h["c"] / topmax * 100:.1f}%"></span></span>\n'
        f'          <span class="hbar__v">{h["c"]}</span>\n'
        "        </li>\n"
    )

# neutral pools grid
pools = ""
for tier, plist in D["pools"].items():
    n = tier.split()[1]
    pools += f'        <div class="pools__col"><h4 class="pools__h">Tier {n}</h4><ul>'
    pools += "".join(f"<li>{e(', '.join(p))}</li>" for p in plist)
    pools += "</ul></div>\n"

# fixes block from the previous build, minus the old source dots
m = re.search(r'<ul class="fixes" id="fixes">.*?</ul>', old_index, re.S)
fixes = m.group(0).replace('<span class="dot dot--valve"></span>', "")

n_heroes = len(D["heroes"])
n_items = len(D["items"])
n_art = len(D["artifacts"])

# ---------- page ----------
head = f"""<!doctype html>
<html lang="da">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Dota 2 patch 7.42 forklaret</title>
  <meta name="description" content="Dota 2 patch 7.42 på dansk: de store ændringer med gammel og ny værdi side om side, små forsøg du kan prøve selv, og alle helte og items til opslag.">
  <meta name="color-scheme" content="light dark">
  <meta property="og:title" content="Dota 2 patch 7.42 forklaret">
  <meta property="og:description" content="Tormentor, illusioner, guld, items og alle {n_heroes} helte. Gammel og ny værdi side om side.">
  <meta property="og:type" content="website">
  <link rel="icon" href="favicon.svg" type="image/svg+xml">
  <link rel="preload" href="fonts/archivo-wdth.woff2" as="font" type="font/woff2" crossorigin>
  <link rel="stylesheet" href="styles.css">
</head>
<body>

<header class="top">
  <div class="wrap top__in">
    <a class="top__brand" href="#top">Patch 7.42</a>
    <nav class="top__nav" aria-label="Sektioner">
      <a href="#tormentor">Tormentor</a>
      <a href="#illusioner">Illusioner</a>
      <a href="#helte">Helte</a>
      <a href="#guld">Guld</a>
      <a href="#kort">Kort</a>
      <a href="#neutrale">Neutrale</a>
      <a href="#items">Items</a>
      <a href="#slaa-op">Slå op</a>
      <a href="#rettelser">Rettelser</a>
    </nav>
  </div>
</header>

<main id="top">

  <section class="hero">
    <div class="wrap">
      <h1 class="hero__title">Patch 7.42</h1>
      <p class="hero__lede">Valve udgav Dota 2-patchen den 18. november 2026. Den rører alle {n_heroes} helte, {n_items} items og {n_art} neutrale items. Her er de ændringer, der flytter mest, med gammel og ny værdi side om side. Nederst kan du slå alt op.</p>

      <div class="ruler" role="group" aria-label="En kamp i minutter, med tre ændringer placeret hvor de sker">
        <div class="ruler__track"></div>
        <span class="tick tick--first" style="--t:0">0</span>
        <span class="tick tick--minor" style="--t:5"></span>
        <span class="tick" style="--t:10">10</span>
        <span class="tick tick--minor" style="--t:15"></span>
        <span class="tick" style="--t:20">20</span>
        <span class="tick tick--minor" style="--t:25"></span>
        <span class="tick" style="--t:30">30</span>
        <span class="tick tick--minor" style="--t:35"></span>
        <span class="tick" style="--t:40">40</span>
        <span class="tick tick--minor" style="--t:45"></span>
        <span class="tick tick--last" style="--t:50">50 min</span>

        <span class="ruler__ghost" title="Før: Tormentor efter 20 min"><span class="ruler__ghost-label">20 min</span></span>

        <a class="mark" href="#guld" style="--t:0; --h:196">
          <span class="mark__label">
            <span class="mark__name">Starthorn</span>
            <span class="mark__note">Passiv XP: 50 i minuttet</span>
          </span>
        </a>
        <a class="mark mark--move" id="mark-tormentor" href="#tormentor" style="--t:15; --h:132">
          <span class="mark__label">
            <span class="mark__name">Tormentor</span>
            <span class="mark__note">Nu efter 15 min, før efter 20</span>
          </span>
        </a>
        <a class="mark mark--end" href="#neutrale" style="--t:50; --h:68">
          <span class="mark__label">
            <span class="mark__name">Sidste neutral tier</span>
            <span class="mark__note">Åbner efter 50 min</span>
          </span>
        </a>
      </div>
    </div>
  </section>

"""


body = ""

# ---- Kort fortalt
body += section(
    "oversigt",
    "Kort fortalt",
    "Fem ændringer, der sætter tonen. Rød og overstreget er det gamle, grøn er det nye.",
    rows(
        row("Første Tormentor", "20 min", "15 min", "Objektivet åbner fem minutter tidligere og kan dermed påvirke kampen i midtspillet.", "#tormentor"),
        row("Basisliv for helte", "120", "200", "Alle helte starter med mere liv. Til gengæld giver Strength lidt mindre liv pr. point.", "#helte"),
        row("Illusioners Item Potency", None, "20%", "Illusioner kan nu bruge de fleste on-hit-effekter fra items, men med en femtedel af styrken.", "#illusioner"),
        row("Spell damage", None, "Mindre skade", "De fleste Magic- og Pure-spells gør mindre skade. Intelligence giver til gengæld lidt mere magic resistance.", "#helte", as_text=True),
        row("Neutrale tiers", "5", "4", "Neutrale items har fire tiers i stedet for fem. Den sidste åbner efter 50 minutter.", "#neutrale"),
    ),
)

# ---- Tormentor
body += section(
    "tormentor",
    "Tormentor kommer tidligere og giver mere",
    "Tormentor dukker op fem minutter før, tåler mere og dropper en ny item, der sender mega creeps ned ad alle tre baner.",
    rows(
        row("Første gang", "20 min", "15 min", "Objektivet åbner fem minutter tidligere end før."),
        row("Barriere", "3.000", "4.000", "Unyielding Shield har en højere grundværdi, så Tormentor tåler mere skade."),
        row("Reflekteret skade", "35%", "15%", "Den starter på 15% og stiger med 5 procentpoint for hver gang, Tormentor er dræbt, op til 30%."),
        row("Guld pr. spiller", "175", "125", "Den første bliver billigere, men der kommer 50 guld oveni for hver tidligere død."),
        row("Aghanim's Shard", None, "Fra anden død", "Fra og med anden død dropper Tormentor altid en Shard, fordelt som før.", as_text=True),
        row("Ny belønning", None, "Greater Horn of Battle", "Tormentor dropper nu flere items ligesom Roshan, og hornet kommer hver gang.", as_text=True),
    )
    + """
      <svg class="horn" viewBox="0 0 720 224" role="img" aria-labelledby="horn-t horn-d">
        <title id="horn-t">Greater Horn of Battle</title>
        <desc id="horn-d">En bølge af mega creeps på hver af dine tre baner, på vej mod fjendens base.</desc>
        <g fill="none" stroke="currentColor" stroke-width="1.5">
          <rect x="6" y="64" width="44" height="72" rx="4"/>
          <rect x="670" y="64" width="44" height="72" rx="4"/>
        </g>
        <g stroke="currentColor" stroke-width="1.5" stroke-dasharray="3 6" opacity=".55">
          <line x1="64" y1="40" x2="656" y2="40"/>
          <line x1="64" y1="100" x2="656" y2="100"/>
          <line x1="64" y1="160" x2="656" y2="160"/>
        </g>
        <g fill="var(--new)">
          <g id="wave">
            <rect x="92" y="26" width="26" height="26" rx="3"/>
            <rect x="126" y="32" width="14" height="14" rx="2"/>
            <rect x="146" y="32" width="14" height="14" rx="2"/>
            <path d="M172 52 V28 l16 6 -16 6"/>
          </g>
          <use href="#wave" y="60"/>
          <use href="#wave" y="120"/>
        </g>
        <g stroke="var(--new)" stroke-width="2" fill="none" stroke-linecap="round" stroke-linejoin="round">
          <path d="M214 40 H260 m-8 -7 l8 7 -8 7"/>
          <path d="M214 100 H260 m-8 -7 l8 7 -8 7"/>
          <path d="M214 160 H260 m-8 -7 l8 7 -8 7"/>
        </g>
        <text x="6" y="212">Din base</text>
        <text x="714" y="212" text-anchor="end">Fjendens base</text>
      </svg>
      <p class="caption">Hornet bruges overalt på kortet og også fra rygsækken. Det koster ingen mana, har ingen cooldown og én ladning, og det kan ikke stakkes. Antallet af creeps følger den aktuelle bølge, men der kommer altid mindst en siege creep og en flagbearer på hver bane.</p>

      <div class="tool">
        <h3 class="tool__title">Hvad får du, når Tormentor dør igen?</h3>
        <p class="tool__hint">Træk i skyderen, og se hvordan reflekteret skade og guld vokser for hver gang, den har været dræbt.</p>
        <label class="tool__label" for="tm-n">Tormentor har været dræbt <output id="tm-out" for="tm-n">0 gange</output> før</label>
        <input class="range" id="tm-n" type="range" min="0" max="4" step="1" value="0">
        <dl class="readout">
          <div><dt>Reflekteret skade</dt><dd id="tm-reflect">15%<small id="tm-cap"></small></dd></div>
          <div><dt>Guld til hver spiller</dt><dd id="tm-gold">125</dd></div>
          <div><dt>Aghanim's Shard</dt><dd id="tm-shard">Ikke garanteret</dd></div>
        </dl>
      </div>
""",
)

# ---- Illusioner
ill_list = ", ".join(e(n) for n in illusion_items)
body += section(
    "illusioner",
    "Illusioner kan bruge items",
    "Hvert angreb fra en helt, eller en enhed der ligner en helt, har nu en Item Potency. Den bestemmer, hvor stærk en on-hit-effekt fra et item er. Helte ligger på 100%, men illusioner kan nu også bruge de fleste on-hit-effekter.",
    rows(
        row("Helte", None, "100%", "Standardværdien for et angreb."),
        row("Illusioner", None, "20%", "Kan nu anvende de fleste on-hit-effekter fra items."),
        row("Illusion Rune", None, "40%", "Illusioner fra en Illusion Rune får det dobbelte af en almindelig illusion."),
        row("Phantasm", None, "100%", "Chaos Knights Phantasm-illusioner har fuld Item Potency."),
        row("Pangolier", None, "60%", "Angreb fra Swashbuckle regnes med 60%."),
        row("Evolved, Tier 4", None, "+20%", "Et angreb fra en helt med en Tier 4 Evolved Enchantment får 20 procentpoint oveni.", as_text=True),
        row("Flere kilder", None, "Den højeste vinder", "Når en debuff kommer fra flere kilder, bruges den med højest Item Potency.", as_text=True),
    )
    + f"""
      <div class="tool">
        <h3 class="tool__title">Hvor stærk er effekten?</h3>
        <p class="tool__hint">Vælg hvem der slår, og se hvor stor en del af et items on-hit-effekt, der kommer igennem. Eksemplet er Desolator.</p>
        <div class="choice" role="group" aria-label="Vælg angriber">
          <button class="btn" type="button" data-p="100" data-n="Helt" aria-pressed="true">Helt</button>
          <button class="btn" type="button" data-p="120" data-n="Helt med Tier 4 Evolved" aria-pressed="false">Helt med Tier 4 Evolved</button>
          <button class="btn" type="button" data-p="60" data-n="Pangolier med Swashbuckle" aria-pressed="false">Pangolier, Swashbuckle</button>
          <button class="btn" type="button" data-p="40" data-n="Illusion fra Illusion Rune" aria-pressed="false">Illusion Rune</button>
          <button class="btn" type="button" data-p="20" data-n="Almindelig illusion" aria-pressed="false">Almindelig illusion</button>
        </div>
        <div class="bars">
          <div class="bars__row">
            <span class="bars__k">Styrke</span>
            <div class="bars__track"><span class="bars__fill bars__fill--new" id="pot-fill"></span></div>
            <span class="bars__v" id="pot-v">100%</span>
          </div>
        </div>
        <dl class="readout">
          <div><dt>Desolator sænker armor med</dt><dd id="pot-armor">6</dd></div>
        </dl>
        <p class="verdict" id="pot-text" aria-live="polite"></p>
        <p class="caption">Valve regner to eksempler: 120% giver 7,2 og 60% giver 3,6. Det svarer til 6 ved 100%, og det er den værdi, skyderen bruger.</p>
      </div>

      <h3 class="sec__sub">Items, der nu virker med illusioner</h3>
      <p class="sec__lede sec__lede--tight">Valve skriver direkte, at disse items nu virker med illusioner: {ill_list}.</p>
""",
)

# ---- Helte
body += section(
    "helte",
    "Helte bliver tykkere, og magi gør mindre ondt",
    "Alle helte starter med mere liv, og de fleste spells gør mindre skade. Magic resistance fra Intelligence bliver samtidig lidt billigere at få.",
    rows(
        row("Basisliv", "120", "200", "Hver helt starter med 80 liv mere, før Strength lægges til."),
        row("Liv pr. Strength", "22", "20", "Hvert Strength-point giver to liv mindre."),
        row("Magic resistance pr. Intelligence", "0,1%", "0,125%", "Otte Intelligence giver nu 1% magic resistance. Før skulle der ti til."),
        row("Spell damage", None, "Sat ned", "Skaden er skåret ned på størstedelen af Magic- og Pure-spells, og nogle lange slows er gjort kortere. De præcise tal står under hver helt.", as_text=True),
        row("Items og spells", None, "Mindre bidrag", "Items giver mindre Spell Amplification, Area of Effect og Cast Range til dine spells.", as_text=True),
    )
    + """
      <div class="tool">
        <h3 class="tool__title">Får din helt mere eller mindre liv?</h3>
        <p class="tool__hint">Regnestykket bruger kun de to tal ovenfor: basisliv plus liv pr. Strength gange din samlede Strength. Items og talents med ekstra liv er ikke med.</p>
        <label class="tool__label" for="hp-str">Samlet Strength: <output id="hp-out" for="hp-str">30</output></label>
        <input class="range" id="hp-str" type="range" min="10" max="80" step="1" value="30">
        <div class="bars">
          <div class="bars__row">
            <span class="bars__k">Før</span>
            <div class="bars__track"><span class="bars__fill bars__fill--old" id="hp-old"></span></div>
            <span class="bars__v" id="hp-old-v"></span>
          </div>
          <div class="bars__row">
            <span class="bars__k">Nu</span>
            <div class="bars__track"><span class="bars__fill bars__fill--new" id="hp-new"></span></div>
            <span class="bars__v" id="hp-new-v"></span>
          </div>
        </div>
        <p class="verdict" id="hp-text" aria-live="polite"></p>
        <p class="caption">Ved 40 Strength er det lige meget. Under 40 får du mere liv, over 40 får du lidt mindre.</p>
      </div>

      <h3 class="sec__sub">De største omlægninger</h3>
      <p class="sec__lede sec__lede--tight">Nogle helte har fået nye eller omarbejdede evner. Her er otte af dem, kort fortalt. Alt det øvrige finder du under <a href="#slaa-op">Slå op</a>.</p>
"""
    + facts(
        [
            ("Chaos Knight", "Ny innate, Ahead, Armageddon. Passivt får han 5 i fart for hvert sekund, han løber uden at stoppe, op til 20 + 2 pr. level. Aktivt kan hans Phantasm-illusioner storme frem mod et punkt, så længe mindst én lever. Fundamental Forging er fjernet.", "#slaa-op"),
            ("Lycan", "Pack Hunter erstatter Apex Predator som innate. Lycan og hans enheder markerer fjender ved angreb i 6 sekunder. Markerede fjender afsløres, også i usynlighed og fog of war. Lycan og hans enheder gør 5% mere skade mod dem og får 3% lifesteal + 1% pr. 3 levels.", "#slaa-op"),
            ("Nyx Assassin", "Scarab Metabolism erstatter Mana Burn som innate. Efter 3 sekunder uden skade får han 5 + 1 pr. level i fart og regenererer 0,35% af sit maks liv og mana i sekundet. Burrow giver nu tre gange så meget, og bonussen forsvinder ikke ved skade.", "#slaa-op"),
            ("Chen", "Zealot er omarbejdet. Passivt får Chens creeps mere fart, skade og et minimum for maks liv. Aktivt genopliver den den udvalgte Zealot, med 60 sekunders cooldown minus 1 pr. level. Holy Persuasion giver ikke længere skade eller fart, men Chen kan målrette sig selv for at samle alle sine creeps hos sig.", "#slaa-op"),
            ("Leshrac", "Nihilism er omarbejdet. Den disarmer fjender inden for 550 i 4 sekunder, mens den konstant dispeller dem og Leshrac selv. Den gør ham ikke længere Ethereal, så den kan bruges, mens han er debuff immune.", "#slaa-op"),
            ("Meepo", "Er nu en Universal-helt, og MegaMeepo er fjernet. Divided We Stand skærer XP forholdsmæssigt efter, hvor mange Meepoer der har fået XP, i stedet for en fast procentdel. Dig kommer med Aghanim's Scepter i stedet for Shard, og Shard giver i stedet et løft-og-kast.", "#slaa-op"),
            ("Juggernaut", "Swiftslash er fjernet. Blade Fury disarmer ham nu helt, men Aghanim's Scepter lader ham angribe under Blade Fury, også mens han bevæger sig, med 75% skade og Item Potency.", "#slaa-op"),
            ("Nature's Prophet", "Curse of the Oldgrowth er en passiv, hvor hans angreb lægger en stakkende debuff på 24 magisk skade i sekundet og 12% slow. Teleportation giver ikke længere barriere, og cooldown er længere, 80/60/40/20 sekunder mod før 65/50/35/20.", "#slaa-op"),
        ]
    )
    + """
      <p class="caption caption--top">Reglerne for, hvilke innates Break slår fra, er opdateret for mange helte. Nogle bliver nu helt slået fra, andre kun delvist.</p>

      <h3 class="sec__sub">De mest ændrede helte</h3>
      <p class="sec__lede sec__lede--tight">Antal ændringslinjer i Valves noter. Det måler, hvor meget teksten fylder, ikke hvor meget en helt er blevet bedre eller værre. Klik på en helt for at se alle ændringerne.</p>
      <ul class="hbar">
"""
    + top_rows
    + "      </ul>\n",
)

# ---- Guld og XP
body += section(
    "guld",
    "Guld og erfaring",
    "Indkomsten bliver fladere. Tårne og barakker giver et fast beløb for sidste hit, passivt guld vokser ikke mere med tiden, og alle får passiv XP fra starthornet.",
    rows(
        row("Passivt guld", None, "Vokser ikke", "Guld pr. minut skalerer ikke længere over spillets længde.", as_text=True),
        row("Passiv XP", None, "50 pr. minut", "Alle helte får det efter starthornet.", as_text=True),
        row("XP til level 30", "64.400", "66.600", "Der skal lidt mere erfaring til for at nå det sidste level."),
        row("Bygningers bounty", None, "Fast", "Bygninger har ikke længere variable bounties ved sidste hit, og bounties er sat ned.", as_text=True),
        row("Heltes kill bounty", None, "Skaleret om", "Valve har omskaleret bounty for at dræbe helte, men noterne oplyser ingen tal.", as_text=True),
    )
    + dumb_chart(
        "Sidste hit på bygninger",
        last_hit,
        "Rød bjælke er det gamle. Hvor Valve oplyste et interval, er hele intervallet tegnet. Grøn prik er det nye. Skalaen er guld.",
    )
    + dumb_chart(
        "Guld pr. spiller",
        per_player,
        "Det guld, hver spiller på holdet får, når bygningen eller Roshan falder.",
    ),
)

# ---- Kort (lane creeps, glyph, pips, map)
body += section(
    "kort",
    "Creeps, Roshan og kortet",
    "Kortets rytme ændrer sig. Siege creeps kommer oftere, Roshan kommer hurtigere igen, glyph kan bruges to gange, og kortet er justeret flere steder.",
    '      <h3 class="sec__sub sec__sub--first">Lane creeps</h3>\n'
    + rows(
        row("Siege, 0-30 min", None, "Uændret", "Én siege creep pr. bølge, hver femte minut.", as_text=True),
        row("Siege, 30-60 min", "2 hver 5. min", "1 hver 2,5 min", "Regnet pr. fem minutter er det stadig to siege creeps, men de kommer fordelt på to bølger."),
        row("Siege, efter 60 min", "3 hver 5. min", "2 hver 2,5 min", "Regnet pr. fem minutter stiger det fra tre til fire siege creeps."),
        row("Melee creeps", None, "Ingen stigning ved 30:00", "Antallet af melee creeps vokser ikke længere ved 30:00.", as_text=True),
        row("Flagbearer efter 30 min", "Hver anden bølge", "Hver bølge", "En flagbearer-creep kommer nu i hver bølge efter 30:00."),
        row("Første ranged creep ekstra", "40:00", "35:00", "Den ekstra ranged creep kommer fem minutter tidligere."),
        row("Pull", None, "Op til 25% langsommere", "Lane creeps, der er trukket ud af banen, bevæger sig langsommere. Pulls ved Tier 1-tårne i safelane tæller ikke.", as_text=True),
        row("Siege og tårne", None, "Skifter ikke mål", "Siege creeps skifter ikke længere aggro til tårne, der angriber helte.", as_text=True),
    )
    + '\n      <h3 class="sec__sub">Roshan, glyph og pips</h3>\n'
    + rows(
        row("Roshans genopstandelse", None, "1 min hurtigere pr. død", "Grundtiden falder med ét minut hver gang Roshan er dræbt, men aldrig under fem minutter. Timeren viser nu også, hvem der bærer Aegis.", as_text=True),
        row("Glyph of Fortification", None, "2 ladninger", "Ny ladning hvert sjette minut og syv sekunder mellem brug. Den nulstilles ikke længere, når en bygning falder.", as_text=True, extra='<span class="pips" aria-hidden="true"><i></i><i></i></span>'),
        row("Pip health", None, "Fælles regler", "Alle enheder kan skade enheder med pips. Et angreb fra en helt, Roshan, et tårn eller fountain tager ét helt pip, og fra en illusion eller creep et kvart. Enheder med Fragile mister to pips til melee-helte.", as_text=True),
        row("Fragile", None, "Courier, Banner, Nimbus", "Couriers og Roshan's Banner har nu fragile pip health, og Zeus' Nimbus har også.", as_text=True),
    )
    + '\n      <h3 class="sec__sub">Kortet</h3>\n'
    + rows(
        row("Tormentor", "20 min", "15 min", "Se Tormentor ovenfor.", "#tormentor"),
        row("Fountain True Sight", "1200", "1800", "Fountain afslører usynlige enheder på længere afstand."),
        row("Dire fountain", None, "300 tættere", "Den er flyttet cirka 300 enheder tættere på Dire Ancient.", as_text=True),
        row("Twin Gates", None, "Flyttet", "De ligger nu på kortets øvre og nedre kant, hvor små oversvømmede camps lå før. Camps ved flodenderne er flyttet i takt.", as_text=True),
        row("Mid lane", None, "Tårne flyttet", "Tårnene er flyttet, så afstanden fra base til tårn er den samme for begge hold. Floden og træerne omkring midten er justeret.", as_text=True),
        row("Outposts", None, "Kan tages, mens du er silenced", "Du kan fange et outpost, selv om du er silenced.", as_text=True),
        row("Wisdom Shrine", "200 + 300", "200 + 200", "XP for første brug plus bonus for hver senere brug."),
        row("Invisibility Rune", None, "Giver Disguise", "Runen giver også en Disguise-buff, der beskytter mod True Sight, så længe du ikke er tæt på fjendtlige helte eller bygninger. Den virker to sekunder efter, runen er taget.", as_text=True),
        row("Illusion Rune", None, "40% Item Potency", "Se Illusioner ovenfor.", "#illusioner", as_text=True),
    )
    + '\n      <h3 class="sec__sub">Spell-regler</h3>\n'
    + rows(
        row("Leashes", None, "Blokerer ikke længere", "Leashes, der ikke udtrykkeligt trænger igennem debuff immunity, som Slarks Pounce, forhindrer ikke længere bevægelses-evner, selv hvis de sættes efter, du er blevet debuff immune.", as_text=True),
        row("Debuff immunity", None, "Magic resistance gælder", "Evner, der trænger igennem debuff immunity, ignorerer ikke længere den magic resistance, som immuniteten giver.", as_text=True),
        row("Spell Lifesteal", None, "Lægges sammen", "Flere eksemplarer af samme item stakker additivt. To Voodoo Masks giver +30%.", as_text=True),
    ),
)

# ---- Neutrale
body += section(
    "neutrale",
    "Neutrale items og creeps",
    "Neutrale items får en tier mindre, og hver tier bliver delt i puljer, der trækkes ved spillets start. Jungle-lejrene er flyttet rundt, og creeps har fået et hjem.",
    rows(
        row("Antal tiers", "5", "4", "Den femte tier er væk, og den sidste åbner efter 50 minutter."),
        row("Madstone til Tier 4", "10", "14", "Det koster flere Madstones at lave et Tier 4-item."),
        row("Madstone ved omlavning", "10", "6", "Hver omlavning af et Tier 4-item koster 6 mere end den forrige, før var det 10."),
    )
    + """
      <div class="tiers" role="group" aria-label="Hvornår hver neutral tier åbner, i minutter">
        <div class="tiers__track"></div>
        <span class="tiers__m" style="--t:0"><b>Tier 1</b><small>0:00</small></span>
        <span class="tiers__m" style="--t:15"><b>Tier 2</b><small>15:00</small></span>
        <span class="tiers__m" style="--t:30"><b>Tier 3</b><small>30:00</small></span>
        <span class="tiers__m" style="--t:50"><b>Tier 4</b><small>50:00</small></span>
        <span class="tiers__m tiers__m--end" style="--t:65"><b>Infinite Madstone</b><small>65:00</small></span>
      </div>

      <h3 class="sec__sub">Puljer i stedet for tilfældige valg</h3>
      <p class="sec__lede sec__lede--tight">Før blev mulighederne i en tier trukket blandt alle items. Nu er hver tier delt i fire puljer med tre artifacts, og der vælges ét fra hver pulje. Alle valg er afgjort fra spillets start.</p>
      <div class="pools">
"""
    + pools
    + "      </div>\n"
    + "\n      <h3 class=\"sec__sub\">Ind og ud</h3>\n"
    + rows(
        row(
            "Nye artifacts",
            None,
            f"{len(art_new)} nye",
            "Tier 1: Red Ledger. Tier 2: Brick. Tier 3: Balmhook og Vile Phial. Tier 4: Helm of the Hivemind.",
            as_text=True,
        ),
        row("Cyklet ud", None, f"{len(art_out)} artifacts", e(", ".join(art_out)) + ".", as_text=True),
        row("Enchantments", None, f"{len(D['enchantments'])} justeret", "Tiers, bonusser og rækkevidder er ændret. Se alle under Slå op.", "#slaa-op", as_text=True),
    )
    + '\n      <h3 class="sec__sub">Jungle</h3>\n'
    + rows(
        row("Guld pr. cyklus", "+1", "Skifter", "Bounty stiger ikke længere med 1 pr. cyklus, men skifter hvert minut mellem at hæve minimum og maksimum med 1.", as_text=True),
        row("XP pr. cyklus", "5", "4", "Opgraderingen af XP-bounty pr. cyklus er sat ned."),
        row("Hjemmejungle", None, "Hver creep har ét hjem", "Alle creeps, der hverken er amfibier eller ancients, spawner kun på deres egen side af kortet.", as_text=True),
        row("Nye camps", None, "4 nye", "Radigull (medium, Radiant), Odobenus (medium, Dire), Eimermole (large, Radiant) og Ancient Ogre Seal (ancient).", as_text=True),
        row("Fjernede camps", None, "3 væk", "I Dire jungle er medium Centaur-camp, large Warpine Raider-camp og Ancient Thunderhide-camp fjernet.", as_text=True),
        row("Kobold camp", "3", "2", "Der er to Kobolds i stedet for tre."),
        row("Defender's gates", None, "Åbne for neutrale", "Neutrale creeps kan nu gå gennem både Radiants og Dires defender's gates.", as_text=True),
    ),
)

# ---- Items
body += section(
    "items",
    "Nye og fjernede items",
    f"Der kommer {len(new_items)} nye items, ét vender tilbage, og {len(removed)} forsvinder. Mange priser og opskrifter er justeret.",
    rows(
        row("Greater Horn of Battle", None, "Ny", "Dropper fra Tormentor og kalder mega creeps på alle tre baner. Se Tormentor ovenfor.", "#tormentor", as_text=True),
        row("Bloodslinger", None, "925 guld", "Ny. Opgraderet Blood Grenade: +100 liv, +8 Intelligence og +1,25 mana regen. Slynger en granat, der bremser med 30%, og som falder til 15% over 5 sekunder.", as_text=True),
        row("Caduceus", None, "5.400 guld", "Ny. Phylactery og Force Staff i ét: +8 Strength, +8 Agility og +20 Intelligence. Den næste unit target-spell på en fjende gør 175 ekstra skade og bremser, og på en allieret heler den 200.", as_text=True),
        row("Ristul's Devotion", None, "3.800 guld", "Ny. Giver +8 armor og en aura på 1200 med 20% lifesteal, 18% spell lifesteal og 18% ekstra skade til allierede i nærheden.", as_text=True),
        row("Sabatons of Mordiggian", None, "5.950 guld", "Ny. Opgradering af Phase Boots og Armlet of Mordiggian, med +40 skade, +30 angrebshastighed og +10 armor. Kan slås til og dræner da 45 liv i sekundet for mere skade, Strength og armor.", as_text=True),
        row("Skypiercer", None, "6.000 guld", "Ny. Heaven's Halberd, Sange og Talisman of Evasion: +35 Strength, +5 armor og +25% evasion. Disarm i 3 sekunder, og tæt på fjender kommer den hurtigere tilbage.", as_text=True),
        row("Starforge", None, "6.000 guld", "Ny. Meteor Hammer og Ultimate Orb: +24 Strength og Agility, +40 Intelligence og +6% spell amp. Efter en disable brænder fjenden i 3 sekunder.", as_text=True),
        row("Quarterstaff", None, "900 guld", "Er tilbage og giver +10 skade og +10 angrebshastighed.", as_text=True),
        row("Fjernet", None, ", ".join(removed), "Valve har fjernet dem fra spillet.", as_text=True),
    )
    + f"""
      <h3 class="sec__sub">Priser</h3>
      <p class="sec__lede sec__lede--tight">{len(prices)} items skifter pris. Bjælken viser, hvor meget prisen er rykket, uanset om den er steget eller faldet. Tallene er den samlede pris i guld. Urn of Shadows er den eneste, der bliver dyrere.</p>
      <ul class="hbar hbar--price">
"""
    + price_rows
    + f"""      </ul>
      <p class="caption caption--top">{len(recipe_changed)} items har fået en ny opskrift. Se detaljerne under <a href="#slaa-op">Slå op</a>.</p>
""",
)

# ---- Slå op
body += """  <section class="sec" id="slaa-op">
    <div class="wrap">
      <h2 class="sec__title">Slå alt op</h2>
      <p class="sec__lede">Alle helte, items, neutrale items og creeps fra Valves noter. Søg efter en helt, en evne eller et item.</p>

      <div class="ref" id="ref">
        <div class="ref__bar">
          <div class="choice" id="ref-tabs" role="group" aria-label="Vælg kategori"></div>
          <div class="ref__find">
            <label class="sr" for="ref-q">Søg</label>
            <input class="search" id="ref-q" type="search" placeholder="Søg, fx Pugna eller Desolator" autocomplete="off">
          </div>
        </div>
        <div class="choice ref__sort" id="ref-sort" role="group" aria-label="Sortér helte" hidden></div>
        <p class="ref__count" id="ref-count" aria-live="polite"></p>
        <div class="ref__list" id="ref-list"></div>
        <noscript><p class="caption">Opslaget kræver JavaScript. Du kan i stedet læse Valves egne noter.</p></noscript>
      </div>
      <p class="caption caption--top">Tal og korte udsagn er hentet direkte fra Valves noter. Længere beskrivelser, især af nye evner, er ikke kopieret hertil. Dem finder du hos <a href="https://www.dota2.com/patches/7.42">Valve</a>.</p>
    </div>
  </section>

"""

# ---- Rettelser
body += f"""  <section class="sec" id="rettelser">
    <div class="wrap">
      <h2 class="sec__title">Rettelser og småting</h2>
      <p class="sec__lede">Valves nyhedsindlæg til patchen lister også genveje, visning, ydelse og fejlrettelser. Her er hele listen, oversat.</p>

      <div class="choice" id="chips" role="group" aria-label="Filtrér efter type"></div>

      {fixes}
    </div>
  </section>

</main>

<footer class="foot" id="kilder">
  <div class="wrap foot__cols">
    <div>
      <h2>Kilder</h2>
      <ul>
        <li><a href="https://www.dota2.com/patches/7.42">Valves officielle patch notes 7.42</a></li>
        <li><a href="https://www.dota2.com/newsentry/689773669992367212">Valves nyhedsindlæg: 7.42 Gameplay Update</a></li>
      </ul>
    </div>
    <div>
      <h2>Om siden</h2>
      <p>Uofficiel forklaring på dansk, skrevet den 18. november 2026. Alle tal er hentet fra Valves officielle noter til 7.42. Længere beskrivelser er ikke kopieret hertil, og hvis noget afviger, er det Valves tekst, der gælder.</p>
      <p>Dota 2 er et varemærke tilhørende Valve Corporation. Siden er ikke tilknyttet Valve. Skrifttypen Archivo er under SIL Open Font License.</p>
    </div>
  </div>
</footer>

<script src="data.js"></script>
<script src="app.js"></script>
</body>
</html>
"""

open(f"{REPO}/index.html", "w", encoding="utf-8").write(head + body)
print("wrote index.html", len(head + body), "bytes")
