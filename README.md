# AgentFoundry — a multi-agent healthcare backend with an auditable message bus

**Nine specialised medical agents that talk to each other over a priority message bus, on top of a
domain-adapted BioMistral-7B, with every inter-agent message anchored to an on-chain audit log.**

[![Python](https://img.shields.io/badge/python-3.10+-8B7CF6?style=flat-square)](#running-it)
[![FastAPI](https://img.shields.io/badge/FastAPI-async-4BC8C0?style=flat-square)](#api-surface)
[![Model](https://img.shields.io/badge/BioMistral--7B-LoRA%20fine--tuned-15181D?style=flat-square)](#the-fine-tune)
[![Solidity](https://img.shields.io/badge/Solidity-0.8.28-15181D?style=flat-square)](#why-a-blockchain-is-here-at-all)
[![Status](https://img.shields.io/badge/status-hackathon%20prototype-ef4444?style=flat-square)](#status-and-honest-limits)

Built by team **HealthFourUs** for the Periscope 2025 hackathon, against the problem statement:
*"smart, adaptive AI avatars that learn, evolve, and communicate with each other."*

A single large model asked to "be a doctor" collapses several different jobs into one prompt: reading an image,
reconciling a medication list, deciding whether something is an emergency, and writing to a medical record.
Those jobs have different inputs, different failure modes and very different consequences if they go wrong.

AgentFoundry splits them into nine agents with explicit specialisations and makes them communicate through a
**central message bus with priority routing**, so that an emergency message overtakes a records lookup rather
than queueing behind it. Every message is logged, and the last 100 are streamed over WebSocket so you can watch
the agents negotiate in real time instead of inferring it from output.

---

## The agents

| Agent | Responsibility |
|---|---|
| `diagnostic_agent` | Forms differential diagnoses from symptoms and history |
| `imaging_agent` | Reads medical images; OCR for scanned reports and prescriptions |
| `treatment_agent` | Proposes treatment plans against the retrieved knowledge base |
| `medication_agent` | Reconciles medication lists and checks interactions |
| `emergency_agent` | Decides whether a case must escalate now, and preempts the queue when it must |
| `records_agent` | Reads and writes the patient record |
| `doctor_notify_agent` | Brings a human clinician into the loop |
| `patient_avatar_agent` | Holds the patient-facing conversational persona |
| `blockchain_agent` | Anchors agent decisions and messages to the on-chain audit log |

All nine inherit from `BaseAgent`, which fixes the contract: an id, a name, a specialisation, a status
(`idle` / `processing` / `error`), a message history, and a single `send_message(to, type, payload, priority)`
path. An agent cannot talk to another agent except through the bus, which is what makes the conversation
auditable rather than implicit.

### The message bus

`agents/message_bus.py` is a registry plus a **priority queue** (`heapq`), an append-only `message_log`, a
rolling 100-message buffer for live streaming, and an event-type subscription map so agents can react to
classes of event rather than being addressed directly. Priority is explicit on every send and defaults to 3,
so raising urgency is a deliberate act.

---

## The fine-tune

The conversational layer is **BioMistral-7B** adapted with LoRA:

| Setting | Value |
|---|---|
| Base model | `BioMistral/BioMistral-7B` |
| Method | LoRA, `task_type=CAUSAL_LM` |
| Rank / alpha / dropout | `r=16` / `32` / `0.05` |
| Target modules | `q_proj`, `k_proj`, `v_proj`, `o_proj` |
| Training length | checkpoints at 6000, 6200, 6250 steps |

The point of the fine-tune is **Indian clinical context**, which a general medical model trained largely on
Western data gets wrong. `prepare_dataset.py` mixes public conversation corpora (HealthCareMagic-100k,
iCliniq) and mental-health data with a hand-written India-specific set covering the things that actually walk
into an Indian OPD, including code-mixed Hinglish phrasing as patients really write it:

- A cough lasting over two weeks triggers a **TB workup** (chest X-ray, CBNAAT/GeneXpert) rather than a generic
  cough response.
- Orange-red urine after starting treatment is **Rifampicin**, a harmless side effect of the AKT-4 kit — and
  the answer tells the patient *not to stop the medication*, because stopping is the real danger.
- Breathlessness plus work in a stone-crushing unit points to **silicosis**, with its TB comorbidity.
- A matted painless neck swelling raises **scrofula** (tuberculous lymphadenitis) and an FNAC for AFB.
- An eschar with fever and travel history is **scrub typhus**: start doxycycline, send IgM ELISA.
- Avoid Combiflam (an NSAID) in suspected **dengue** because of bleeding risk.
- Inhalers are **not addictive** — answering a specific, widespread myth rather than a textbook question.

Each of those is a case where a plausible-sounding generic answer is a clinically wrong answer in India.

---

## Why a blockchain is here at all

Three Solidity contracts, and each has a job that a database genuinely does less well:

| Contract | What it is for |
|---|---|
| `AgentCommunicationLog.sol` | A tamper-evident record that agent A told agent B X at time T. If an automated decision is later disputed, the log cannot be quietly rewritten by whoever owns the server. |
| `AccessControl.sol` | On-chain permissioning over who may read or write a record. |
| `HealthToken.sol` | The incentive/settlement primitive for the platform. |

This is the honest version of the argument: the audit log is the part that benefits from being
append-only and independently verifiable. Patient records themselves are **not** put on chain.

---

## Retrieval

`rag/` is a conventional four-part pipeline — `embeddings.py`, `vector_store.py`, `knowledge_bases.py`,
`retrieval.py` — with knowledge bases kept separate per domain so a treatment lookup does not retrieve from an
unrelated corpus. Treatment proposals are grounded in retrieved text rather than generated free-hand.

## API surface

FastAPI, async throughout:

| Route | Purpose |
|---|---|
| `/agents` | Agent registry, status, and the live message stream |
| `/chat` | Patient-facing conversation |
| `/patient` | Record read/write |
| `/medical_images` | Image analysis |
| `/ocr` | Scanned reports and prescriptions |
| `/blockchain` | Audit log and contract interaction |

## Repository map

| Path | Contents |
|---|---|
| `agents/` | The nine agents, `base_agent.py`, `message_bus.py` |
| `api/routes/` | FastAPI routers, schemas, dependencies |
| `blockchain/` | Solidity contracts and `deploy.py` |
| `rag/` | Embeddings, vector store, knowledge bases, retrieval |
| `models/` | Model loading and inference |
| `database/` | SQLAlchemy models and session handling |
| `prepare_dataset.py` | Builds the fine-tuning mixture |

## Running it

```bash
pip install -r requirements.txt
cp env.example .env          # provider keys, DB URL, chain RPC
python main.py               # FastAPI app
```

`cpu_test.py` checks that inference runs without a GPU. Datasets and adapter weights are not committed;
`prepare_dataset.py` rebuilds the training mixture.

---

## Status and honest limits

A **hackathon prototype**. It is not a medical device, it has not been clinically validated, and it must not be
used to make real clinical decisions.

- **The fine-tune has no evaluation.** There is no held-out benchmark, no accuracy or quality metric and no
  LLM-judge harness in this repository. The adapter weights exist and the training mixture is reproducible, but
  any claim about how much the fine-tune improved anything would be unmeasured. This is the most important
  piece of unfinished work here, and it is stated rather than papered over.
- **No clinician review.** The India-specific training pairs were written from reference material, not
  validated by a practising physician.
- **The emergency path is not a safety system.** `emergency_agent` raises priority on the bus; it is not a
  certified triage system and there is no guaranteed latency bound.
- **Contracts are unaudited** and were deployed to a test network only.
- **Patient data handling is prototype-grade** — adequate for a demo, not for real patient data under DPDP or
  HIPAA.

---

## Team

**HealthFourUs** — Aryan Lomte, Shivam Verma, Aditya Yadav, Sujal Thakkar.

Related repositories: the Next.js 3D frontend lives in
[HealthFourUS](https://github.com/Aryan-lomte05/HealthFourUS).
