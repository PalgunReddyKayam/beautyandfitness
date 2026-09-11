# Beauty & Fitness — setup guide

A beauty & fitness blog built with Eleventy (site generator) and Decap CMS (the editor), hosted free on Cloudflare Pages.

Once set up, you write and edit articles at **beautyandfitness.in/admin** in a visual editor. Every time you press Publish, the site rebuilds and goes live in about a minute. No code, no re-uploading.

Total setup time: about 20 minutes. Everything below is free.

---

## What's in this folder

```
src/posts/        ← your articles (one Markdown file each)
src/uploads/      ← images you add through the editor
src/admin/        ← the editor (Decap CMS)
src/_data/site.json ← site name, tagline, description
src/_includes/    ← page templates
src/assets/       ← stylesheet, JavaScript, logo
functions/api/    ← the GitHub login handler for the editor
```

---

## Step 1 — Put the project on GitHub

1. Create a free account at https://github.com if you don't have one.
2. Click **New repository**. Name it exactly `beautyandfitness` (the editor is already configured for this name). Leave it **Public** or **Private** — both work. Do **not** tick "Add a README".
3. Upload this folder's contents. Easiest way without installing anything:
   - On the empty repository page, click **uploading an existing file**.
   - Drag in everything from this folder **except** `node_modules` and `_site` (they're not included in the zip anyway).
   - Click **Commit changes**.

   If you're comfortable with Git instead:
   ```
   git init
   git add .
   git commit -m "Initial site"
   git branch -M main
   git remote add origin https://github.com/PalgunReddyKayam/beautyandfitness.git
   git push -u origin main
   ```

## Step 2 — Deploy on Cloudflare Pages

1. Log in to https://dash.cloudflare.com → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**.
2. Authorise GitHub and pick the repository.
3. Build settings:
   - **Framework preset:** Eleventy (or None)
   - **Build command:** `npm run build`
   - **Build output directory:** `_site`
4. Click **Save and Deploy**. In about a minute you'll have a `something.pages.dev` address and the site will be live.

## Step 3 — Add your domain

1. In the same Pages project → **Custom domains** → **Set up a custom domain** → enter your domain.
2. If the domain is already on Cloudflare, it's done automatically. If not, Cloudflare walks you through adding it (you change the nameservers at your registrar; propagation takes minutes to a few hours).

## Step 4 — Make the editor work (GitHub login)

The editor at `/admin` saves articles to your GitHub repository, so it needs permission to log in with GitHub. One-time setup:

### 4a. Create a GitHub OAuth app

1. GitHub → click your profile picture → **Settings** → **Developer settings** (bottom of the left menu) → **OAuth Apps** → **New OAuth App**.
2. Fill in:
   - **Application name:** Beauty & Fitness editor
   - **Homepage URL:** `https://beautyandfitness.in`
   - **Authorization callback URL:** `https://beautyandfitness.in/api/callback`
3. Click **Register application**.
4. Copy the **Client ID**. Then click **Generate a new client secret** and copy that too (you only see it once).

### 4b. Give the secrets to Cloudflare

1. Cloudflare → your Pages project → **Settings** → **Variables and Secrets** → **Add**.
2. Add two entries (type: **Secret**):
   - `GITHUB_CLIENT_ID` = the Client ID
   - `GITHUB_CLIENT_SECRET` = the client secret
3. Save, then go to **Deployments** and **Retry deployment** on the latest one so the secrets take effect.

### 4c. Already done for you

`src/admin/config.yml` is pre-filled with `PalgunReddyKayam/beautyandfitness` and `https://beautyandfitness.in`. Nothing to change — as long as the repository is named `beautyandfitness`.

## Step 5 — Write

Go to **https://beautyandfitness.in/admin**, click **Login with GitHub**, and you're in.

- **Articles** → **New Article** to write. Fill in the title, section (Beauty / Fitness), category, summary, optional cover image, and the article body. The body editor supports headings, bold, lists, links, images and tables.
- Articles start as **Drafts** → move to **In review** → **Ready**, then **Publish**. (This "editorial workflow" is optional; set `publish_mode` to `simple` in `config.yml` if you'd rather have a single Publish button.)
- **Site settings** lets you change the site name, tagline and the About page.

Each publish takes roughly a minute to appear on the live site.

---

## Things you may want later

- **Newsletter:** the subscribe box currently just shows a confirmation. To collect real emails, sign up for a free tier at Buttondown, MailerLite or Mailchimp and swap in their form action in `src/index.njk`.
- **Logo:** `src/assets/logo-mark.svg` (the symbol, also used as the favicon) and `src/assets/logo.svg` (symbol + name).
- **Colours:** the palette lives at the top of `src/assets/style.css` under `:root`.
- **Preview locally** (optional, needs Node.js): `npm install` then `npm run dev`, open http://localhost:8080.

## If something goes wrong

- **Build fails on Cloudflare:** open the deployment log. Nearly always it's a typo in an article's front matter (the block between `---` lines). Titles containing a colon need quotes: `title: "Retinol: what to know"`.
- **Editor says "Login failed":** check the callback URL in the GitHub OAuth app is exactly `https://beautyandfitness.in/api/callback`, and that both secrets are set in Cloudflare and you redeployed afterwards.
- **Editor loads but shows no articles:** the `repo:` line in `config.yml` doesn't match your GitHub username/repo.
