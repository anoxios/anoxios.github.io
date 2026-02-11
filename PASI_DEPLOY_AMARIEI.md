# Pași concreti: de la proiect local → amariei.org

Urmează ordinea de mai jos. După fiecare pas, poți verifica că merge înainte să treci la următorul.

---

## Partea 1: Pune proiectul pe GitHub

### 1.1 Creează un repo nou pe GitHub

1. Mergi pe **https://github.com/new**
2. **Repository name:** poți pune `amariei.github.io` (atunci site-ul va fi direct la `https://amariei.github.io`) SAU `ctf-writeups` (atunci va fi `https://amariei.github.io/ctf-writeups/`).
3. **Public**, fără README / .gitignore / license (le ai deja local).
4. Click **Create repository**.

### 1.2 Inițializează git în folderul ctf și fă primul push

Deschizi Terminal, te pozi în proiect și rulezi (înlocuiești `amariei` cu username-ul tău GitHub dacă e diferit):

```bash
cd /Users/sabinamariei/Desktop/ctf
git init
git add .
git status
```

Verifici că **nu** apar în listă: `.venv/`, `site/`, `__pycache__/` (le ignoră `.gitignore`). Apoi:

```bash
git commit -m "Site CTF writeups + MkDocs"
git branch -M main
git remote add origin https://github.com/amariei/amariei.github.io.git
git push -u origin main
```

(Înlocuiești `amariei/amariei.github.io` cu `USERNAME/REPO` – exact cum apare în pagina repo-ului tău.)

Dacă te întreabă de login: folosești **Personal Access Token** ca parolă (Settings → Developer settings → Personal access tokens), nu parola contului.

---

## Partea 2: Activezi GitHub Pages

1. În repo: **Settings** (tab-ul din repo) → în meniul din stânga **Pages**.
2. La **Build and deployment**:
   - **Source:** alege **GitHub Actions** (nu „Deploy from a branch”).
3. Workflow-ul `.github/workflows/deploy.yml` rulează la fiecare push pe `main` și publică site-ul.

După 1–2 minute, site-ul va fi live la:
- **https://amariei.github.io** (dacă repo-ul e `amariei.github.io`)
- sau **https://amariei.github.io/ctf-writeups/** (dacă repo-ul e `ctf-writeups`).

---

## Partea 3: Legi domeniul amariei.org

### 3.1 În Namecheap (DNS)

1. **Domain List** → **amariei.org** → **Manage** → **Advanced DNS**.
2. Adaugi / editezi înregistrările:

   | Type  | Host | Value                 | TTL   |
   |-------|------|------------------------|-------|
   | A     | @    | 185.199.108.153        | Automatic |
   | A     | @    | 185.199.109.153        | Automatic |
   | A     | @    | 185.199.110.153        | Automatic |
   | A     | @    | 185.199.111.153        | Automatic |
   | CNAME | www  | amariei.github.io.     | Automatic |

   La CNAME e important **punctul de la final**: `amariei.github.io.`

3. **Save**. Propagarea durează de la câteva minute până la ~48h (de obicei sub 1h).

### 3.2 În GitHub (Custom domain)

1. Tot în **Settings → Pages** al repo-ului.
2. La **Custom domain** scrii: **amariei.org** (fără https://).
3. **Save**.
4. După ce DNS-ul e propagat, bifezi **Enforce HTTPS** (poate apărea după câteva minute).

### 3.3 Dacă repo-ul e `ctf-writeups` (nu `username.github.io`)

Atunci **https://amariei.org** trebuie să știe că site-ul e la `amariei.github.io/ctf-writeups/`. Variante:

- **A)** În Namecheap, la CNAME pentru `@` (root): GitHub Pages **nu** acceptă CNAME pe root de la terți; trebuie A records (cele 4 IP-uri de mai sus). Deci la **Custom domain** în GitHub pui **amariei.org** și GitHub va răspunde pe acel domeniu dacă repo-ul e setat ca „user/org site”.  
  Pentru **user site** (un singur site per cont), repo-ul trebuie să se numească **amariei.github.io**. Concluzie: cel mai simplu e să **redenumești** repo-ul în **amariei.github.io** (Settings → Repository name → Rename). Atunci amariei.org va servi direct acel site.
- **B)** Lași repo-ul `ctf-writeups` și folosești **doar** **https://amariei.github.io/ctf-writeups/**; domeniul custom **amariei.org** pe GitHub Pages merge doar cu un repo „site” (user/org), deci tot ajungi la varianta A.

**Recomandare:** repo **amariei.github.io**, A records în Namecheap ca mai sus, Custom domain **amariei.org** în Settings → Pages. Apoi **https://amariei.org** va fi site-ul tău.

---

## Rezumat rapid

| Pas | Unde | Ce faci |
|-----|------|--------|
| 1 | GitHub | Creezi repo `amariei.github.io` (sau `ctf-writeups`) |
| 2 | Terminal | `git init`, `git add .`, `git commit`, `git remote add origin ...`, `git push` |
| 3 | GitHub → Settings → Pages | Source: **GitHub Actions** |
| 4 | Namecheap → Advanced DNS | 4× A @ → IP-uri GitHub; CNAME www → amariei.github.io. |
| 5 | GitHub → Settings → Pages | Custom domain: **amariei.org** → Save → Enforce HTTPS |

După asta, la fiecare modificare în proiect:

```bash
cd /Users/sabinamariei/Desktop/ctf
git add .
git commit -m "Descriere modificare"
git push
```

Site-ul se reconstruiește singur și **https://amariei.org** se actualizează.
