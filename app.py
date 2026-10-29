
import asyncio
import os
from datetime import datetime
from io import StringIO

import streamlit as st
from ddgs import DDGS
from dotenv import load_dotenv

from autogen_agentchat.agents import AssistantAgent
from autogen_agentchat.conditions import TextMentionTermination
from autogen_agentchat.teams import RoundRobinGroupChat
from autogen_ext.models.openai import OpenAIChatCompletionClient


# ============================================================
# 1. CONFIGURATION
# ============================================================

load_dotenv()

API_KEY = os.getenv("OPENAI_API_KEY")
MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

MAX_TEAM_TURNS = 6
MAX_SEARCH_RESULTS = 3

st.set_page_config(
    page_title="AI SEO Content Studio",
    page_icon="🚀",
    layout="wide",
)


# ============================================================
# 2. STREAMLIT UI
# ============================================================

st.title("🚀 AI SEO Content Studio")
st.caption(
    "Research trends, generate content, optimize SEO, "
    "and review quality using four AI agents."
)

with st.sidebar:
    st.header("⚙️ Settings")

    word_count = st.select_slider(
        "Article length",
        options=[500, 700, 1000, 1500, 2000],
        value=700,
    )

    target_audience = st.text_input(
        "Target audience",
        value="General online audience",
    )

    writing_tone = st.selectbox(
        "Writing tone",
        [
            "Professional",
            "Informative",
            "Conversational",
            "Friendly",
            "Persuasive",
        ],
    )

    st.markdown("---")
    st.caption(f"Model: {MODEL}")
    st.caption("Maximum team turns: 6")
    st.caption("Web results per search: 3")


# ============================================================
# 3. WEB RESEARCH
# ============================================================

def search_web(topic: str) -> str:
    """
    Search for recent information related to the user's topic.
    Returns a small number of results to reduce research time.
    """

    query = (
        f"{topic} latest trends "
        f"{datetime.now().year}"
    )

    results = []

    try:
        with DDGS() as ddgs:
            search_results = ddgs.text(
                query,
                max_results=MAX_SEARCH_RESULTS,
            )

            for item in search_results:
                results.append(
                    "\n".join(
                        [
                            f"Title: {item.get('title', '')}",
                            f"Snippet: {item.get('body', '')}",
                            f"URL: {item.get('href', '')}",
                        ]
                    )
                )

    except Exception as exc:
        return (
            f"Web search failed: {exc}\n"
            "No verified search results are available. "
            "Clearly disclose this limitation and do not "
            "invent sources or claim that trends are verified."
        )

    if not results:
        return (
            "No web search results were returned. "
            "Do not invent sources, statistics, or current trends."
        )

    return "\n\n".join(results)


# ============================================================
# 4. HELPER FUNCTIONS
# ============================================================

def get_message_text(message) -> str:
    """Extract readable text from an AutoGen message."""

    content = getattr(message, "content", "")

    if isinstance(content, str):
        return content

    if isinstance(content, list):
        parts = []

        for item in content:
            text = getattr(item, "text", None)

            if text:
                parts.append(text)
            else:
                parts.append(str(item))

        return "\n".join(parts)

    return str(content)


def get_agent_name(message) -> str:
    """Get the sender name from an AutoGen message."""

    return getattr(message, "source", "System")


# ============================================================
# 5. AGENT 1 — SEO RESEARCHER
# ============================================================

async def run_researcher(
    topic: str,
    search_results: str,
    model_client,
) -> str:

    researcher = AssistantAgent(
        name="seo_researcher",
        model_client=model_client,
        system_message=f"""
You are an SEO Research Analyst.

Your task is to research the topic: {topic}

Use the supplied web search results as your evidence.

Produce a concise research report containing:

1. Topic overview.
2. Recent or potentially trending angles.
3. Search intent.
4. Primary keyword.
5. Five to eight related keywords.
6. Long-tail keyword opportunities.
7. Audience questions and pain points.
8. Three possible article angles.
9. Recommended article angle and reasons.
10. Source URLs and the claims each source supports.

Important rules:
- Distinguish verified facts from your own suggestions.
- Search snippets alone may not verify every claim.
- Do not invent search volume, traffic figures, statistics,
  publication dates, or source URLs.
- If evidence is insufficient, say so explicitly.
- Do not claim that a topic is definitively trending based
  only on a few search results.
- Keep the report useful and concise.
""",
    )

    task = f"""
TOPIC:
{topic}

WEB SEARCH RESULTS:
{search_results}

Analyze the results and prepare the SEO research report.
"""

    result = await researcher.run(task=task)

    return get_message_text(result.messages[-1])


