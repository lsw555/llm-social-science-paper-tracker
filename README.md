# LLM Social Science Paper Tracker

An automated GitHub Pages digest of recent social-science research about large language models, ChatGPT, and generative AI.

## Automated workflow

Every day, the GitHub Action in `.github/workflows/update-papers.yml`:

1. Searches OpenAlex across three streams: LLMs as social-science research tools; human–AI interaction and social outcomes; and LLM behavior, values, and bias. The first empty run searches the previous 90 days to seed the tracker; later daily runs search the previous 10 days.
2. Retrieves metadata, author names, venue, publication year, DOI/link, and abstract.
3. Uses a low-cost first pass (`gpt-5-nano`) to remove clearly irrelevant papers, then uses `gpt-5.6-luna` to make the final social-science inclusion decision while excluding purely technical AI work.
4. Creates three short abstract-grounded fields: **Goal**, **Methodology**, and **Finding**.
5. Adds up to 10 approved records to `data/papers.json`, rejects duplicates by OpenAlex ID, DOI, and normalized title, commits them, and thereby refreshes the GitHub Pages site.

The website is deliberately simple: a headline, latest-update timestamp, search/field filter, and paper cards. There is no subscription component.

## Publish on GitHub Pages

1. Create a public GitHub repository and upload this folder's contents.
2. In **Settings → Pages**, select **Deploy from a branch**, then select `main` and `/ (root)`.
3. In **Settings → Secrets and variables → Actions**, create a secret named `OPENAI_API_KEY`.
4. Open the **Actions** tab and run **Find and summarize new papers** once to populate the initially empty tracker.

Never place `OPENAI_API_KEY` in frontend files, repository variables, or `data/papers.json`. The current dataset is intentionally empty until the first workflow run.

## Run locally

```sh
python3 -m http.server 4173
```

Then visit `http://localhost:4173`.
