#!/usr/bin/env python3
"""Write one new article for beautyandfitness.in and fetch a cover image.

Runs inside GitHub Actions. Needs ANTHROPIC_API_KEY in the environment.
"""
import datetime, glob, json, os, random, re, sys, time
import urllib.error, urllib.parse, urllib.request

POSTS = "src/posts"
UPLOADS = "src/uploads"
MODELS = [
    "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250929",
    "claude-sonnet-4-20250514",
    "claude-3-7-sonnet-latest",
    "claude-3-5-sonnet-latest",
]

CATEGORIES = {
    "beauty": ["Skincare", "Hair", "Makeup"],
    "fitness": ["Strength", "Mobility", "Cardio", "Nutrition", "Recovery", "Mindset"],
}


def existing():
    titles, slugs = [], []
    for path in sorted(glob.glob(os.path.join(POSTS, "*.md"))):
        slugs.append(os.path.basename(path)[:-3])
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                if line.startswith("title:"):
                    titles.append(line.split(":", 1)[1].strip().strip('"'))
                    break
    return titles, slugs


def samples(n=2):
    paths = sorted(glob.glob(os.path.join(POSTS, "*.md")))
    random.shuffle(paths)
    out = []
    for p in paths[:n]:
        with open(p, encoding="utf-8") as fh:
            out.append(fh.read())
    return "\n\n---8<---\n\n".join(out)


SYSTEM = """You write for Beauty & Fitness, a plain-language beauty and fitness site. \
You are a careful human writer, not a chatbot. Your writing is quiet, specific and \
evidence-led. Readers trust the site because it never oversells.

HARD RULES — breaking any of these ruins the piece:
- British spelling (moisturise, colour, programme, fibre).
- No AI throat-clearing. Never open with "In today's world", "Let's dive in", \
"Whether you're a beginner or", "Imagine this", a rhetorical question, or a definition \
of the topic. Open on a concrete observation, a common mistake, or a specific scene.
- Never use: delve, elevate, unlock, game-changer, journey, holistic, embark, \
testament, tapestry, "it's important to note", "when it comes to", "not only... but also", \
"in conclusion", "the key takeaway". No sentence that begins with "Remember,".
- No emoji. No bold scattered through paragraphs for emphasis — bold only to label a \
list item or a short lead-in.
- Vary sentence length. Short declarative sentences are good. Do not write three \
consecutive sentences of the same shape.
- Be specific: real numbers, real timeframes, real ingredient names, real exercise names. \
Vague advice is the failure mode.
- Say when evidence is weak or when something does not matter. Contradict popular advice \
where the evidence supports it.
- No medical claims about treating disease. No promises of specific results.
- 700-950 words.

STRUCTURE (match the examples exactly):
- YAML front matter, then the body.
- Body opens with 2-3 short paragraphs of plain prose, no heading.
- Then 3-5 "## " sections with concrete, useful content.
- Ends with a "## What to do this week" section of 3-5 bullet actions.
- Markdown only: ##, **bold**, - bullets. No H1, no tables, no images in the body.
"""


def prompt(titles, pillar, category, date, examples):
    return f"""Here are two existing articles from the site, so you can match the voice exactly:

{examples}

---8<---

Articles already on the site (do not repeat these topics):
{chr(10).join('- ' + t for t in titles)}

Write ONE new article.
- Section (pillar): {pillar}
- Category: {category}
- Publish date: {date}

Pick a topic in that category that is genuinely useful, is not in the list above, and \
that a real reader would search for. Prefer a specific question over a broad survey.

Return ONLY the finished Markdown file, starting with --- and nothing before it. The front \
matter must be exactly these keys in this order:

---
title: "..."
date: {date}
pillar: {pillar}
category: {category}
summary: One or two sentences, plain, no hype.
author: Beauty & Fitness
draft: false
imagePrompt: "..."
coverAlt: "..."
---

imagePrompt is a brief for a photograph of an OBJECT or a PLACE. It must contain NO PEOPLE.

RULES for imagePrompt — these are absolute:
- No people. No person, no model, no hands, no face, no body part of any kind. Not even \
partly, not even out of focus, not even in the background. A brief that mentions a human \
in any form is rejected and replaced automatically.
- Photograph the thing, not the user of the thing: shampoo bottles on a wet tiled shelf, a \
loaded barbell on a gym floor at dawn, chopped vegetables on a wooden board, running shoes \
by a front door, a folded towel beside a bar of soap, an open jar on a cluttered shelf.
- Describe the light and the place. Ordinary, slightly imperfect, lived-in.
- One sentence. Never a studio, never glamorous, never an illustration or 3D render.

coverAlt is a short plain description of that photograph for screen readers."""