# ============================================================
# 6. AGENT 2 — CONTENT WRITER
# ============================================================

def create_writer(model_client, word_count, audience, tone):

    return AssistantAgent(
        name="content_writer",
        model_client=model_client,
        system_message=f"""
You are an experienced SEO content writer.

Write an original, useful article using the research report
and the user's requested topic.

Requirements:
- Target length: approximately {word_count} words.
- Target audience: {audience}.
- Writing tone: {tone}.
- Use the primary keyword naturally.
- Address the reader's search intent.
- Use a compelling H1 title.
- Organize content with logical H2 and H3 headings.
- Include an introduction, useful body sections,
  and a conclusion.
- Include practical examples where appropriate.
- Avoid keyword stuffing, repetition, and exaggerated claims.
- Do not invent statistics, quotations, or citations.
- Preserve source URLs when referencing researched facts.
- Write useful content for people, not just search engines.
- Return the complete article in Markdown.

When revising, use the latest reviewer feedback.
Return the complete revised article, not just a list of edits.
""",
    )


# ============================================================
# 7. AGENT 3 — SEO OPTIMIZER
# ============================================================

def create_optimizer(model_client):

    return AssistantAgent(
        name="seo_optimizer",
        model_client=model_client,
        system_message="""
You are a technical SEO content optimizer.

Review the article written by the content writer.

Your responsibilities:

1. Improve the SEO title.
2. Write a meta description of approximately 150–160 characters.
3. Suggest a concise URL slug.
4. Identify the primary and secondary keywords.
5. Improve H1, H2, and H3 heading structure.
6. Improve keyword placement without stuffing.
7. Suggest internal link opportunities.
8. Suggest relevant image ideas and descriptive alt text.
9. Identify missing search-intent questions.
10. Improve readability and content organization.

Rules:
- Keep the article accurate, readable, and useful.
- Do not fabricate internal URLs.
- Label internal link suggestions as suggestions.
- Do not invent keyword search volumes or SEO scores.
- Preserve useful source links and factual qualifications.
- Include the complete optimized article in Markdown.
- Put the SEO metadata in a separate, clearly labeled section.

If the reviewer provides feedback, address it in the next
optimization pass.
""",
    )


# ============================================================
# 8. AGENT 4 — CONTENT REVIEWER
# ============================================================

def create_reviewer(model_client):

    return AssistantAgent(
        name="content_reviewer",
        model_client=model_client,
        system_message="""
You are a strict but constructive SEO content reviewer.

Review the latest optimized article and its SEO metadata.

Evaluate:
1. Relevance to the topic and search intent.
2. Accuracy and support for factual claims.
3. Content usefulness and completeness.
4. Grammar, readability, and structure.
5. Natural keyword usage.
6. Title and meta description quality.
7. Heading hierarchy.
8. Potentially misleading claims.
9. Source and citation quality.
10. Whether the content satisfies the target audience.

If the article has significant problems:
- Explain the specific issues.
- Give actionable corrections.
- End your response with the exact standalone marker:
  NEEDS_REVISION

If the article meets the requirements:
- Give a concise review summary.
- State any remaining limitations.
- End your response with the exact standalone marker:
  APPROVE

Approval rules:
- Do not approve unsupported factual claims.
- Do not claim that keyword rankings or traffic are guaranteed.
- Do not approve simply to finish the workflow.
- Apply reasonable standards for a useful first draft.
- Keep feedback concise and actionable.
- The final marker must be on its own final line.

When you receive a revised article, review that latest version.
""",
    )


