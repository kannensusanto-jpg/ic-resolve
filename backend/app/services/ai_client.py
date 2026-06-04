import os
import anthropic

_client: anthropic.Anthropic | None = None

IC_SYSTEM_PROMPT = (
    "You are an expert intercompany reconciliation analyst with deep knowledge of multinational "
    "financial close processes, FX translation, intercompany agreement structures, and dispute resolution.\n\n"
    "Your responsibilities:\n"
    "- Diagnose IC reconciliation discrepancies and identify root causes precisely\n"
    "- Draft concise, professional dispute descriptions for finance controllers\n"
    "- Summarise period-end close status for CFO close packs\n"
    "- Answer natural language queries about reconciliation data with specific entity names and amounts\n\n"
    "Always cite entity names explicitly, reference amounts with their currency, and maintain a "
    "professional, audit-ready tone. Be specific — vague answers are not acceptable in a close context."
)


def _get_client() -> anthropic.Anthropic:
    global _client
    if _client is None:
        _client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY", ""))
    return _client


def _build_system(policy_text: str | None) -> list[dict]:
    """
    Build the system array for a Claude API call.
    The base system prompt is always cached.
    If a policy document is present it's injected as a second cached block —
    this means the policy text is cached separately and reused across calls
    without re-sending, keeping latency and cost low even for large documents.
    """
    blocks = [
        {"type": "text", "text": IC_SYSTEM_PROMPT, "cache_control": {"type": "ephemeral"}},
    ]
    if policy_text:
        blocks.append({
            "type": "text",
            "text": (
                "The client has provided their intercompany reconciliation policy below. "
                "You must apply this policy when classifying disputes, drafting descriptions, "
                "answering queries, and generating summaries. Where the policy sets specific rules "
                "(e.g. tolerance thresholds, ownership rules, escalation criteria, SLA definitions), "
                "those rules take precedence over general best practice.\n\n"
                "=== CLIENT IC POLICY ===\n\n"
                + policy_text
            ),
            "cache_control": {"type": "ephemeral"},
        })
    return blocks


def draft_dispute_description(
    entity_a: str,
    entity_b: str,
    dispute_type: str,
    amount_gbp: float,
    amount_a_gbp: float,
    amount_b_gbp: float,
    period: str,
    journal_details: str,
    policy_text: str | None = None,
) -> tuple[str, str]:
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=512,
        system=_build_system(policy_text),
        messages=[{
            "role": "user",
            "content": (
                f"Draft a dispute description for this IC reconciliation discrepancy.\n\n"
                f"Entity pair: {entity_a} ↔ {entity_b}\n"
                f"Period: {period}\n"
                f"Dispute type: {dispute_type}\n"
                f"Discrepancy: {amount_gbp:,.0f}\n"
                f"{entity_a} balance: {amount_a_gbp:,.0f}\n"
                f"{entity_b} balance: {amount_b_gbp:,.0f}\n"
                f"Journal details: {journal_details}\n\n"
                "Apply the client policy where relevant (ownership rules, SLA, escalation thresholds).\n\n"
                "Write exactly two lines:\n"
                "DESCRIPTION: <2-3 sentence plain-English description for a finance manager>\n"
                "REASONING: <1 sentence explaining the classification, referencing the policy if applicable>"
            ),
        }],
    )
    text = response.content[0].text
    description, reasoning = "", ""
    for line in text.strip().splitlines():
        if line.startswith("DESCRIPTION:"):
            description = line[len("DESCRIPTION:"):].strip()
        elif line.startswith("REASONING:"):
            reasoning = line[len("REASONING:"):].strip()
    return description or text.strip(), reasoning or "AI-classified based on balance discrepancy pattern."


def generate_close_summary(
    stats: dict,
    disputes: list,
    period: str,
    policy_text: str | None = None,
) -> str:
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=900,
        system=_build_system(policy_text),
        messages=[{
            "role": "user",
            "content": (
                f"Generate a close pack summary for the CFO for period {period}.\n\n"
                f"Reconciliation statistics:\n{stats}\n\n"
                f"Open disputes:\n{disputes}\n\n"
                "Apply the client policy when assessing severity and required actions. "
                "Write exactly 3 paragraphs:\n"
                "1. Overall status (headline numbers)\n"
                "2. Key issues requiring immediate attention — cite policy thresholds where relevant\n"
                "3. Recommended next steps and owners"
            ),
        }],
    )
    return response.content[0].text


def answer_query(
    query: str,
    context: str,
    period: str,
    policy_text: str | None = None,
) -> tuple[str, str]:
    client = _get_client()
    response = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=800,
        system=_build_system(policy_text),
        messages=[{
            "role": "user",
            "content": (
                f"Current reconciliation data for period {period}:\n\n"
                f"{context}\n\n"
                f"User query: {query}\n\n"
                "Answer specifically using entity names and amounts from the data. "
                "Where the client policy sets relevant rules or thresholds, apply and cite them."
            ),
        }],
    )
    return response.content[0].text, "claude-sonnet-4-6"