def available_models(key):
    """Ask the API which models this key can actually use."""
    req = urllib.request.Request("https://api.anthropic.com/v1/models?limit=50")
    req.add_header("x-api-key", key)
    req.add_header("anthropic-version", "2023-06-01")
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            data = json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        body = e.read().decode()[:300]
        print(f"model list -> HTTP {e.code}: {body}", file=sys.stderr)
        return []
    except Exception as exc:  # noqa: BLE001
        print(f"model list failed: {exc}", file=sys.stderr)
        return []
    ids = [m["id"] for m in data.get("data", [])]
    print("Models available to this key:", ", ".join(ids) or "(none)")
    sonnet = [i for i in ids if "sonnet" in i]
    opus = [i for i in ids if "opus" in i]
    haiku = [i for i in ids if "haiku" in i]
    return sonnet + opus + haiku + ids


def call_claude(sys_prompt, user_prompt):
    key = os.environ.get("ANTHROPIC_API_KEY")
    if not key:
        sys.exit("ANTHROPIC_API_KEY is not set. Add it as a repository secret.")
    candidates = available_models(key)
    seen = set()
    ordered = [m for m in candidates + MODELS if not (m in seen or seen.add(m))]
    last = ""
    for model in ordered:
        body = json.dumps({
            "model": model,
            "max_tokens": 4000,
            "temperature": 1.0,
            "system": sys_prompt,
            "messages": [{"role": "user", "content": user_prompt}],
        }).encode()
        req = urllib.request.Request(
            "https://api.anthropic.com/v1/messages", data=body, method="POST")
        req.add_header("x-api-key", key)
        req.add_header("anthropic-version", "2023-06-01")
        req.add_header("content-type", "application/json")
        try:
            with urllib.request.urlopen(req, timeout=180) as r:
                data = json.loads(r.read().decode())
            text = "".join(b.get("text", "") for b in data["content"])
            if data.get("stop_reason") == "max_tokens":
                print(f"{model} ran out of room mid-article; discarding.", file=sys.stderr)
                last = "response truncated (max_tokens)"
                continue
            print("Wrote with model:", model)
            return text
        except urllib.error.HTTPError as e:
            last = e.read().decode()[:400]
            print(f"model {model} -> HTTP {e.code}: {last}", file=sys.stderr)
            if e.code in (401, 403):
                sys.exit("API key rejected. Check the ANTHROPIC_API_KEY secret and that "
                         "the account has credit.")
            continue
        except Exception as exc:  # noqa: BLE001
            last = str(exc)
            print(f"model {model} -> {exc}", file=sys.stderr)
            continue
    sys.exit("No usable model. Last error: " + last)


def slugify(title):
    s = title.lower()
    s = re.sub(r"[^a-z0-9\s-]", "", s)
    s = re.sub(r"\s+", "-", s).strip("-")
    return s[:60].rstrip("-")


BANNED = [
    "woman", "women", "man", "men", "girl", "boy", "lady", "person", "people",
    "model", "female", "male", "body", "torso", "chest", "breast", "shoulder",
    "bare", "nude", "naked", "topless", "lingerie", "bikini", "underwear",
    "swimsuit", "skin texture", "face", "portrait", "selfie", "her ", "his ",
    "she ", "he ", "wearing", "dressed", "undressed", "shower", "bathing",
    "bath ", "towel-wrapped", "sensual", "beautiful young", "attractive",
    "hands", "hand ", "arm", "leg", "thigh", "hair of", "lips", "eyes",
]

SAFE_SUFFIX = (" — still life object photography, empty scene, absolutely no people, "
               "no human figures, no body parts, no faces, natural light, 35mm, "
               "shallow depth of field, no text, no logos")