# ============================================================
# 9. MULTI-AGENT WORKFLOW
# ============================================================

async def generate_seo_content(
    topic: str,
    word_count: int,
    audience: str,
    tone: str,
    api_key: str,
    model: str,
    live_output,
):

    model_client = OpenAIChatCompletionClient(
        model=model,
        api_key=api_key,
    )

    try:
        # ----------------------------------------------------
        # STEP 1: Search the web
        # ----------------------------------------------------

        live_output.markdown(
            "### 🔎 Agent 1: SEO Researcher\n"
            "Searching for relevant information..."
        )

        search_results = await asyncio.to_thread(
            search_web,
            topic,
        )

        # ----------------------------------------------------
        # STEP 2: Create the research report
        # ----------------------------------------------------

        research_report = await run_researcher(
            topic,
            search_results,
            model_client,
        )

        live_output.markdown(
            "### 🔎 Agent 1: SEO Researcher\n"
            "Research report completed.\n\n"
            "### ✍️ Agents 2–4: Writer, Optimizer and Reviewer\n"
            "Starting the content workflow..."
        )

        # ----------------------------------------------------
        # STEP 3: Create the remaining agents
        # ----------------------------------------------------

        writer = create_writer(
            model_client,
            word_count,
            audience,
            tone,
        )

        optimizer = create_optimizer(model_client)

        reviewer = create_reviewer(model_client)

        # Stop when the reviewer explicitly approves.
        # max_turns provides an additional hard limit.
        termination = TextMentionTermination(
            "APPROVE",
            sources=["content_reviewer"],
        )

        team = RoundRobinGroupChat(
            participants=[
                writer,
                optimizer,
                reviewer,
            ],
            termination_condition=termination,
            max_turns=MAX_TEAM_TURNS,
        )

        task = f"""
USER'S TOPIC:
{topic}

TARGET ARTICLE LENGTH:
Approximately {word_count} words.

TARGET AUDIENCE:
{audience}

WRITING TONE:
{tone}

SEO RESEARCH REPORT:
{research_report}

WORKFLOW INSTRUCTIONS:

1. The content writer creates the initial article.
2. The SEO optimizer optimizes the article and metadata.
3. The content reviewer checks the optimized result.
4. If the reviewer returns NEEDS_REVISION, the writer must
   revise the article using the feedback.
5. The optimizer must optimize the revised article.
6. The reviewer must check the latest version.
7. Repeat this sequence only while team turns remain.

The reviewer must return APPROVE when the latest version
satisfies the review requirements.

If the maximum turn limit is reached without approval,
stop and report that the article was not approved.

Keep each agent's response focused. Return complete article
content when writing or revising, but avoid unrelated commentary.
"""

        # ----------------------------------------------------
        # STEP 4: Stream agent messages live
        # ----------------------------------------------------

        messages = []
        latest_by_agent = {}
        agent_log = []

        async for event in team.run_stream(task=task):

            # AutoGen streams chat messages and a final TaskResult.
            source = getattr(event, "source", None)

            if not source:
                continue

            content = get_message_text(event)

            messages.append(event)
            latest_by_agent[source] = content

            agent_log.append(
                f"### {source.replace('_', ' ').title()}\n\n"
                f"{content}"
            )

            # Show the latest agent response while processing.
            live_output.markdown(
                "\n\n---\n\n".join(agent_log[-4:])
            )

        # ----------------------------------------------------
        # STEP 5: Extract the final results
        # ----------------------------------------------------

        final_article = (
            latest_by_agent.get("seo_optimizer")
            or latest_by_agent.get("content_writer")
            or ""
        )

        final_review = latest_by_agent.get(
            "content_reviewer",
            "The reviewer did not return a review.",
        )

        # Approval must come from the latest reviewer response.
        review_lines = [
            line.strip()
            for line in final_review.splitlines()
            if line.strip()
        ]

        last_line = review_lines[-1] if review_lines else ""

        approved = last_line == "APPROVE"

        # Determine why the workflow ended.
        if approved:
            stop_reason = "The content reviewer approved the article."
        else:
            stop_reason = (
                "The workflow ended without explicit approval. "
                "Review the feedback and revise the article manually."
            )

        return {
            "topic": topic,
            "research": research_report,
            "article": final_article,
            "review": final_review,
            "approved": approved,
            "message_count": len(messages),
            "stop_reason": stop_reason,
            "transcript": "\n\n---\n\n".join(agent_log),
        }

    finally:
        await model_client.close()


