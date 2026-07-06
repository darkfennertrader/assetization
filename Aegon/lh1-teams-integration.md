---
title: "LH1 — Teams Integration Design Note"
subtitle: "Investor Relations Agent: live-call architecture using Microsoft Teams"
author: "Raimondo Marino, Solution AI Architect"
date: "2026-07-01"
status: "AGREED — MVP scope locked"
---

# LH1 — Teams Integration Design Note

## 1. Context

The Investor Relations Agent must assist the CEO/CFO **during live investor calls**. The platform for those calls is **Microsoft Teams** (Teams-only, Zoom/Webex/phone are out of scope for PoC and MVP).

This note documents the integration pattern chosen, the rationale, the prerequisite checklist for Aegon, and the precise data flows for both the **live-call** and **post-call archive** paths.

---

## 2. Two patterns evaluated

| | Pattern A — Teams Media Bot | Pattern B — Meeting Side Panel ✅ CHOSEN |
|---|---|---|
| **How audio enters Azure** | Bot Framework app joins meeting as a participant via Graph Communications Calling API; receives raw RTP audio per speaker | Teams native Live Transcription API emits diarized text events; our app consumes the event stream |
| **Who does the STT** | Azure AI Speech in real time (our compute) | Microsoft (native Teams feature) |
| **Speaker identification** | From Graph API call roster | Built into Live Transcription events |
| **UX for CEO/CFO** | Separate browser window | Side panel **inside** the Teams meeting window |
| **Infrastructure** | Bot Framework registration + Windows Server VM or AKS (media plugin) | Teams app registration + ACA container |
| **Teams Premium required** | No (media bot works on standard) | **Yes** (Live Transcription API for external meetings) |
| **Setup effort** | 2–3 weeks | ~3 days |
| **Best for MVP** | ❌ Over-engineered | ✅ Right size |

**Decision: Pattern B — Meeting Side Panel App via Teams Live Transcription API.**

Teams Premium licence confirmed available at Aegon for the executive tier.

---

## 3. What TTS (Text-to-Speech) does in this design

**TTS is explicitly ruled out for LH1 MVP — and should never be added without a dedicated compliance review.**

- The agent produces a **text answer + citations**, displayed in the side panel.
- The **CEO or CFO reads the answer and speaks it aloud** on the call.
- The AI voice must never appear on an investor/earnings call. The reputational, compliance, and legal exposure (MiFID II, MAR, voice-cloning regulations) is unacceptable.
- This is a permanent architectural constraint, not a temporary limitation.

---

## 4. Aegon pre-requisite checklist

Before any code is written for LH1's live-call path, Aegon IT / compliance must confirm:

| # | Prerequisite | Owner | Status |
|---|---|---|---|
| P1 | Teams Premium licence active for IR team, CEO, CFO | Aegon IT | ⬜ To confirm |
| P2 | Teams admin consent granted for `OnlineMeetingTranscript.Read.All` Graph permission (app-level) | Aegon Tenant Admin | ⬜ To confirm |
| P3 | Meeting transcription policy enabled for the executive Teams group | Aegon IT | ⬜ To confirm |
| P4 | Teams app manifest approved and sideloaded into the Aegon tenant (or published to internal app catalogue) | Aegon IT + PwC builder | ⬜ To confirm |
| P5 | Participant consent mechanism reviewed by Legal / Compliance (GDPR, NL data protection) | Aegon Legal | ⬜ To confirm |
| P6 | IR meeting invite template updated to include consent notice for attendees | Aegon IR team | ⬜ To confirm |
| P7 | Teams meeting recording policy confirmed (is recording enabled for IR calls?) | Aegon IT | ⬜ To confirm |

---

## 5. Live-call data flow (sequence)

