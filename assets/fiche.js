/* Kervillage — boutons de partage des fiches (statiques et dynamiques). */
(function () {
  "use strict";
  var fiche = window.KERVILLAGE_FICHE;
  var btn = document.getElementById("btn-partage");
  var btnLien = document.getElementById("btn-lien");
  var statut = document.getElementById("partage-statut");

  function dire(msg) { if (statut) statut.textContent = msg; }

  if (btn) {
    btn.addEventListener("click", function () {
      if (!fiche || typeof KVPartage === "undefined") { dire("Partage indisponible."); return; }
      try {
        var canvas = KVPartage.genererImage(fiche);
        var nom = "kervillage-" + fiche.nomBr.toLowerCase().replace(/[^a-z0-9]+/g, "-") + ".png";
        KVPartage.telecharger(canvas, nom);
        dire("Image téléchargée. Le lien à coller avec : " + fiche.url);
      } catch (e) {
        dire("La génération de l'image a échoué dans ce navigateur.");
      }
    });
  }
  if (btnLien) {
    btnLien.addEventListener("click", function () {
      if (!fiche) return;
      var done = function () { dire("Lien copié : " + fiche.url); };
      if (navigator.clipboard && navigator.clipboard.writeText) {
        navigator.clipboard.writeText(fiche.url).then(done, function () { dire("Copie impossible — le lien : " + fiche.url); });
      } else {
        var t = document.createElement("textarea");
        t.value = fiche.url;
        document.body.appendChild(t);
        t.select();
        try { document.execCommand("copy"); done(); } catch (e) { dire("Le lien : " + fiche.url); }
        t.remove();
      }
    });
  }
})();