# ============================================================
# 10. MAIN STREAMLIT FORM
# ============================================================

with st.form("seo_form"):

    topic = st.text_input(
        "Enter your SEO topic",
        placeholder="Example: AI tools for small businesses",
    )

    submitted = st.form_submit_button(
        "🚀 Generate SEO Content",
        use_container_width=True,
    )


if submitted:

    if not API_KEY:
        st.error(
            "OPENAI_API_KEY is missing. Add it to your .env file "
            "and restart Streamlit."
        )

    elif not topic.strip():
        st.warning("Please enter a topic before generating content.")

    else:
        live_output = st.empty()

        with st.status(
            "Running the SEO multi-agent workflow...",
            expanded=True,
        ) as status:

            try:
                result = asyncio.run(
                    generate_seo_content(
                        topic=topic.strip(),
                        word_count=word_count,
                        audience=target_audience,
                        tone=writing_tone,
                        api_key=API_KEY,
                        model=MODEL,
                        live_output=live_output,
                    )
                )

                status.update(
                    label="SEO workflow finished",
                    state="complete",
                    expanded=False,
                )

                st.session_state["seo_result"] = result

            except Exception as exc:
                status.update(
                    label="SEO workflow failed",
                    state="error",
                    expanded=True,
                )

                st.error(f"An error occurred: {exc}")

                st.info(
                    "Check your API key, internet connection, "
                    "installed package versions, and terminal logs."
                )


# ============================================================
# 11. DISPLAY RESULTS
# ============================================================

if "seo_result" in st.session_state:

    result = st.session_state["seo_result"]

    st.divider()

    st.header("📊 SEO Content Results")

    if result["approved"]:
        st.success("Content approved by the reviewer.")
    else:
        st.warning(
            "Content was generated, but final approval was not "
            "confirmed. Check the review feedback before publishing."
        )

    st.caption(result["stop_reason"])

    tab_research, tab_article, tab_review, tab_log = st.tabs(
        [
            "🔎 Research",
            "📝 Optimized Article",
            "✅ Review",
            "📜 Agent Transcript",
        ]
    )

    with tab_research:
        st.subheader("Research Report")

        st.markdown(result["research"])

    with tab_article:
        st.subheader("Optimized Content")

        if result["article"].strip():
            st.markdown(result["article"])

            st.download_button(
                label="⬇️ Download Article as Markdown",
                data=result["article"],
                file_name="seo_article.md",
                mime="text/markdown",
                use_container_width=True,
            )
        else:
            st.warning(
                "No article content was returned. "
                "Try generating the article again."
            )

    with tab_review:
        st.subheader("Content Review")

        st.markdown(result["review"])

        st.metric(
            "Agent messages received",
            result["message_count"],
        )

        if result["approved"]:
            st.success("Final status: APPROVED")
        else:
            st.warning("Final status: NOT APPROVED")

    with tab_log:
        st.subheader("Agent Activity")

        st.markdown(result["transcript"])

        st.download_button(
            label="⬇️ Download Agent Transcript",
            data=result["transcript"],
            file_name="seo_agent_transcript.md",
            mime="text/markdown",
            use_container_width=True,
        )

    st.divider()

    if st.button("🗑️ Clear Results"):
        del st.session_state["seo_result"]
        st.rerun()


# ============================================================
# 12. FOOTER
# ============================================================

st.divider()

st.caption(
    "Built with AutoGen, OpenAI, DuckDuckGo Search and Streamlit. "
    "Always fact-check sources and review content before publishing."
)