FALLBACK_PROMPTS = [
    "a row of unlabelled skincare bottles on a wet bathroom shelf, morning light",
    "a loaded barbell resting on a worn gym floor, early daylight through a high window",
    "chopped vegetables and a knife on a scratched wooden board, kitchen counter",
    "a pair of worn running shoes by a front door, hallway light",
    "a folded towel and a plain bar of soap on a tiled ledge",
    "a glass of water and a notebook on a windowsill, overcast afternoon",
    "a kettlebell and a skipping rope on a concrete floor",
    "an open jar of plain moisturiser on a cluttered shelf, side light",
]


def prompt_is_safe(text):
    """True only if the brief describes no person and no body part."""
    low = " " + text.lower() + " "
    hits = [w for w in BANNED if w in low]
    if hits:
        print("Image brief rejected, mentions:", ", ".join(sorted(set(hits))), file=sys.stderr)
        return False
    return True


def fetch_cover(image_prompt, slug):
    os.makedirs(UPLOADS, exist_ok=True)

    if not prompt_is_safe(image_prompt):
        image_prompt = random.choice(FALLBACK_PROMPTS)
        print("Using a safe fallback image brief instead.", file=sys.stderr)

    full = image_prompt.strip().rstrip(".") + SAFE_SUFFIX
    enc = urllib.parse.quote(full[:1200])
    dest = os.path.join(UPLOADS, slug + ".jpg")

    for attempt in range(3):
        seed = random.randint(1, 10**8)
        url = (f"https://image.pollinations.ai/prompt/{enc}"
               f"?width=1600&height=900&model=flux&nologo=true&safe=true&seed={seed}")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "beautyandfitness-bot"})
            with urllib.request.urlopen(req, timeout=180) as r:
                data = r.read()
            if len(data) > 20000:
                with open(dest, "wb") as fh:
                    fh.write(data)
                return "/uploads/" + slug + ".jpg"
            print("image came back too small, retrying", file=sys.stderr)
        except Exception as exc:  # noqa: BLE001
            print(f"image attempt {attempt + 1} failed: {exc}", file=sys.stderr)
        time.sleep(15)

    print("No cover image this time; publishing without one.", file=sys.stderr)
    return None


def main():
    titles, slugs = existing()
    if not titles:
        sys.exit("No existing posts to learn the voice from.")

    # alternate between beauty and fitness based on what is thinner
    counts = {"beauty": 0, "fitness": 0}
    for path in glob.glob(os.path.join(POSTS, "*.md")):
        with open(path, encoding="utf-8") as fh:
            txt = fh.read()
        for p in counts:
            if f"pillar: {p}" in txt:
                counts[p] += 1
    pillar = min(counts, key=counts.get)
    category = random.choice(CATEGORIES[pillar])
    date = datetime.date.today().isoformat()

    md = call_claude(SYSTEM, prompt(titles, pillar, category, date, samples()))
    md = md.strip()
    if md.startswith("```"):
        md = re.sub(r"^```[a-z]*\n", "", md)
        md = re.sub(r"\n```$", "", md)
    if not md.startswith("---"):
        sys.exit("Model did not return a Markdown file with front matter.")

    m = re.search(r'^title:\s*"?(.+?)"?\s*$', md, re.M)
    if not m:
        sys.exit("No title in the generated front matter.")
    title = m.group(1)
    slug = slugify(title)
    name = f"{date}-{slug}"
    if any(s.endswith(slug) for s in slugs):
        sys.exit(f"Topic '{title}' already covered; skipping this run.")

    body = md.split("---", 2)[-1]
    problems = []
    if "## What to do this week" not in md:
        problems.append("missing the closing 'What to do this week' section")
    if len(body.split()) < 450:
        problems.append(f"too short ({len(body.split())} words)")
    if body.rstrip()[-1:] not in ".!?:" and not body.rstrip().endswith("]"):
        problems.append("ends mid-sentence")
    if body.count("**") % 2 != 0:
        problems.append("unclosed bold markup")
    if problems:
        sys.exit("Article rejected, publishing nothing. Problems: " + "; ".join(problems))

    ip = re.search(r'^imagePrompt:\s*"?(.+?)"?\s*$', md, re.M)
    cover = fetch_cover(ip.group(1), name) if ip else None
    if cover:
        md = re.sub(r"^(summary:.*)$", r"\1\ncover: " + cover, md, count=1, flags=re.M)

    os.makedirs(POSTS, exist_ok=True)
    path = os.path.join(POSTS, name + ".md")
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(md.rstrip() + "\n")
    print("Wrote", path)


if __name__ == "__main__":
    main()
