/* Kervillage — fiche dynamique des lieux-dits (lieu.html?d=XX&i=NNN). */
(function () {
  "use strict";
  var params = new URLSearchParams(window.location.search);
  var dept = params.get("d");
  var i = parseInt(params.get("i"), 10);
  var B = window.KERVILLAGE_BRIQUES;

  var DEPTS = { "22": "Côtes-d'Armor", "29": "Finistère", "35": "Ille-et-Vilaine",
                "44": "Loire-Atlantique", "56": "Morbihan" };
  var TYPES = { commune: "Commune", town: "Ville", village: "Village", hamlet: "Lieu-dit" };

  function fold(s) {
    if (!s) return "";
    return s.replace(/œ/g, "oe").replace(/æ/g, "ae").replace(/[’']/g, "-")
      .normalize("NFD").replace(/[̀-ͯ]/g, "")
      .toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-+|-+$/g, "");
  }

  // portage strict du matching python (build.py -> decompose)
  function decompose(nom) {
    var s = fold(nom);
    if (!s || B.exclude.indexOf(s) !== -1) return [];
    var prefixes = B.briques.filter(function (b) { return b.position === "prefix"; });
    var suffixes = B.briques.filter(function (b) { return b.position === "suffix"; });
    function formsDesc(b) { return b.matchForms.slice().sort(function (a, c) { return c.length - a.length; }); }
    // le nom entier est une brique (Kemper, Breizh…)
    for (var w = 0; w < B.briques.length; w++) {
      if (B.briques[w].matchForms.indexOf(s) !== -1) {
        return [{ t: "brique", surface: s, brique: B.briques[w] }];
      }
    }
    var segs = [], rest = s, changed = true;
    while (changed && rest) {
      changed = false;
      for (var p = 0; p < prefixes.length && !changed; p++) {
        var fs = formsDesc(prefixes[p]);
        for (var k = 0; k < fs.length; k++) {
          var f = fs[k];
          if (rest.indexOf(f) === 0 && rest.length - f.length >= 3) {
            segs.push({ t: "brique", surface: rest.slice(0, f.length), brique: prefixes[p] });
            rest = rest.slice(f.length).replace(/^-+/, "");
            changed = true;
            break;
          }
        }
      }
    }
    var tail = [];
    changed = true;
    while (changed && rest) {
      changed = false;
      for (var p2 = 0; p2 < suffixes.length && !changed; p2++) {
        var fs2 = formsDesc(suffixes[p2]);
        for (var k2 = 0; k2 < fs2.length; k2++) {
          var f2 = fs2[k2];
          var avant = rest.length - f2.length;
          if (rest.slice(-f2.length) === f2 && (avant >= 2 || (avant === 0 && segs.length))) {
            tail.unshift({ t: "brique", surface: rest.slice(-f2.length), brique: suffixes[p2] });
            rest = rest.slice(0, rest.length - f2.length).replace(/-+$/, "");
            changed = true;
            break;
          }
        }
      }
    }
    if (rest) segs.push({ t: "reste", surface: rest });
    segs = segs.concat(tail);
    if (!segs.some(function (g) { return g.t === "brique"; })) return [];
    return segs;
  }

  function sensPhrase(segs) {
    var briques = segs.filter(function (g) { return g.t === "brique"; });
    var restes = segs.filter(function (g) { return g.t === "reste"; });
    if (!briques.length) return "";
    var courts = briques.map(function (g) {
      return "« " + g.surface + " » : " + g.brique.court + (g.brique.probable ? " (sens probable)" : "");
    });
    var phrase = "On y retrouve " + courts.join(" et ") + ".";
    if (restes.length) {
      phrase += " Le reste du nom (« " + restes.map(function (g) { return g.surface; }).join(" », « ") +
        " ») n'a pas de lecture certaine.";
    }
    return phrase;
  }

  function sourceLabel(src) {
    if (src === "osm+wikidata") return "OpenStreetMap (ODbL) + Wikidata (CC0)";
    if (src === "wikidata") return "Wikidata (CC0)";
    return "OpenStreetMap (ODbL)";
  }

  function el(id) { return document.getElementById(id); }

  fetch("/data/lieux-" + dept + ".json")
    .then(function (r) { return r.json(); })
    .then(function (lst) {
      var e = lst[i];
      if (!e) { el("lieu-type").textContent = "Lieu introuvable."; return; }
      var nom = e.nom_br || e.nom_fr;
      var nomFr = e.nom_fr || e.nom_br;

      if (e.departement_nom) {
        el("fil-dept").innerHTML = " · " + e.departement_nom;
      }
      el("lieu-type").textContent = (TYPES[e.type] || e.type) + (e.nom_fr && e.nom_fr !== nom ? " · " + e.nom_fr : "");
      el("lieu-nom").textContent = nom;
      document.title = nom + " — un lieu de Bretagne en breton | Kervillage";

      var segs = decompose(nom);
      var sens = sensPhrase(segs);
      el("lieu-sens").textContent = sens;
      if (segs.length) {
        el("lieu-briques").hidden = false;
        var wrap = el("lieu-chips");
        segs.forEach(function (g) {
          var chip, surf, sensEl;
          if (g.t === "brique") {
            chip = document.createElement("a");
            chip.className = "brique";
            chip.href = "/decodeur.html#" + g.brique.anchor;
            chip.title = g.brique.titre + " : " + g.brique.court;
          } else {
            chip = document.createElement("span");
            chip.className = "brique brique--reste";
          }
          surf = document.createElement("span");
          surf.className = "brique__surf";
          surf.lang = "br";
          surf.textContent = g.surface;
          sensEl = document.createElement("span");
          sensEl.className = "brique__sens";
          sensEl.textContent = g.t === "brique"
            ? g.brique.court + (g.brique.probable ? " probable" : "")
            : "non décodé";
          chip.appendChild(surf);
          chip.appendChild(sensEl);
          wrap.appendChild(chip);
        });
      }

      el("lieu-source").textContent = "Source : " + sourceLabel(e.source);
      var ul = el("lieu-liens");
      if (e.url_source) {
        var li = document.createElement("li");
        li.innerHTML = '<a href="' + e.url_source + '" rel="noopener">Fiche d\'origine</a>';
        ul.appendChild(li);
      }
      if (e.brwiki) {
        var li2 = document.createElement("li");
        li2.innerHTML = '<a href="' + e.brwiki + '" rel="noopener">Article sur Wikipédia en breton</a> (CC BY-SA)';
        ul.appendChild(li2);
      }
      var li3 = document.createElement("li");
      li3.innerHTML = '<a href="/sources.html">Comment ces informations sont rassemblées</a>';
      ul.appendChild(li3);

      window.KERVILLAGE_FICHE = {
        nomFr: nomFr,
        nomBr: nom,
        sens: sens || ("Forme bretonne : " + nom + "."),
        url: "https://kervillage.brozapi.com" + window.location.pathname + window.location.search
      };
    })
    .catch(function () {
      el("lieu-type").textContent = "Impossible de charger les données de ce lieu.";
    });
})();
