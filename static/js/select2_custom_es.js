(function () {
  if (jQuery && jQuery.fn && jQuery.fn.select2 && jQuery.fn.select2.amd) {
    var e = jQuery.fn.select2.amd;
    e.define("select2/i18n/es", [], function () {
      // Sobrescribimos las traducciones por defecto de Select2 para español
      return {
        errorLoading: function () {
          return "No se pudieron cargar los resultados";
        },
        inputTooLong: function (e) {
          var t = e.input.length - e.maximum,
            n = "Por favor, elimine " + t + " car";
          return (n += 1 == t ? "ácter" : "acteres");
        },
        // --- INICIO: ESTA ES LA TRADUCCIÓN QUE QUEREMOS CAMBIAR ---
        inputTooShort: function (e) {
          var t = e.minimum - e.input.length,
            n = "Por favor, ingrese " + t + " o más car";
          return (n += 1 == t ? "acteres" : "acteres");
        },
        // --- FIN: ESTA ES LA TRADUCCIÓN QUE QUEREMOS CAMBIAR ---
        loadingMore: function () {
          return "Cargando más resultados…";
        },
        maximumSelected: function (e) {
          var t = "Sólo puede seleccionar " + e.maximum + " elemento";
          return 1 != e.maximum && (t += "s"), t;
        },
        noResults: function () {
          return "No se encontraron resultados";
        },
        searching: function () {
          return "Buscando…";
        },
        removeAllItems: function () {
          return "Eliminar todos los elementos";
        },
      };
    });
  }
})();
