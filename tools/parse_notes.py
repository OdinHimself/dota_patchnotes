#!/usr/bin/env python3
"""Parse Valve's Dota 2 patch notes (plain text) into structured JSON.

Usage: parse_notes.py NOTES.txt OUT.json
The text has no indentation, so headings are told apart from change lines by
shape: a heading is short, Title Case, has no digits and no change verbs.
"""
import json, re, sys

HEROES = """Abaddon|Alchemist|Ancient Apparition|Anti-Mage|Arc Warden|Axe|Bane|Batrider|Beastmaster|Bloodseeker|Bounty Hunter|Brewmaster|Bristleback|Broodmother|Centaur Warrunner|Chaos Knight|Chen|Clinkz|Clockwerk|Crystal Maiden|Dark Seer|Dark Willow|Dawnbreaker|Dazzle|Death Prophet|Disruptor|Doom|Dragon Knight|Drow Ranger|Earth Spirit|Earthshaker|Elder Titan|Ember Spirit|Enchantress|Enigma|Faceless Void|Grimstroke|Gyrocopter|Hoodwink|Huskar|Invoker|Io|Jakiro|Juggernaut|Keeper of the Light|Kez|Kunkka|Largo|Legion Commander|Leshrac|Lich|Lifestealer|Lina|Lion|Lone Druid|Luna|Lycan|Magnus|Marci|Mars|Medusa|Meepo|Mirana|Monkey King|Morphling|Muerta|Naga Siren|Nature's Prophet|Necrophos|Night Stalker|Nyx Assassin|Ogre Magi|Omniknight|Oracle|Outworld Destroyer|Pangolier|Phantom Assassin|Phantom Lancer|Phoenix|Primal Beast|Puck|Pudge|Pugna|Queen of Pain|Razor|Riki|Ringmaster|Rubick|Sand King|Shadow Demon|Shadow Fiend|Shadow Shaman|Silencer|Skywrath Mage|Slardar|Slark|Snapfire|Sniper|Spectre|Spirit Breaker|Storm Spirit|Sven|Techies|Templar Assassin|Terrorblade|Tidehunter|Timbersaw|Tinker|Tiny|Treant Protector|Troll Warlord|Tusk|Underlord|Undying|Ursa|Vengeful Spirit|Venomancer|Viper|Visage|Void Spirit|Warlock|Weaver|Windranger|Winter Wyvern|Witch Doctor|Wraith King|Zeus""".split("|")
HERO_SET = set(HEROES)

SMALL = {"of", "the", "and", "to", "in", "for", "on", "a", "an", "from", "with"}
KEYWORDS = re.compile(
    r"\b(increased|decreased|changed|rescaled|reduced|improved|reworked|replaced|swapped|renamed|moved|removed|added|"
    r"new|returning|cycled|now|no longer|still|also|can't|cannot|doesn't|don't|does|has|have|will|can|is|are|"
    r"instead|unchanged|requires|provides|costs|cost|total|recipe|upgraded|applies|deals|grants|works|affects|lost)\b", re.I)

def is_heading(s):
    if s == "General changes":
        return True
    if ". " in s:
        return False
    if len(s) > 44 or s.endswith(".") or re.search(r"\d", s) or "," in s or ":" in s:
        return False
    if KEYWORDS.search(s):
        return False
    words = s.split()
    if len(words) > 6:
        return False
    for w in words:
        if w.lower() in SMALL:
            continue
        if not (w[0].isupper() or w[0] in "'\"("):
            return False
    return True

DIFF = re.compile(r"^(?P<k>.+?)\s+(?P<v>increased|decreased|changed|rescaled|reduced|improved|reworked|replaced)\s+from\s+(?P<a>.+?)\s+to\s+(?P<b>.+)$", re.I)

SENT = re.compile(r"(?<=[a-z0-9%)g])\.\s+(?=[A-Z])")

def line_objs(s):
    """One line may hold two diffs ('Recipe cost ... . Total cost ...'): split those only."""
    if len(re.findall(r"\bfrom\b.+?\bto\b", s)) >= 2 and SENT.search(s):
        return [line_obj(t) for t in SENT.split(s)]
    return [line_obj(s)]

def line_obj(s):
    m = DIFF.match(s)
    if m:
        return {"k": m["k"], "a": m["a"], "b": m["b"]}
    return {"x": s}

def parse_blocks(lines, label_names=()):
    """Split into [{name, lines:[obj]}]; an entry starts at a heading line."""
    out, cur, pre = [], None, []
    for s in lines:
        if s in label_names:
            cur = {"label": s, "entries": []}
            out.append(cur)
            continue
        if is_heading(s):
            if cur is None:
                cur = {"label": None, "entries": []}
                out.append(cur)
            cur["entries"].append({"name": s, "lines": []})
        else:
            if cur is None or not cur["entries"]:
                if cur is None:
                    cur = {"label": None, "entries": []}
                    out.append(cur)
                cur["entries"].append({"name": None, "lines": []})
            cur["entries"][-1]["lines"].extend(line_objs(s))
    return out

