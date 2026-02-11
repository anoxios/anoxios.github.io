# Ghid pas cu pas: Site cu writeup-uri CTF pe amariei.org

Ai domeniul **amariei.org** pe Namecheap și vrei să publici soluții CTF explicate frumos. Mai jos e planul pas cu pas.

---

## Pasul 1: Alege cum hostezi site-ul (fără să plătești hosting separat)

Poți folosi **hosting gratuit** și doar să „îndrepți” domeniul tău către el.

### Opțiunea A (recomandată): **GitHub Pages**
- **Cost:** 0 lei
- **Idea:** Repo pe GitHub → site static (HTML/CSS/JS sau Markdown convertit).
- **Plusuri:** Simplu, versiune (git), poți edita writeup-urile în Markdown.

### Opțiunea B: **Netlify** sau **Vercel**
- **Cost:** 0 lei (plan free)
- **Idea:** Conectezi un repo GitHub; la fiecare push se reconstruiește site-ul.
- **Plusuri:** Deploy automat, SSL, redirect-uri, formulare (Netlify).

**Recomandare:** Începe cu **GitHub Pages** – un singur loc (GitHub) pentru cod + writeup-uri, apoi le poți lega de amariei.org.

---

## Pasul 2: Creează un repo pentru site-ul de writeup-uri

