# LLM Social Science Paper Tracker

An automated GitHub Pages digest of recent social-science research about large language models, ChatGPT, and generative AI.

## Automated workflow

Every day, the GitHub Action in `.github/workflows/update-papers.yml`:

1. Searches OpenAlex across three streams: LLMs as social-science research tools; human–AI interaction and social outcomes; and LLM behavior, values, and bias. The first empty run searches the previous 90 days to seed the tracker; later daily runs search the previous 10 days.
2. Retrieves metadata, author names, venue, publication year, DOI/link, and abstract.
3. Uses a low-cost first pass (`gpt-5-nano`) to remove clearly irrelevant papers, then uses `gpt-5.6-luna` to make the final social-science inclusion decision while excluding purely technical AI work.
4. Creates three short abstract-grounded fields: **Goal**, **Methodology**, and **Finding**.
5. Adds up to 10 approved records to `data/papers.json`, rejects duplicates by OpenAlex ID, DOI, and normalized title, commits them, and thereby refreshes the GitHub Pages site.

## Corpus insights

Each update also generates `data/insights.json`, which powers the tracker’s **Corpus overview**. It includes a concise synthesis of the eligible corpus, 3–5 recurring themes, emerging keywords, paper counts by publication year, and the distribution across research streams. The thematic synthesis uses `gpt-5-nano` over a compact version of the current corpus; counts are calculated directly from the tracker data.

## Discovery queries

The tracker uses broad concept-based OpenAlex searches for LLMs/generative AI in social science, public opinion, content analysis, communication/media/journalism, human–AI interaction, mental health/social support, health/climate behavior, AI-generated news, and human behavior/bias/values. It does not rely on a single product name such as ChatGPT.

## Included journals

The tracker admits papers only from: **Humanities and Social Sciences Communications**, **Scientific Reports**, **Nature Communications**, **Nature**, **Science**, **Computers in Human Behavior**, **Social Science Computer Review**, **PNAS**, **PNAS Nexus**, **Digital Journalism**, **Journal of Communication**, **Communication Research**, **Human Communication Research**, and **Communication Methods and Measures**. The update workflow also removes existing records from other sources, so the public catalogue remains restricted to this list.

The website is deliberately simple: a headline, latest-update timestamp, search/field filter, and paper cards. There is no subscription component.

## Publish on GitHub Pages

1. Create a public GitHub repository and upload this folder's contents.
2. In **Settings → Pages**, select **Deploy from a branch**, then select `main` and `/ (root)`.
3. In **Settings → Pages**, set **Source** to **GitHub Actions**.
4. In **Settings → Secrets and variables → Actions**, create a secret named `OPENAI_API_KEY`.
5. Open the **Actions** tab and run **Find and summarize new papers** once to populate the initially empty tracker. On completion, the same workflow deploys the public site; use the link shown on its `deploy` job.

Never place `OPENAI_API_KEY` in frontend files, repository variables, or `data/papers.json`. The current dataset is intentionally empty until the first workflow run.

## Run locally

```sh
python3 -m http.server 4173
```

Then visit `http://localhost:4173`.
