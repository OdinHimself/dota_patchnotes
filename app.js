(() => {
  "use strict";

  const $ = (sel, root = document) => root.querySelector(sel);
  const $$ = (sel, root = document) => Array.from(root.querySelectorAll(sel));
  const reduceMotion = window.matchMedia("(prefers-reduced-motion: reduce)").matches;

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
      shard.textContent = deaths >= 1 ? "Sikret" : "Ikke sikret";
    };

    tmRange.addEventListener("input", updateTormentor);
    updateTormentor();
  }

  /* Item Potency: pick who attacks, see how much of the effect gets through. */
  const potButtons = $$("[data-p]");
  if (potButtons.length) {
    const fill = $("#pot-fill");
    const value = $("#pot-v");
    const text = $("#pot-text");

    const selectPotency = (btn) => {
      const pct = Number(btn.dataset.p);
      potButtons.forEach((b) => b.setAttribute("aria-pressed", String(b === btn)));
      fill.style.width = `${pct}%`;
      value.textContent = `${pct}%`;
      text.textContent =
        pct === 100
          ? "En helt bruger on-hit-effekter med fuld styrke."
          : `${btn.dataset.n} bruger on-hit-effekter med ${pct}% af styrken.`;
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
