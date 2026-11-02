/* The JSON API keeps its original language tags; this only localizes the two public pages. */
(() => {
  const french = {
    landingTitle: "API de métadonnées des Simpson · Données ouvertes de Springfield",
    landingDescription: "Métadonnées des épisodes, saisons, films et courts métrages des Simpson en JSON public. Aucune clé API requise.",
    guideTitle: "Guide des épisodes · Métadonnées des Simpson",
    guideDescription: "Parcourez les épisodes, films et courts métrages des Simpson avec leurs titres, références et liens Disney+.",
    skipContent: "Aller au contenu",
    skipCatalogue: "Aller au catalogue",
    brandSmall: "API JSON publique",
    brandHome: "Accueil de l’API de métadonnées des Simpson",
    primaryNav: "Navigation principale",
    navGuide: "Guide des épisodes",
    navDatasets: "Jeux de données",
    navApi: "Référence de l’API ↗",
    navHome: "Accueil",
    navJson: "JSON brut",
    heroEyebrow: "Données ouvertes · version 1",
    heroLead: "Springfield,",
    heroEm: "en données structurées.",
    heroLede: "Explorez les épisodes, saisons, films et autres données des <em>Simpson</em> dans des fichiers JSON publics. Prêts à utiliser dans votre projet, sans compte ni clé API.",
    browseGuide: "Parcourir le guide →",
    exploreDatasets: "Explorer les jeux de données",
    factReadOnly: "JSON en lecture seule",
    factHttpsCors: "HTTPS + CORS",
    factNoKey: "Aucune clé API",
    sampleAria: "Exemple de réponse JSON",
    openJson: "Ouvrir le JSON ↗",
    sampleNote: "Extrait de réponse · les entrées sont indexées par identifiant",
    catalogueKicker: "Parcourir le catalogue",
    pickDataset: "Choisissez un jeu de données.",
    datasetIntro: "Chaque lien ouvre un objet JSON complet. <a href=\"/episodes/\" data-page-link=\"/episodes/\">Parcourez les tableaux du guide</a> ou téléchargez un jeu de données pour rechercher des identifiants dans votre code.",
    datasetEpisodes: "Épisodes",
    descEpisodes: "Épisodes réguliers de la série",
    datasetSeasons: "Saisons",
    descSeasons: "Catalogue des saisons",
    datasetMovies: "Films",
    descMovies: "Films sortis et annoncés",
    datasetTracey: "Courts métrages du Tracey Ullman Show",
    descTracey: "Premiers courts métrages d’animation",
    datasetDisney: "Courts métrages Disney+",
    descDisney: "Courts métrages disponibles sur Disney+",
    datasetCommercials: "Publicités",
    descCommercials: "Apparitions publicitaires",
    datasetSpecials: "Émissions spéciales",
    descSpecials: "Autres sorties hors série",
    coverageNote: "<strong>À propos de la couverture :</strong> Certains jeux de données sont encore vides et renvoient <code>{}</code>. Les champs inconnus sont omis; un lien <code>null</code> indique que l’absence de cette destination a été vérifiée.",
    requestKicker: "Faire une requête",
    startFetch: "Commencez par un seul fetch.",
    fetchIntro: "Les réponses sont indexées par des identifiants comme <code>s01e01</code>. Il n’y a ni URL par entrée ni filtre côté serveur : récupérez un jeu de données, puis interrogez-le localement.",
    exploreEndpoints: "Explorer tous les points d’accès dans la référence de l’API →",
    jsExample: "Exemple JavaScript",
    moreKicker: "Pour aller plus loin",
    exploreIntegrate: "Explorer et intégrer.",
    findRecord: "Trouver une entrée",
    findIntro: "Les index de production, TVDB, TMDB et IMDb relient un identifiant externe à son jeu de données et à son identifiant interne.",
    openProduction: "Ouvrir l’index de production →",
    inspectContract: "Consulter l’API",
    inspectIntro: "Parcourez la référence interactive ou consultez la description OpenAPI lisible par machine.",
    openApi: "Ouvrir la référence de l’API →",
    trackChanges: "Suivre les changements",
    trackIntro: "Le manifeste répertorie les fichiers publiés et leurs empreintes SHA-256 pour les clients qui mettent les données en cache.",
    viewManifest: "Voir le manifeste →",
    footerLanding: "Métadonnées fournies sous <a href=\"https://github.com/thewade/simpsons-metadata/blob/main/LICENSE-DATA.md\">CC BY 4.0</a>. Ce projet n’est pas affilié aux ayants droit des <em>Simpson</em>.",
    sourceContrib: "Code source et contributions",
    guideEyebrow: "Parcourir le catalogue",
    guideHeading: "Guide des épisodes",
    guideIntro: "{episodes} épisodes numérotés répartis sur {seasons} saisons, ainsi que {movies} films et {shorts} courts métrages. Sélectionnez une ligne pour voir les titres, les références et les liens Disney+ disponibles.",
    classic: "Saisons 1 à 20",
    modern: "À partir de la saison 21",
    movies: "Films",
    traceyShorts: "Courts métrages du Tracey Ullman Show",
    disneyShorts: "Courts métrages Disney+",
    downloadEpisodes: "Télécharger episodes.json ↗",
    jumpSeason: "Aller à une saison",
    guideNote: "<strong>À propos des liens :</strong> Les liens Disney+ sont créés à partir des identifiants enregistrés. Leur fonctionnement actuel n’a pas été revérifié et la disponibilité dépend de la région et de l’abonnement. Les dates prévues des films sont indiquées.",
    guideNoScript: "Activez JavaScript pour développer les lignes. La <a href=\"/docs/\">référence de l’API</a> donne accès aux jeux de données JSON complets.",
    episodeCatalogue: "Catalogue des épisodes",
    seasonLabel: "Saison {number}",
    numberedEpisodes: "{count} épisodes numérotés",
    englishArticle: "Article en anglais ↗",
    frenchArticle: "Article en français ↗",
    noNumberedEpisodes: "Aucun épisode numéroté pour cette saison.",
    overall: "N° global",
    number: "N°",
    episode: "Épisode",
    originalAirDate: "Première diffusion",
    productionCode: "Code de production",
    details: "Détails",
    beyondEpisodes: "Au-delà des épisodes numérotés",
    moviesIntro: "Longs métrages, y compris les sorties annoncées.",
    traceyIntro: "Les premiers courts métrages télévisés, classés par date de première diffusion.",
    disneyIntro: "Courts métrages disponibles sur Disney+, y compris ceux d’abord sortis au cinéma.",
    recordsCount: "{count} entrées.",
    downloadJson: "Télécharger le JSON ↗",
    film: "Film",
    short: "Court métrage",
    releaseDate: "Date de sortie",
    firstRelease: "Première sortie",
    planned: "(prévue)",
    englishTitle: "Titre anglais",
    titleLanguage: "Titre ({language})",
    aspectRatio: "Format d’image original",
    wikiEnglish: "Wikipédia (anglais) ↗",
    wikiFrench: "Wikipédia (français) ↗",
    noWikiEnglish: "Aucun article individuel sur Wikipédia en anglais",
    openDisney: "Ouvrir sur Disney+ ↗",
    amazonDvd: "DVD sur Amazon ↗",
    amazonBluray: "Blu-ray sur Amazon ↗",
    noExternalLinks: "Aucun lien externe enregistré.",
    archivedFields: "Champs de la source historique",
    episodeDetails: "Détails de l’épisode",
    filmDetails: "Détails du film",
    shortDetails: "Détails du court métrage",
    linkEpisode: "Lien vers l’épisode",
    linkFilm: "Lien vers le film",
    linkShort: "Lien vers le court métrage",
    noRecords: "Aucune entrée pour le moment.",
    footerGuide: "Métadonnées fournies sous <a href=\"https://github.com/thewade/simpsons-metadata/blob/main/LICENSE-DATA.md\">CC BY 4.0</a>.",
    apiHome: "Accueil de l’API",
  };

  function normalizeLocale(value) {
    const tag = (value || "").toLowerCase();
    if (tag === "fr-ca" || tag.startsWith("fr-ca-")) return "fr-CA";
    if (tag === "fr" || tag.startsWith("fr-")) return "fr-FR";
    if (tag === "en" || tag.startsWith("en-")) return "en";
    return null;
  }

  function storedLocale() {
    try { return normalizeLocale(localStorage.getItem("simpsons-locale")); }
    catch { return null; }
  }

  function initialLocale() {
    const explicit = normalizeLocale(new URLSearchParams(location.search).get("lang"));
    if (explicit) return explicit;
    const saved = storedLocale();
    if (saved) return saved;
    for (const language of navigator.languages?.length ? navigator.languages : [navigator.language]) {
      const found = normalizeLocale(language);
      if (found) return found;
    }
    return "en";
  }

  const originals = new Map();
  const defaultTitle = document.title;
  function original(element, attribute) {
    if (!originals.has(element)) originals.set(element, {});
    const values = originals.get(element);
    if (!(attribute in values)) values[attribute] = attribute === "html" ? element.innerHTML
      : attribute === "aria" ? element.getAttribute("aria-label") : element.textContent;
    return values[attribute];
  }

  function interpolate(value, element) {
    return value.replace(/\{([a-zA-Z]+)\}/g, (_, key) => element.dataset[key] ?? "");
  }

  function applyLocale(locale) {
    document.documentElement.lang = locale;
    const text = locale === "en" ? null : french;
    for (const element of document.querySelectorAll("[data-i18n]")) {
      const fallback = original(element, "text");
      element.textContent = text?.[element.dataset.i18n]
        ? interpolate(text[element.dataset.i18n], element) : fallback;
    }
    for (const element of document.querySelectorAll("[data-i18n-html]")) {
      const fallback = original(element, "html");
      element.innerHTML = text?.[element.dataset.i18nHtml]
        ? interpolate(text[element.dataset.i18nHtml], element) : fallback;
    }
    for (const element of document.querySelectorAll("[data-i18n-aria]")) {
      const fallback = original(element, "aria");
      element.setAttribute("aria-label", text?.[element.dataset.i18nAria] || fallback);
    }
    const page = document.body.dataset.page;
    document.title = text?.[page + "Title"] || defaultTitle;
    const description = document.querySelector('meta[name="description"]');
    if (description) {
      if (!originals.has(description)) originals.set(description, {content: description.content});
      description.content = text?.[page + "Description"] || originals.get(description).content;
    }
    const formatter = new Intl.DateTimeFormat(locale === "en" ? "en-US" : locale,
      {year: "numeric", month: "long", day: "numeric", timeZone: "UTC"});
    for (const time of document.querySelectorAll("time[datetime]")) {
      time.textContent = formatter.format(new Date(time.dateTime + "T00:00:00Z"));
    }
    for (const button of document.querySelectorAll(".episode-toggle[data-title-en]")) {
      const title = locale === "fr-CA" ? button.dataset.titleFrCa
        : locale === "fr-FR" ? button.dataset.titleFrFr : button.dataset.titleEn;
      button.textContent = title;
      document.getElementById(button.getAttribute("aria-controls"))?.querySelector(".detail-top h4")
        ?.replaceChildren(document.createTextNode(title));
    }
    for (const field of document.querySelectorAll("[data-english-title]")) {
      field.hidden = locale === "en";
    }
    const sampleTitle = document.getElementById("sample-title");
    if (sampleTitle) {
      const title = locale === "fr-CA" ? sampleTitle.dataset.titleFrCa
        : locale === "fr-FR" ? sampleTitle.dataset.titleFrFr : sampleTitle.dataset.titleEn;
      document.getElementById("sample-title-language").textContent = JSON.stringify(locale);
      sampleTitle.textContent = JSON.stringify(title);
      document.getElementById("sample-js-language").textContent = locale;
      document.getElementById("sample-js-title").textContent = "// " + title;
    }
    for (const link of document.querySelectorAll("a[data-page-link]")) {
      const url = new URL(link.dataset.pageLink, location.href);
      url.searchParams.set("lang", locale);
      link.href = url.pathname + url.search + url.hash;
    }
    const picker = document.getElementById("language-select");
    if (picker) picker.value = locale;
  }

  const selected = initialLocale();
  applyLocale(selected);
  document.getElementById("language-select")?.addEventListener("change", event => {
    const locale = normalizeLocale(event.target.value) || "en";
    try { localStorage.setItem("simpsons-locale", locale); } catch { /* Private browsing may block storage. */ }
    const url = new URL(location.href);
    url.searchParams.set("lang", locale);
    history.replaceState(null, "", url);
    applyLocale(locale);
  });
})();
