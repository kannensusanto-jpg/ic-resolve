# IC Resolve — Demo Video Script
**Version 1.0 | Runtime: ~6 minutes | Audience: Group Controllers, CFOs, FP&A Leaders**

---

## PRE-DEMO SETUP CHECKLIST
- [ ] Backend running on localhost:8000
- [ ] Frontend running on localhost:5173
- [ ] Database is empty (fresh state — run `/api/data/seed` has NOT been clicked)
- [ ] Sample files ready on desktop: TB, IC Transactions, FX Rates, Policy DOCX
- [ ] Browser zoom at 100%, full screen
- [ ] No other tabs open

---

## SCENE 1 — THE PROBLEM (0:00–0:40)
*Start on a blank slide or title card, not the app*

**[NARRATOR]**
"Every period end, finance teams across multinational groups spend days doing the same thing manually — exporting trial balances, pasting them into spreadsheets, chasing controllers in different time zones, and trying to figure out whether a $34,000 discrepancy is a genuine posting error or just someone using yesterday's FX rate.

IC Resolve changes that. It's an AI-powered intercompany reconciliation orchestrator that takes your raw financial data, runs the full reconciliation automatically, classifies every discrepancy, drafts dispute descriptions, and gives your team a close-ready output — in minutes, not days."

**[ACTION]** Cut to browser showing IC Resolve dashboard — empty state.

---

## SCENE 2 — UPLOAD DATA (0:40–1:30)
*Dashboard, empty state*

**[NARRATOR]**
"Let's start from scratch. The only thing IC Resolve needs from you is your trial balance extract. Everything else is optional."

**[ACTION]** Click **Upload Excel** button top right.

**[NARRATOR]**
"We have three file slots. Trial balance is required. IC transaction detail and FX rates are optional — upload them for deeper analysis, or leave them out and the system derives what it needs from the TB alone."

**[ACTION]** Drop `IC_Resolve_Trial_Balance_Sample.xlsx` into the first slot.
**[ACTION]** Drop `IC_Resolve_IC_Transactions_Sample.xlsx` into the second slot.
**[ACTION]** Drop `IC_Resolve_FX_Rates_Sample.xlsx` into the third slot.

**[NARRATOR]**
"The period — March 2026 — is detected automatically from the file header. No manual configuration."

**[ACTION]** Click **Import Files**. Wait for success banner.

**[NARRATOR]**
"Fourteen IC trial balance rows, nine transactions, seven FX rates — all loaded in under two seconds."

**[ACTION]** Close the modal.

---

## SCENE 3 — RUN THE RECONCILIATION (1:30–2:15)
*Back on Dashboard, still showing empty KPI cards*

**[NARRATOR]**
"Now we run the reconciliation. One click fires three steps in sequence: normalisation, matching, and AI dispute drafting."

**[ACTION]** Click **Run with AI**.

*While loading — narrate what's happening:*

**[NARRATOR]**
"First, the normalisation layer resolves any entity name variations and applies the official FX rates to convert every local currency balance to USD.

Then the matching engine compares what each entity recorded against its counterparty — applying your tolerance thresholds, checking posting dates for timing differences, and crucially, comparing the exchange rate each entity actually used against the official rate you uploaded.

Finally, Claude drafts a plain-English dispute description for every unmatched pair — grounded in the actual journal detail."

**[ACTION]** Wait for the dashboard to populate.

**[CAPTION OVERLAY]** *"3 steps. 5 entity pairs. Completed in under 15 seconds."*

---

## SCENE 4 — DASHBOARD OVERVIEW (2:15–2:50)
*Dashboard now fully populated*

**[NARRATOR]**
"The dashboard gives us the close picture at a glance."

**[ACTION]** Point to KPI cards one by one.

**[NARRATOR]**
"Five IC pairs in scope. Two matched automatically — the management fee and the commission, both within tolerance. Three are unmatched, with a combined exposure of $1.3 million.

The pie chart breaks down the match types — one missing posting, one FX rate error, one genuine amount difference. And the bar chart shows which pairs are driving the exposure — that IC loan from NXR-UK to NXR-SG dominates at $1.2 million."

**[ACTION]** Hover over the bar chart bars briefly.

---

## SCENE 5 — RECON WORKBENCH (2:50–3:50)
*Navigate to Recon Workbench*

**[NARRATOR]**
"The Reconciliation Workbench shows every pair in detail."

**[ACTION]** Click **Recon Workbench** in the sidebar.

**[NARRATOR]**
"Let's look at the interesting one — NXR-UK and NXR-DE, the IT Services pair."

**[ACTION]** Click to expand the NXR-UK ↔ NXR-DE row.

**[NARRATOR]**
"NXR-UK recorded $316,250. NXR-DE recorded $311,246. $5,004 gap. But look at the AI reasoning."

**[ACTION]** Pause on the expanded reasoning panel.

**[NARRATOR]**
"CONFIRMED FX RATE ERROR. The gap disappears when official rates are applied. NXR-DE used a rate of 1.065 for EUR. The official rate was 1.082 — a 1.6% deviation. At the correct rate, NXR-DE's balance would be $316,214 — virtually identical to NXR-UK's $316,250. This is not a posting error. It's a stale rate."

**[ACTION]** Collapse that row. Expand the NXR-UK ↔ NXR-SG row.

