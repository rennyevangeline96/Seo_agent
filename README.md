# AI SEO Content Studio

An AI-powered SEO content generation application built with **Microsoft
AutoGen**, **OpenAI**, **DuckDuckGo Search**, and **Streamlit**.

The app accepts a topic, researches relevant information, drafts an
article, optimizes it for SEO, and reviews the result using a
multi-agent workflow.

## Features

-   **SEO Researcher:** Searches the web and prepares a report with
    topic angles, search intent, keywords, audience questions, and
    source URLs.
-   **Content Writer:** Creates an article using the research, selected
    word count, target audience, and writing tone.
-   **SEO Optimizer:** Improves the SEO title, meta description, URL
    slug, keyword placement, headings, and internal-link and
    image-alt-text suggestions.
-   **Content Reviewer:** Evaluates accuracy, usefulness, readability,
    search intent, and SEO structure. It returns `APPROVE` or
    `NEEDS_REVISION`.
-   **Streamlit frontend:** Lets users enter a topic, choose settings,
    view agent output, and download the article or transcript.
-   **Bounded review loop:** Limits the content team to six turns to
    avoid endless revisions.

## Architecture

``` text
User enters topic in Streamlit
             |
             v
      SEO Researcher
    DuckDuckGo web search
             |
             v
       Research report
             |
             v
       Content Writer
             |
             v
       SEO Optimizer
             |
             v
      Content Reviewer
        /          \
    APPROVE     NEEDS_REVISION
       |              |
       v              v
 Show results    Writer revises
                       |
                       v
                 SEO Optimizer
                       |
                       v
                   Reviewer
                       |
                       v
             Stop at approval or
               six team turns
```

## Agent responsibilities

  -----------------------------------------------------------------------
  Agent                               Responsibility
  ----------------------------------- -----------------------------------
  SEO Researcher                      Finds relevant search results and
                                      summarizes potential trends, search
                                      intent, keywords, and content
                                      angles.

  Content Writer                      Writes the first article and
                                      revises it when reviewer feedback
                                      requires changes.

  SEO Optimizer                       Optimizes the article and provides
                                      SEO metadata and improvement
                                      suggestions.

  Content Reviewer                    Checks the latest optimized content
                                      and decides whether to approve it
                                      or request revisions.
  -----------------------------------------------------------------------

The researcher runs before the content team. The content team runs in
round-robin order: **Writer → Optimizer → Reviewer**.

## How the six-turn limit works

The application uses `MAX_TEAM_TURNS = 6`.

    Turn Agent           Typical action
  ------ --------------- -------------------------------
       1 Writer          Creates the initial article
       2 SEO Optimizer   Optimizes the article
       3 Reviewer        Approves or requests changes
       4 Writer          Revises the article if needed
       5 SEO Optimizer   Optimizes the revised article
       6 Reviewer        Reviews the revised article

Six turns is a maximum, not a requirement. If the reviewer returns
`APPROVE` on turn 3, the workflow stops early. If the limit is reached
without approval, the app shows the content as **not approved**. This
allows one revision cycle after the initial draft.

## Technology stack

-   Python
-   Microsoft AutoGen AgentChat
-   AutoGen OpenAI model client
-   OpenAI chat completion model
-   DuckDuckGo Search (`ddgs`)
-   Streamlit
-   `python-dotenv`

## Project structure

``` text
ai-seo-content-studio/
├── app.py
├── README.md
├── requirements.txt
├── .env
└── .gitignore
```

-   `app.py` --- Streamlit frontend, web search, agent definitions, and
    workflow.
-   `requirements.txt` --- Python dependencies.
-   `.env` --- API key and model configuration. Do not commit this file.
-   `.gitignore` --- Excludes secrets and local development files from
    Git.

## Prerequisites

-   Python version supported by the installed AutoGen dependencies.
-   An OpenAI API key with API access and available billing or credits.
-   Internet access for package installation and web search.

## Installation

### 1. Create a project folder

``` powershell
mkdir ai-seo-content-studio
cd ai-seo-content-studio
```

Save the application code as `app.py` in this folder.

### 2. Create and activate a virtual environment

``` powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Create `requirements.txt`

``` text
autogen-agentchat
autogen-ext[openai]
streamlit
python-dotenv
ddgs
```

Install the dependencies:

``` powershell
python -m pip install --upgrade pip
pip install -r requirements.txt
```

For reproducible deployments, test the application and pin the
dependency versions that work in your environment.

### 4. Configure environment variables

Create a `.env` file in the project root:

``` dotenv
OPENAI_API_KEY=your_actual_openai_api_key
OPENAI_MODEL=gpt-4o-mini
```

Replace the example key with your own. Never publish your API key.

### 5. Start the application

``` powershell
streamlit run app.py
```

Open the local URL printed in the terminal, commonly
`http://localhost:8501`.

## How to use the app

1.  Enter a topic.
2.  Select an article length.
3.  Enter the target audience.
4.  Choose the writing tone.
5.  Click **Generate SEO Content**.
6.  Watch agent activity as the workflow runs.
7.  Open the **Research**, **Optimized Article**, **Review**, and
    **Agent Transcript** tabs.
8.  Download the article as Markdown or download the transcript.

## Output

-   Research report with search findings and source URLs.
-   SEO-optimized article in Markdown.
-   SEO metadata and suggestions, such as title, meta description, slug,
    keywords, headings, internal-link ideas, and image alt text.
-   Reviewer feedback and approval status.
-   Agent transcript for inspecting the workflow.

SEO metadata and suggestions are generated as part of the optimizer's
response and may appear alongside the article in the **Optimized
Article** tab.

## Configuration and performance

The current settings in `app.py` include:

``` python
MAX_TEAM_TURNS = 6
MAX_SEARCH_RESULTS = 3
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
```

-   `MAX_TEAM_TURNS` caps the Writer--Optimizer--Reviewer team.
-   `MAX_SEARCH_RESULTS` limits the number of DuckDuckGo results used in
    the research input.
-   `OPENAI_MODEL` selects the OpenAI model through `.env`.

Research and the content-team workflow run sequentially. Total runtime
depends on search latency, model response time, and article length.

## Important limitations

-   A small number of search results cannot prove that a topic is
    trending. Treat trend claims as preliminary unless supported by
    stronger evidence.
-   Search snippets may not fully verify a claim. Visit source URLs and
    fact-check important details before publishing.
-   The app does not guarantee rankings, traffic, or conversions.
-   Automated reviewer approval is not a substitute for human
    fact-checking or editorial review.
-   If the six-turn limit is reached without `APPROVE`, treat the result
    as not approved.
-   DuckDuckGo results and availability can vary.
-   OpenAI API usage may incur charges.

## Troubleshooting

### `OPENAI_API_KEY is missing`

-   Confirm `.env` is in the same folder as `app.py`.
-   Confirm the variable is named `OPENAI_API_KEY`.
-   Restart Streamlit after editing `.env`.

### Package import errors

Activate the intended virtual environment and run:

``` powershell
python -m pip install -r requirements.txt
```

If an AutoGen import or API differs, check the installed package
versions and official AutoGen documentation.

### Web search fails

-   Check the internet connection.
-   Try again later if the search service is temporarily unavailable.
-   Do not present unverified suggestions as sourced facts.

### Workflow ends without approval

This may happen when the reviewer requests revisions but the six-turn
limit is reached. Read the feedback, revise the article, or deliberately
adjust the turn limit. Do not label the article approved unless the
latest reviewer response ends with `APPROVE`.

## Security

-   Keep `.env` out of source control.
-   Do not hard-code API keys in `app.py`.
-   Do not share logs or screenshots that expose secrets.
-   Review generated content and sources before publishing.

Recommended `.gitignore` entries:

``` gitignore
.env
.venv/
venv/
__pycache__/
*.py[cod]
.streamlit/secrets.toml
```

## Future improvements

-   Persist previous generations in a database.
-   Add stronger source validation and date-aware trend comparisons.
-   Allow country, language, or industry selection.
-   Add tests and pin dependency versions.
-   Return structured output so the article and SEO metadata can be
    displayed separately.
-   Add configurable review limits and manual approval before
    publishing.

## License

Add a license file and license details if you intend to distribute this
project publicly.
