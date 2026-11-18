(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const dk = new Intl.NumberFormat("da-DK", { maximumFractionDigits: 1 });

  /* Match ruler: Tormentor glides from the old time (20) to the new (15), once. */
  const tormentor = $("#mark-tormentor");
  if (tormentor && !reduceMotion) {
    tormentor.style.setProperty("--t", "20");
    window.setTimeout(() => tormentor.style.setProperty("--t", "15"), 900);
  }

  /* Tormentor: reflect and gold grow with every previous death. */
  const tmRange = $("#tm-n");
  if (tmRange) {
    const out = $("#tm-out");
    const reflect = $("#tm-reflect");
    const cap = $("#tm-cap");
    const gold = $("#tm-gold");
    const shard = $("#tm-shard");

    const updateTormentor = () => {
      const deaths = Number(tmRange.value);
      const reflectPct = Math.min(15 + 5 * deaths, 30);
      out.textContent = deaths === 1 ? "1 gang" : `${deaths} gange`;
      reflect.firstChild.nodeValue = `${reflectPct}%`;
      cap.textContent = reflectPct === 30 ? "Loftet er nået" : "";
      gold.textContent = String(125 + 50 * deaths);
      shard.textContent = deaths >= 1 ? "Altid" : "Ikke garanteret";
    };

    tmRange.addEventListener("input", updateTormentor);
    updateTormentor();
  }

  /* Item Potency: pick who attacks, see how much of the effect gets through. */
  const potButtons = $$("[data-p]");
  if (potButtons.length) {
    const fill = $("#pot-fill");
    const value = $("#pot-v");
    const armor = $("#pot-armor");
    const text = $("#pot-text");
    const scaleMax = 120;
    const desolatorBase = 6; /* 7,2 at 120% and 3,6 at 60% in Valve's own examples */

    const selectPotency = (btn) => {
      const pct = Number(btn.dataset.p);
      potButtons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      fill.style.width = `${(pct / scaleMax) * 100}%`;
      value.textContent = `${pct}%`;
      armor.textContent = dk.format((desolatorBase * pct) / 100);
      if (pct === 100) text.textContent = "En helt bruger on-hit-effekter med fuld styrke.";
      else if (pct > 100) text.textContent = `${btn.dataset.n} bruger on-hit-effekter med ${pct}%, altså mere end normalt.`;
      else text.textContent = `${btn.dataset.n} bruger on-hit-effekter med ${pct}% af styrken.`;
    };

    potButtons.forEach((b) => b.addEventListener("click", () => selectPotency(b)));
    selectPotency(potButtons[0]);
  }

  /* Hero health: old formula against new formula. */
  const hpRange = $("#hp-str");
  if (hpRange) {
    const out = $("#hp-out");
    const oldFill = $("#hp-old");
    const newFill = $("#hp-new");
    const oldV = $("#hp-old-v");
    const newV = $("#hp-new-v");
    const text = $("#hp-text");
    const scaleMax = 2000;
    const fmt = new Intl.NumberFormat("da-DK");

    const updateHealth = () => {
      const str = Number(hpRange.value);
      const before = 120 + 22 * str;
      const after = 200 + 20 * str;
      const diff = after - before;

      out.textContent = String(str);
      oldFill.style.width = `${(before / scaleMax) * 100}%`;
      newFill.style.width = `${(after / scaleMax) * 100}%`;
      oldV.textContent = fmt.format(before);
      newV.textContent = fmt.format(after);

      if (diff > 0) text.textContent = `Du får ${fmt.format(diff)} liv mere.`;
      else if (diff < 0) text.textContent = `Du får ${fmt.format(-diff)} liv mindre.`;
      else text.textContent = "Du får præcis lige meget liv.";
    };

    hpRange.addEventListener("input", updateHealth);
    updateHealth();
  }

  /* Lookup: heroes, items, neutral items, enchantments and creeps from Valve's notes. */
  const refList = $("#ref-list");
  if (refList) initLookup();

  function initLookup() {
    const data = window.PATCH;
    const tabsBox = $("#ref-tabs");
    const sortBox = $("#ref-sort");
    const query = $("#ref-q");
    const count = $("#ref-count");

    if (!data) {
      refList.innerHTML = '<p class="ref__empty">Opslaget kunne ikke hentes. Valves noter findes på dota2.com/patches/7.42.</p>';
      return;
    }

    const LABELS = { Abilities: "Evner", Talents: "Talents" };
    const el = (tag, cls, text) => {
      const n = document.createElement(tag);
      if (cls) n.className = cls;
      if (text != null) n.textContent = text;
      return n;
    };

    /* Normalise every category into { name, n, groups:[{label, entries:[{name, lines}]}], omitted, hay } */
    const fromEntries = (list, extra) =>
      list.map((x) => {
        const lines = x.ls || [];
        return {
          name: x.n,
          n: lines.length + (x.o || 0),
          groups: [{ label: null, entries: [{ name: null, lines }] }],
          omitted: x.o || 0,
          hay: (x.n + " " + lines.map((l) => l.x || `${l.k} ${l.a} ${l.b}`).join(" ")).toLowerCase(),
          ...(extra ? extra(x) : {}),
        };
      });

    const heroes = data.heroes.map((h) => {
      const groups = [];
      if (h.base.length) groups.push({ label: "Grundstats", entries: [{ name: null, lines: h.base }] });
      h.sections.forEach((s) => groups.push({ label: LABELS[s.label] || s.label, entries: s.entries }));
      const names = h.sections.flatMap((s) => s.entries.map((e) => e.name || "")).join(" ");
      return { name: h.n, n: h.c, groups, omitted: h.o || 0, hay: (h.n + " " + names).toLowerCase() };
    });

    const categories = [
      { id: "heroes", label: "Helte", rows: heroes, noun: "helte", sortable: true },
      { id: "items", label: "Items", rows: fromEntries(data.items), noun: "items" },
      { id: "artifacts", label: "Neutrale items", rows: fromEntries(data.artifacts), noun: "neutrale items" },
      { id: "enchantments", label: "Enchantments", rows: fromEntries(data.enchantments), noun: "enchantments" },
      { id: "creeps", label: "Creeps", rows: fromEntries(data.creeps), noun: "poster" },
    ];

    const state = { cat: categories[0], sort: "az", q: "", open: null };

    const lineNode = (l) => {
      const li = el("li");
      if (l.k !== undefined) {
        li.append(el("span", "ref__k", l.k));
        li.append(el("del", null, l.a));
        li.append(document.createTextNode(" "));
        li.append(el("ins", null, l.b));
      } else {
        li.textContent = l.x;
      }
      return li;
    };

    const fillBody = (body, rec) => {
      rec.groups.forEach((g) => {
        if (g.label) body.append(el("h4", "ref__grp", g.label));
        g.entries.forEach((e) => {
          if (e.name) body.append(el("h5", "ref__ab", e.name));
          if (e.lines.length) {
            const ul = el("ul", "ref__lines");
            e.lines.forEach((l) => ul.append(lineNode(l)));
            body.append(ul);
          }
        });
      });
      if (rec.omitted) {
        const more = el("p", "ref__more");
        more.append(
          document.createTextNode(
            rec.omitted === 1
              ? "1 længere beskrivelse er ikke med her. Se den hos "
              : `${rec.omitted} længere beskrivelser er ikke med her. Se dem hos `
          )
        );
        const a = el("a", null, "Valve");
        a.href = "https://www.dota2.com/patches/7.42";
        more.append(a, document.createTextNode("."));
        body.append(more);
      }
    };

    const itemNode = (rec) => {
      const d = el("details", "ref__item");
      d.dataset.name = rec.name;
      const s = el("summary", "ref__sum");
      s.append(el("span", "ref__name", rec.name));
      s.append(el("span", "ref__n", rec.n === 1 ? "1 linje" : `${rec.n} linjer`));
      const body = el("div", "ref__body");
      d.append(s, body);
      d.addEventListener("toggle", () => {
        if (d.open && !body.hasChildNodes()) fillBody(body, rec);
      });
      return d;
    };

    const render = () => {
      const q = state.q.trim().toLowerCase();
      let rows = state.cat.rows.filter((r) => !q || r.hay.includes(q));
      if (state.cat.sortable && state.sort === "most") rows = rows.slice().sort((a, b) => b.n - a.n || a.name.localeCompare(b.name));
      else rows = rows.slice().sort((a, b) => a.name.localeCompare(b.name, "en"));

      refList.replaceChildren();
      if (!rows.length) {
        refList.append(el("p", "ref__empty", "Ingen træffere. Prøv et andet navn."));
      } else {
        const frag = document.createDocumentFragment();
        rows.forEach((r) => frag.append(itemNode(r)));
        refList.append(frag);
      }
      count.textContent = q
        ? `${rows.length} af ${state.cat.rows.length} ${state.cat.noun}`
        : `${rows.length} ${state.cat.noun}`;
      sortBox.hidden = !state.cat.sortable;
    };

    const markPressed = (box, attr, value) =>
      $$("button", box).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset[attr] === value)));

    categories.forEach((c) => {
      const b = el("button", "btn");
      b.type = "button";
      b.dataset.c = c.id;
      b.setAttribute("aria-pressed", String(c === state.cat));
      b.append(c.label);
      b.append(el("span", "chips__count", String(c.rows.length)));
      b.addEventListener("click", () => {
        state.cat = c;
        markPressed(tabsBox, "c", c.id);
        render();
      });
      tabsBox.append(b);
    });

    [
      ["az", "A til Å"],
      ["most", "Flest ændringer"],
    ].forEach(([id, label]) => {
      const b = el("button", "btn", label);
      b.type = "button";
      b.dataset.s = id;
      b.setAttribute("aria-pressed", String(id === state.sort));
      b.addEventListener("click", () => {
        state.sort = id;
        markPressed(sortBox, "s", id);
        render();
      });
      sortBox.append(b);
    });

    query.addEventListener("input", () => {
      state.q = query.value;
      render();
    });

    render();

    /* Links with data-hero jump straight to that hero. */
    $$("[data-hero]").forEach((a) => {
      a.addEventListener("click", (ev) => {
        const name = a.dataset.hero;
        if (!heroes.some((h) => h.name === name)) return;
        ev.preventDefault();
        state.cat = categories[0];
        state.q = name;
        query.value = name;
        markPressed(tabsBox, "c", "heroes");
        render();
        const target = $(".ref__item", refList);
        if (target) {
          target.open = true;
          $("#ref").scrollIntoView({ behavior: reduceMotion ? "auto" : "smooth", block: "start" });
        }
      });
    });
  }

  /* Fix list: filter by category. */
  const fixList = $("#fixes");
  const chipBox = $("#chips");
  if (fixList && chipBox) {
    const items = $$("li", fixList);
    const cats = ["Alle", ...new Set(items.map((li) => li.dataset.c))];

    const apply = (cat) => {
      items.forEach((li) => {
        li.hidden = cat !== "Alle" && li.dataset.c !== cat;
      });
      $$("button", chipBox).forEach((b) => b.setAttribute("aria-pressed", String(b.dataset.f === cat)));
    };

    cats.forEach((cat) => {
      const count = cat === "Alle" ? items.length : items.filter((li) => li.dataset.c === cat).length;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "btn";
      btn.dataset.f = cat;
      btn.setAttribute("aria-pressed", "false");
      btn.append(cat);
      const n = document.createElement("span");
      n.className = "chips__count";
      n.textContent = String(count);
      btn.append(n);
      btn.addEventListener("click", () => apply(cat));
      chipBox.append(btn);
    });

    apply("Alle");
  }
})();