def main(src, dst):
    L = [l.strip() for l in open(src, encoding="utf-8") if l.strip()]
    idx = {}
    for name in ("General Updates", "Map Objectives", "Terrain Changes", "Neutral Creep Updates", "Item Updates",
                 "Basic Items", "Upgrades", "Neutral Item Updates", "Global Changes", "Artifact Changes",
                 "Artifact Pools", "Enchantment Changes", "Hero Updates"):
        idx[name] = L.index(name)
    data = {"counts": {}}

    # neutral creeps: from "Neutral Creep Updates" up to "Item Updates"
    creeps = L[idx["Neutral Creep Updates"] + 1: idx["Item Updates"]]
    data["creeps"] = parse_blocks(creeps)

    # items
    basic = L[idx["Basic Items"] + 1: idx["Upgrades"]]
    upg = L[idx["Upgrades"] + 1: idx["Neutral Item Updates"]]
    data["itemsBasic"] = parse_blocks(basic)
    data["itemsUpgrades"] = parse_blocks(upg)

    # neutral items
    glob = L[idx["Global Changes"] + 1: idx["Artifact Changes"]]
    art = L[idx["Artifact Changes"] + 1: idx["Artifact Pools"]]
    pools = L[idx["Artifact Pools"] + 1: idx["Enchantment Changes"]]
    ench = L[idx["Enchantment Changes"] + 1: idx["Hero Updates"]]
    data["neutralGlobal"] = glob
    data["artifacts"] = parse_blocks(art)
    data["enchantments"] = parse_blocks(ench)
    pl, tier = {}, None
    for s in pools:
        if re.fullmatch(r"Tier \d", s):
            tier = s; pl[tier] = []
        elif tier and "," in s:
            pl[tier].append([x.strip() for x in s.split(",")])
        elif tier is None:
            data.setdefault("poolRules", []).append(s)
        else:
            data.setdefault("poolRules", []).append(s)
    data["pools"] = pl

    # heroes
    H = L[idx["Hero Updates"] + 1:]
    heroes, cur = [], None
    for s in H:
        if s in HERO_SET and not (cur and cur["n"] == s):
            cur = {"n": s, "raw": []}
            heroes.append(cur)
        elif cur is not None:
            cur["raw"].append(s)
    out_heroes = []
    for h in heroes:
        blocks = parse_blocks(h["raw"], label_names=("Abilities", "Talents"))
        # lines before the first label are base stats / hero-wide
        base = []
        secs = []
        for b in blocks:
            if b["label"] is None:
                for e in b["entries"]:
                    if e["name"]:
                        base.append({"h": e["name"]})
                    base.extend(e["lines"])
            else:
                secs.append(b)
        n_changes = sum(len(e["lines"]) for b in blocks for e in b["entries"])
        out_heroes.append({"n": h["n"], "base": base, "sections": secs, "c": n_changes})
    data["heroes"] = out_heroes
    data["counts"] = {
        "heroes": len(out_heroes),
        "itemsBasic": sum(len(b["entries"]) for b in data["itemsBasic"]),
        "itemsUpgrades": sum(len(b["entries"]) for b in data["itemsUpgrades"]),
        "artifacts": sum(len(b["entries"]) for b in data["artifacts"]),
        "enchantments": sum(len(b["entries"]) for b in data["enchantments"]),
        "creeps": sum(len(b["entries"]) for b in data["creeps"]),
        "heroLines": sum(h["c"] for h in out_heroes),
    }
    missing = [x for x in HEROES if x not in {h["n"] for h in out_heroes}]
    data["counts"]["missingHeroes"] = missing
    # item price changes ("Total cost decreased from 4650g to 4550g")
    price = re.compile(r"Total cost (?:increased|decreased) from (\d+)g to (\d+)g")
    prices = []
    for group in ("itemsBasic", "itemsUpgrades"):
        for b in data[group]:
            for e in b["entries"]:
                for x in e["lines"]:
                    if x.get("k") == "Total cost":
                        a, b = re.sub(r"\D", "", x["a"]), re.sub(r"\D", "", x["b"].split(" ")[0])
                        if a and b:
                            prices.append({"n": e["name"], "a": int(a), "b": int(b)})
    prices.sort(key=lambda r: r["b"] - r["a"])

    MAXLEN = 120  # longer prose is left out: numbers and short statements only

    def slim(lines):
        keep, omitted = [], 0
        for x in lines:
            if "x" in x and len(x["x"]) > MAXLEN:
                omitted += 1
            else:
                keep.append(x)
        return keep, omitted

    def flat(blocks):
        out = []
        for b in blocks:
            for e in b["entries"]:
                ls, o = slim(e["lines"])
                out.append({"n": e["name"], "ls": ls, "o": o})
        return out

    for h in data["heroes"]:
        h["base"], h["ob"] = slim(h["base"])
        tot = h["ob"]
        for s in h["sections"]:
            for e in s["entries"]:
                e["lines"], e["o"] = slim(e["lines"])
                tot += e["o"]
        h["o"] = tot

    site = {
        "counts": data["counts"],
        "heroes": data["heroes"],
        "items": [dict(g="basic", **i) for i in flat(data["itemsBasic"])] + [dict(g="upgrade", **i) for i in flat(data["itemsUpgrades"])],
        "artifacts": flat(data["artifacts"]),
        "enchantments": flat(data["enchantments"]),
        "creeps": flat(data["creeps"]),
        "pools": data["pools"],
        "prices": prices,
    }
    js = "window.PATCH=" + json.dumps(site, ensure_ascii=False, separators=(",", ":")) + ";\n"
    if dst.endswith(".json"):
        json.dump(data, open(dst, "w", encoding="utf-8"), ensure_ascii=False, separators=(",", ":"))
    else:
        open(dst, "w", encoding="utf-8").write(js)
    print(json.dumps(data["counts"], ensure_ascii=False), "prices:", len(prices))

if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