```
CEO/CFO opens Teams meeting on device
        │
        ▼
Meeting Side Panel App launches automatically
(Teams app manifest → auto-launch on meeting start)
        │
        ▼
Consent banner displayed to all participants
(native Teams feature — no custom code needed)
        │
        ▼
Analyst asks a question verbally on the call
        │
        ▼
Teams Live Transcription API (Microsoft-hosted)
· Speaker-labelled transcript event emitted (<1s latency)
· Event payload: { speaker: "Analyst Name", text: "What is your..." }
        │
        ▼
Side Panel App (Teams SDK v2, runs in meeting iframe)
· Receives event via notifyAppHandleOnMeeting() / getTranscript()
· Detects: is this speaker an analyst? (compare roster vs. analyst list)
· Sends HTTP POST to Azure APIM AI Gateway:
  { question: "...", speaker_id: "...", call_id: "..." }
        │
        ▼
APIM AI Gateway
· Validates Entra ID token of the Side Panel app
· Routes to LangGraph Orchestrator
        │
        ▼
LangGraph Orchestrator
┌────────────────────────────────────────────┐
│ 1. /sentiment tool                          │
│    → Cosmos DB: look up analyst profile     │
│    → Returns: likely topics, sentiment,     │
│      prior questions from this analyst      │
│                                             │
│ 2. /rag tool                                │
│    → Azure AI Search LH1 index             │
│    → Hybrid search: Q&A deck + archived     │
│      transcripts, cited                     │
│    → Returns: top-k passages + citations    │
│                                             │
│ 3. GPT-4o (via Azure OpenAI)               │
│    → Synthesises answer                     │
│    → Respects CEO/CFO tone hint             │
│    → Includes citation references           │
└────────────────────────────────────────────┘
        │
        ▼
HITL Gate (LangGraph interrupt node)
· Packages: suggested_answer, citations, confidence_score
        │
        ▼  (sub-200ms target from question detection to answer display)
Side Panel App (in Teams meeting)
┌─────────────────────────────────────────────┐
│ Suggested answer                             │
│ ─────────────────────────────────────────── │
│ "Aegon's capital position remains strong…"  │
│                                              │
│ Sources: [Q4 2025 Q&A deck p.3] [AR 2024]  │
│ Analyst: J. Smith (ING) — focus: capital    │
│ Confidence: ●●●○○                           │
│                                              │
│  [Use this answer]  [Skip]  [Edit & use]    │
└─────────────────────────────────────────────┘
CEO/CFO READS the answer and SPEAKS it
        │
        ▼
CEO/CFO clicks [Use this answer] (or [Skip])
        │
        ▼
Orchestrator receives HITL approval signal
· Writes Q&A entry to Cosmos DB (call notes)
· Queues for post-call knowledge capture
```

---

## 6. Post-call archive flow

After the Teams meeting ends:

```
Teams recording saved to SharePoint / Microsoft Stream
(if recording policy is enabled — see P7 above)
        │
        ▼
Logic Apps (scheduled, ~30 min post-call)
· Detects new recording via Graph API (Drives or Stream)
· Copies recording file to ADLS Gen2 / Blob
        │
        ▼
LH1 /batch-stt MCP tool (triggered by Blob event)
· Azure AI Speech batch transcription
· High-accuracy re-transcription with custom financial vocabulary
· Produces VTT + JSON transcript with speaker diarization
        │
        ▼
Transcript written to:
· Blob (raw archive)
· Azure AI Search LH1 index (chunked, with call_id + date + analyst metadata)
        │
        ▼
Q&A entries from Cosmos DB merged with transcript
· Enriches the index: "this question was answered this way on this call"
· Available for next call's /rag context
```

---

## 7. What is explicitly out of scope for LH1 MVP

| Feature | Status | Reason |
|---|---|---|
| TTS (agent speaks on the call) | ❌ Permanently out | Compliance, reputational, legal risk |
| Zoom / Webex / phone support | ❌ Phase 2 | Requires separate integration per platform |
| Teams Media Bot (Pattern A) | ❌ Not used | Over-engineered for MVP |
| Sentiment analysis during the call (real-time tone detection) | ❌ Phase 2 | Privacy risk; live tone analysis of analysts is legally sensitive |
| Analyst Q predicted before they speak | ❌ Phase 2 | Requires prior call history; available after first cycle |
| Autonomous question detection without IR triggering | ❌ Phase 2 | For MVP, IR team activates side panel manually |

---

## 8. Teams app components (what the TypeScript engineer builds)

| Component | Technology | Effort estimate |
|---|---|---|
| Teams app manifest + registration | Teams Dev Portal | 0.5 day |
| Side Panel React app (Fluent UI v9) | TypeScript / React / Teams SDK v2 | 3 days |
| Live transcript event handler | `microsoftTeams.meeting.getLiveTranscript()` polling or webhook | 1 day |
| APIM call (question → answer) | `fetch` with Entra token (MSAL) | 0.5 day |
| Answer display + HITL buttons | Fluent UI components | 1 day |
| Post-call export to Cosmos DB | Azure SDK for JS | 0.5 day |
| **Total TypeScript work (LH1 Teams path)** | | **~6–7 days** |

The backend (LangGraph orchestrator + `/rag` + `/sentiment` tools) is shared with the other lighthouses and is built by the Python/ML engineer in parallel.

---

*Owner: Raimondo Marino — reviewed with: Michael (implementer) · Last updated: 2026-07-01*
