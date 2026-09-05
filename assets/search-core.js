/* Kervillage — moteur de recherche (pur, testable sous Node).
   Insensible aux accents et a la casse, tolerance legere aux fautes. */
(function (root, factory) {
  if (typeof module === "object" && module.exports) module.exports = factory();
  else root.KVSearch = factory();
})(typeof self !== "undefined" ? self : this, function () {
  "use strict";

  function fold(s) {
    if (!s) return "";
    return s
      .replace(/œ/g, "oe").replace(/æ/g, "ae").replace(/[’']/g, "-")
      .normalize("NFD").replace(/[\u0300-\u036f]/g, "")
      .toLowerCase()
      .replace(/[^a-z0-9]+/g, "-")
      .replace(/^-+|-+$/g, "");
  }

  // distance de Damerau-Levenshtein (OSA, borne max : coupe tot)
  function dl(a, b, max) {
    if (Math.abs(a.length - b.length) > max) return max + 1;
    var i, j;
    var prev2 = null, prev = [], cur = [];
    for (j = 0; j <= b.length; j++) prev[j] = j;
    for (i = 1; i <= a.length; i++) {
      cur[0] = i;
      var rowMin = cur[0];
      for (j = 1; j <= b.length; j++) {
        var cost = a[i - 1] === b[j - 1] ? 0 : 1;
        var v = Math.min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + cost);
        if (i > 1 && j > 1 && a[i - 1] === b[j - 2] && a[i - 2] === b[j - 1]) {
          v = Math.min(v, prev2[j - 2] + 1);
        }
        cur[j] = v;
        if (v < rowMin) rowMin = v;
      }
      if (rowMin > max) return max + 1;
      prev2 = prev;
      prev = cur;
      cur = [];
    }
    return prev[b.length];
  }

  function scoreOne(candidate, q) {
    if (!candidate) return -1;
    if (candidate === q) return 0;
    if (candidate.indexOf(q) === 0) return 5;
    if (candidate.indexOf("-" + q) !== -1) return 8;
    var max = q.length <= 8 ? 1 : 2;
    var best = max + 1;
    var candTokens = candidate.split("-");
    var qTokens = q.split("-");
    for (var qi = 0; qi < qTokens.length; qi++) {
      var qt = qTokens[qi];
      if (qt.length < 4) continue; // pas de fuzzy sur les tokens tres courts
      var mt = qt.length <= 8 ? 1 : 2;
      for (var ci = 0; ci < candTokens.length; ci++) {
        var d = dl(qt, candTokens[ci], mt);
        if (d < best) best = d;
      }
    }
    if (best <= max) return 20 + best;
    return -1;
  }

  // entry : {n, b, s, q, d, t, u} ; retourne -1 si aucune correspondance
  function score(entry, queryFolded) {
    var s1 = scoreOne(entry.s, queryFolded);
    var s2 = scoreOne(entry.q, queryFolded);
    var best = -1;
    if (s1 >= 0) best = s1;
    if (s2 >= 0 && (best < 0 || s2 < best)) best = s2;
    return best;
  }

  function search(index, query, limit) {
    var q = fold(query);
    if (q.length < 2) return [];
    var out = [];
    for (var i = 0; i < index.length; i++) {
      var sc = score(index[i], q);
      if (sc >= 0) out.push({ e: index[i], sc: sc });
    }
    // score, puis les communes d'abord, puis ordre alphabetique
    out.sort(function (a, b) {
      return a.sc - b.sc
        || ((a.e.t === "commune" ? 0 : 1) - (b.e.t === "commune" ? 0 : 1))
        || (a.e.n < b.e.n ? -1 : 1);
    });
    return out.slice(0, limit || 8).map(function (x) { return x.e; });
  }

  return { fold: fold, search: search, dl: dl };
});