1. Mergi pe [github.com](https://github.com) și creează un repo nou, de exemplu: **`ctf-writeups`** sau **`amariei-blog`**.
2. Fă-l **Public**.
3. Adaugă un **README.md** dacă vrei (poți scrie „CTF writeups – amariei.org”).

Acest repo va conține:
- pagini de writeup (Markdown sau HTML),
- (opțional) un generator de site static sau un theme pentru „blog”.

---

## Pasul 3: Alege cum arată site-ul („frumos explicate”)

Două căi simple:

### Varianta 1: Site static simplu (HTML + CSS)
- Creezi manual `index.html`, `froggy-crackme.html`, etc.
- Fiecare writeup = o pagină HTML cu titlu, explicații, blocuri de cod.
- **Plus:** Control total. **Minus:** trebuie să copiezi/formezi HTML pentru fiecare writeup.

### Varianta 2: Generator de site din Markdown (recomandat)
- Scrii writeup-urile în **Markdown** (ca `SOLUTION.md`).
- Folosești un generator:
  - **MkDocs** (Python) + theme **Material** → site cu meniu, search, cod colorat.
  - **Hugo** (Go) sau **Jekyll** (Ruby) – la fel, theme-uri frumoase.
- **Plus:** Editezi doar `.md`; site-ul se generează singur și arată foarte bine.

**Recomandare:** **MkDocs Material** – instalare rapidă, theme modern, suport pentru cod Python, tabele, note.

---

## Pasul 4: MkDocs Material – setup rapid pe calculatorul tău

Rulezi comenzile în Terminal (în folderul unde vrei proiectul, de ex. `~/Desktop/ctf-site`).

1. **Creează un director și un mediu virtual (opțional):**
   ```bash
   mkdir ~/Desktop/ctf-site && cd ~/Desktop/ctf-site
   python3 -m venv venv
   source venv/bin/activate   # pe Windows: venv\Scripts\activate
   ```

2. **Instalează MkDocs și theme-ul Material:**
   ```bash
   pip install mkdocs-material
   ```

3. **Inițializează site-ul:**
   ```bash
   mkdocs new .
   ```
   Se creează `mkdocs.yml` și `docs/` cu `index.md`.

4. **Deschide `mkdocs.yml`** și pune conținut de forma:
   ```yaml
   site_name: CTF Writeups
   site_url: https://amariei.org
   theme:
     name: material
     language: ro
     palette:
       - scheme: default
         primary: indigo
         accent: indigo
     features:
       - content.code.copy
       - content.tabs.link
   markdown_extensions:
     - pymdownx.highlight:
         anchor_linenums: true
     - pymdownx.superfences
     - tables
   nav:
     - Acasă: index.md
     - Writeups:
       - Froggy CrackMe: writeups/froggy-crackme.md
   ```

5. **Structura în `docs/`:**
   ```
   docs/
   ├── index.md              # Pagina principală
   └── writeups/
       └── froggy-crackme.md # Writeup Froggy (conținut din SOLUTION.md + extra)
   ```

6. **Copiază/adaugă writeup-ul** – deschide `docs/writeups/froggy-crackme.md` și lipește acolo conținutul din `SOLUTION.md` (și poți adăuga secțiuni „Cod”, „Cum rulezi scriptul”, etc.).

7. **Verifici local:**
   ```bash
   mkdocs serve
   ```
   Deschizi în browser `http://127.0.0.1:8000` și vezi site-ul.

8. **Build pentru deploy:**
   ```bash
   mkdocs build
   ```
   Se generează directorul `site/`. Acest `site/` este ce va servi GitHub Pages (sau Netlify/Vercel).

---

## Pasul 5: Conectează repo-ul la GitHub Pages

1. În repo-ul tău GitHub (ex: `ctf-writeups`), mergi la **Settings → Pages**.
2. La **Source** alege **GitHub Actions** (sau „Deploy from a branch”).
3. Dacă alegi **branch:**
   - Branch: `main` (sau `master`).
   - Folder: **`/ (root)`** dacă pui site-ul generat în root, sau **`/docs`** doar dacă folosești Jekyll cu `docs/` ca sursă.  
   Pentru MkDocs, de obicei pui un **GitHub Action** care rulează `mkdocs build` și pune conținutul din `site/` pe branch-ul `gh-pages` sau într-un folder special.

**Variantă simplă cu GitHub Actions pentru MkDocs:**

Creezi în repo fișierul `.github/workflows/deploy.yml`:

```yaml
name: Deploy
on:
  push:
    branches: [ main ]
jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: '3.x'
      - run: pip install mkdocs-material
      - run: mkdocs build
      - run: mkdocs gh-deploy --force
```

La fiecare push pe `main`, se construiește site-ul și se publică pe **GitHub Pages**. URL-ul va fi: `https://<username>.github.io/ctf-writeups/`.

---

## Pasul 6: Leagă domeniul amariei.org de GitHub Pages

1. **În Namecheap (DNS):**
   - Intră la **Domain List → amariei.org → Manage → Advanced DNS**.
   - Adaugi înregistrări:
     - **A Record:** Host `@`, Value `185.199.108.153` (și opțional `185.199.109.153`, `185.199.110.153`, `185.199.111.153` pentru redundanță).
     - **CNAME Record:** Host `www`, Value `<username>.github.io.` (cu punct la final).
   - Salvezi. Propagarea durează până la ~48h, de obicei mai puțin.

2. **În GitHub (repo):**
   - **Settings → Pages** → la **Custom domain** scrii: **`amariei.org`**.
   - Bifezi **Enforce HTTPS** după ce DNS-ul e activ.

3. După propagare, **https://amariei.org** va afișa site-ul tău (dacă Pages e setat pe acel repo; dacă e repo „user site”, atunci `amariei.org` trebuie setat ca custom domain pe **user/organization** GitHub Pages).

**Important:** Pentru **repository** GitHub Pages (nu user site), URL-ul de bază în `mkdocs.yml` trebuie să fie `https://amariei.org` și la **Custom domain** pui `amariei.org`. Apoi, dacă vrei ca **amariei.org** (fără path) să fie site-ul, trebuie ca acel repo să fie setat ca **user/org site** (repo numit `username.github.io`) SAU să pui redirect de la domeniu la `https://username.github.io/ctf-writeups/`. Cel mai simplu: creezi un repo numit **`<username>.github.io`**, pui acolo deploy-ul MkDocs; atunci **amariei.org** poate fi setat direct ca custom domain și **https://amariei.org** va fi exact site-ul tău.

---

## Pasul 7: Template pentru un writeup „frumos”

Pentru fiecare challenge, poți folosi un singur fișier Markdown, de exemplu `docs/writeups/froggy-crackme.md`:

```markdown
# Froggy CrackMe – Soluție

**Categorie:** Reverse / CrackMe  
**Instrumente:** IDA, Python, Z3 (opțional)

## Rezumat

Serial format: `XXXXXXXX-XXXXXXXX-XXXXXXXX-XXXXXXXX`. Validarea leagă numele de serial (FNV + mix). O singură condiție decide succesul; poți și patch la jump.

---

## 1. Flow de validare

... (conținut din SOLUTION.md) ...

## 2. Patch rapid (NOP)

... (pași clari) ...

## 3. Keygen / Solver (fără patch)

Logica e în `froggy_solver.py` și `key.py`. Exemplu de rulare:

\`\`\`bash
python3 key.py "Froggy"
\`\`\`

\`\`\`python
# fragment relevant din key.py
...
\`\`\`

## 4. Referință rapidă

| Element    | Valoare / Locație |
|-----------|--------------------|
| Target    | 0xB9229933597558C9 |
| Patch     | 0x2734: 90 90      |
```

Adaugi în `mkdocs.yml` la `nav` fiecare writeup nou, ex:

```yaml
nav:
  - Acasă: index.md
  - Writeups:
    - Froggy CrackMe: writeups/froggy-crackme.md
    - Al doilea challenge: writeups/al-doilea.md
```

Salvezi, faci push; după ce ai deploy-ul configurat, site-ul se actualizează singur.

---

## Rezumat pași (ordine practică)

| # | Ce faci |
|---|--------|
| 1 | Creezi repo GitHub (ex: `ctf-writeups` sau `username.github.io`) |
| 2 | Pe PC: `pip install mkdocs-material`, `mkdocs new .`, configurezi `mkdocs.yml` |
| 3 | Creezi `docs/writeups/froggy-crackme.md` (conținut din SOLUTION.md + cod/pași) |
| 4 | Rulezi `mkdocs serve`, verifici local |
| 5 | Adaugi workflow GitHub Actions pentru `mkdocs gh-deploy` (sau deploy manual în branch `gh-pages`) |
| 6 | În Namecheap: A + CNAME pentru amariei.org → GitHub Pages |
| 7 | În GitHub Pages: Custom domain = amariei.org, Enforce HTTPS |

După asta, pentru fiecare writeup nou: adaugi un `.md` în `docs/writeups/`, îl pui în `nav` din `mkdocs.yml`, push – și apare pe **https://amariei.org**.

Dacă vrei, următorul pas concret poate fi: generarea fișierelor `mkdocs.yml` și `docs/index.md` + `docs/writeups/froggy-crackme.md` direct în folderul tău de CTF (sau într-un folder `ctf-site`) ca să le poți folosi imediat.
