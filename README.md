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

De formulieren (contact, offerte, homepage) versturen via
[FormSubmit](https://formsubmit.co) naar `info@niya-solutions.be`
(instelling `FORM_ENDPOINT` bovenaan `assets/js/main.js`).
**Bij de allereerste inzending stuurt FormSubmit een activatiemail naar
info@niya-solutions.be — die één keer bevestigen, daarna komen alle berichten binnen.**

## Opnieuw bouwen

```
python3 tools/fetch_forms.py   # (optioneel) formuliervragen ophalen
python3 tools/build.py         # genereert alle pagina's uit tools/source/
```

## Live zetten op niya-solutions.be (GitHub Pages)

1. Repo → Settings → Pages → Deploy from branch `main` / root.
2. Custom domain: `www.niya-solutions.be` (GitHub maakt dan een `CNAME`-bestand).
3. DNS bij de domeinregistrar: `CNAME www → <gebruiker>.github.io` en
   A-records voor het kale domein naar 185.199.108.153, .109.153, .110.153, .111.153.