**[NARRATOR]**
"NXR-UK has a $1.265 million loan receivable from NXR-SG. NXR-SG has posted nothing. Classic missing posting — the system flags it, assigns it to NXR-SG, and the dispute is already waiting in the workbench."

**[ACTION]** Close the expanded row.

**[NARRATOR]**
"You can also adjust tolerance thresholds directly from here."

**[ACTION]** Click **Tolerance** button — show the config panel briefly, then close.

---

## SCENE 6 — DISPUTE WORKBENCH (3:50–4:40)
*Navigate to Dispute Workbench*

**[ACTION]** Click **Dispute Workbench** in the sidebar.

**[NARRATOR]**
"Three disputes, automatically created. Each one has a type, an amount, an assigned owner, and an SLA deadline calculated from the close calendar."

**[ACTION]** Point to the SLA column — note any red breach indicators.

**[NARRATOR]**
"Let's expand the FX error dispute."

**[ACTION]** Click to expand the NXR-UK ↔ NXR-DE dispute row.

**[NARRATOR]**
"This is what your team would normally spend 20 minutes writing. IC Resolve drafts it in seconds — citing the entities by name, the specific amounts, and the root cause. It's ready to send directly to the NXR-DE controller."

**[ACTION]** Pause on the AI description text.

**[NARRATOR]**
"You can update the status as you work it."

**[ACTION]** Click **→ in_review**. Status badge updates.

**[NARRATOR]**
"Add a resolution note."

**[ACTION]** Type in the notes field: *"NXR-DE confirmed stale rate used. Reposting at 1.082 by COB today."* Click **Save Notes**.

---

## SCENE 7 — AI QUERY (4:40–5:15)
*Navigate to AI Query*

**[ACTION]** Click **AI Query** in the sidebar.

**[NARRATOR]**
"Instead of building a report, your controller can just ask."

**[ACTION]** Click the suggested query: *"Show me all open disputes over $50,000"*

**[NARRATOR]**
"Claude reads the live reconciliation data and answers with specific entity names and amounts."

**[ACTION]** Wait for the response to appear. Pause on it.

**[ACTION]** Type manually: *"Which entities haven't confirmed their close yet?"*

**[ACTION]** Wait for response.

**[NARRATOR]**
"Everything it tells you is grounded in the actual data — no hallucination, no guessing. It's reading the reconciliation state, not generating fiction."

---

## SCENE 8 — POLICY UPLOAD (5:15–5:40)
*Navigate to IC Policy*

**[ACTION]** Click **IC Policy** in the sidebar.

**[NARRATOR]**
"One more thing. IC Resolve lets you upload your group's reconciliation policy — and once it's active, every AI output is grounded in your specific rules."

**[ACTION]** Set label: *"Nexora IC Policy v3.2"*. Drop in `IC_Resolve_Policy_Sample.docx`. Click **Upload & Activate**.

**[NARRATOR]**
"Now when Claude drafts dispute descriptions, it applies your SLA thresholds, your escalation criteria, your ownership rules — not generic best practice. It knows, for example, that any dispute over $500,000 must be escalated to the GFC immediately."

**[ACTION]** Navigate back to Dispute Workbench. Point to the $1.2M missing posting dispute.

**[NARRATOR]**
"That $1.265 million loan dispute is above the escalation threshold. With the policy active, Claude will flag that explicitly in any description it generates."

---

## SCENE 9 — AUDIT TRAIL (5:40–6:00)
*Navigate to Audit Trail*

**[ACTION]** Click **Audit Trail** in the sidebar.

**[NARRATOR]**
"Every decision is logged. Every AI call. Every match classification. Every tolerance check. Expand any row and you see the full reasoning.

Your auditors don't have to take the system's word for it — they can trace every output back to the data that produced it."

**[ACTION]** Expand a match_decision entry. Show the rate detail JSON briefly.

---

## SCENE 10 — CLOSE (6:00–6:20)
*Return to Dashboard*

**[ACTION]** Navigate back to Dashboard.

**[NARRATOR]**
"Trial balance in. Policy loaded. Reconciliation run. Disputes assigned. Close pack ready.

IC Resolve turns a two-day spreadsheet exercise into a 15-second automated process — with an AI that understands your policy, explains every decision, and gives your controllers a dispute workbench they can actually act on.

This is what period-end close looks like when finance automation is done properly."

**[ACTION]** Slowly zoom out to show the full dashboard.

**[CAPTION OVERLAY]** *IC Resolve — AI-Powered Intercompany Reconciliation*

---

## RECORDING NOTES

**Pace:** Speak at ~130 words/minute. The narration is written slightly long — trim in delivery.

**Pauses:** Add a 1-second pause after each `[ACTION]` before continuing narration. Let the UI breathe.

**B-roll opportunities:**
- Close-up of the FX rate error reasoning text (Scene 5) — this is the money shot
- The dispute AI description panel (Scene 6)
- The audit trail JSON detail (Scene 9)

**If demoing live (not recorded):** Skip Scene 1 slide and open directly on the empty dashboard. Keep a pre-seeded database as a fallback in case the live run is slow.

**Suggested title card text:**
> *"IC Resolve — from raw trial balance to close-ready reconciliation in under 60 seconds"*
