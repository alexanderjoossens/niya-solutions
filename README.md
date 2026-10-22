# niya-solutions.be

Statische website van **Niya Solutions** (facility management, projectmanagement,
schoonmaak en kluswerken). Visueel identiek aan de vorige Webhero-site, maar zonder
CMS: gewone HTML/CSS/JS die overal gehost kan worden (GitHub Pages, Netlify, …).

## Structuur

```
index.html                 homepage
<pagina>/index.html        elke pagina in een eigen map (propere URL's: /over-ons/)
assets/css/style.css       stylesheet
assets/js/main.js          menu, dropdowns, lazy images, FAQ, formulieren, cookies
assets/img, video, fonts, icons
tools/                     build-script + bronpagina's van de oude site
```

Alle interne links zijn relatief, dus de site werkt zowel op
`https://www.niya-solutions.be/` als in een submap (bv. GitHub Pages-preview).

## Formulieren

De formulieren (contact, offerte, homepage) versturen via de centrale AlexWeb-dienst
`forms.alexweb.be` (site-id `niya-solutions` in `site-form-mailer/sites.json`) naar
`info@niya-solutions.be`, met spamfilter (ondertekend token, honeypot, spamscore, limieten).
Instelling `FORMS_URL` / `FORM_SITE` bovenaan `assets/js/main.js`.

## Opnieuw bouwen

```
python3 tools/fetch_forms.py   # (optioneel) formuliervragen ophalen
python3 tools/build.py         # genereert alle pagina's uit tools/source/
```

## Live zetten

Gehost op Railway (project `niya-solutions`), deployt automatisch bij een push naar `main`.
DNS bij Hostinger: `www` CNAME en `@` ALIAS naar Railway; mail blijft bij Microsoft 365.
