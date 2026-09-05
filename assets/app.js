/* Kervillage — branchement DOM de la recherche (toutes les pages avec #champ). */
(function () {
  "use strict";
  var champ = document.getElementById("champ");
  var liste = document.getElementById("resultats");
  if (!champ || !liste || typeof KVSearch === "undefined") return;

  var index = null;
  var chargement = null;
  var actif = -1;

  var DEPTS = { "22": "Côtes-d'Armor", "29": "Finistère", "35": "Ille-et-Vilaine",
                "44": "Loire-Atlantique", "56": "Morbihan" };
  var TYPES = { commune: "Commune", town: "Ville", village: "Village", hamlet: "Lieu-dit" };

  function charger() {
    if (index) return Promise.resolve(index);
    if (!chargement) {
      chargement = fetch("/data/search.json").then(function (r) { return r.json(); })
        .then(function (d) { index = d; return d; });
    }
    return chargement;
  }

  function vider() {
    liste.innerHTML = "";
    liste.hidden = true;
    actif = -1;
  }

  function rendre(resultats) {
    liste.innerHTML = "";
    if (!resultats.length) {
      var li = document.createElement("li");
      var sp = document.createElement("span");
      sp.style.cssText = "display:block;padding:.65rem 1rem;color:#4C6267";
      sp.textContent = "Aucun résultat — essaie sans les accents, ou avec le nom breton.";
      li.appendChild(sp);
      liste.appendChild(li);
      liste.hidden = false;
      return;
    }
    resultats.forEach(function (e, i) {
      var li = document.createElement("li");
      li.setAttribute("role", "option");
      var a = document.createElement("a");
      a.href = "/" + e.u;
      var gauche = document.createElement("span");
      var fr = document.createElement("span");
      fr.className = "res__fr";
      fr.textContent = e.n;
      gauche.appendChild(fr);
      if (e.b && e.b !== e.n) {
        gauche.appendChild(document.createTextNode(" — "));
        var br = document.createElement("span");
        br.className = "res__br";
        br.lang = "br";
        br.textContent = e.b;
        gauche.appendChild(br);
      }
      var meta = document.createElement("span");
      meta.className = "res__meta";
      meta.textContent = (TYPES[e.t] || e.t) + " · " + (DEPTS[e.d] || e.d);
      a.appendChild(gauche);
      a.appendChild(meta);
      a.addEventListener("mouseenter", function () { selectionner(i); });
      li.appendChild(a);
      liste.appendChild(li);
    });
    liste.hidden = false;
    actif = -1;
  }

  function selectionner(i) {
    var liens = liste.querySelectorAll("a");
    if (!liens.length) return;
    actif = (i + liens.length) % liens.length;
    liens.forEach(function (a, j) {
      a.setAttribute("aria-selected", j === actif ? "true" : "false");
    });
  }

  var timer = null;
  champ.addEventListener("input", function () {
    var q = champ.value;
    clearTimeout(timer);
    if (q.trim().length < 2) { vider(); return; }
    timer = setTimeout(function () {
      charger().then(function () { rendre(KVSearch.search(index, q, 8)); });
    }, 120);
  });

  champ.addEventListener("keydown", function (ev) {
    if (liste.hidden) return;
    if (ev.key === "ArrowDown") { ev.preventDefault(); selectionner(actif + 1); }
    else if (ev.key === "ArrowUp") { ev.preventDefault(); selectionner(actif - 1); }
    else if (ev.key === "Enter" && actif >= 0) {
      ev.preventDefault();
      var liens = liste.querySelectorAll("a");
      if (liens[actif]) window.location.href = liens[actif].href;
    } else if (ev.key === "Escape") { vider(); }
  });

  document.addEventListener("click", function (ev) {
    if (!liste.contains(ev.target) && ev.target !== champ) vider();
  });

  // prechargement discret des donnees des que la page est calme
  if ("requestIdleCallback" in window) requestIdleCallback(function () { charger(); }, { timeout: 4000 });
})();
