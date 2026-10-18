# Clinical Trial Agent

A tool-calling agent that answers questions about clinical trials by querying the [ClinicalTrials.gov API](https://clinicaltrials.gov/data-api/api). The model decides which tools to call and in what order — the sequence is not scripted.

## What it does

Ask a question in plain language:

```bash
python agent.py "What are the eligibility criteria for recruiting CKD trials?"
```

The agent searches for matching trials, then pulls eligibility criteria for the relevant ones, then answers. A question like "find phase 3 recruiting trials for type 2 diabetes" resolves in a single search call instead. Nothing in the code decides this — the model picks the tools and the order from the question.

## How it works

The loop in `agent.py` is the whole agent:

1. Send the conversation and the tool definitions to the model
2. If the model returns `stop_reason == "tool_use"`, run whichever tools it named
3. Append the results to the conversation
4. Repeat until the model answers without requesting a tool, or the turn cap is hit

Tool results go back as a user message, which is what lets the model chain calls — search first, then look up details on an NCT ID it only learned about from the search result.

## Tools

| Tool | Purpose |
| --- | --- |
| `search_trials` | Search by condition, with optional phase and recruitment-status filters |
| `get_trial_details` | Enrollment, sponsor, conditions and summary for one NCT ID |
| `summarize_eligibility` | Eligibility criteria, age range and sex for one NCT ID |

Each tool trims the API response before returning it. ClinicalTrials.gov records run to thousands of tokens; the tools return only the fields the model needs, since everything returned is paid for on the next request.

## Design notes

**Turn cap.** `MAX_TURNS = 5` bounds the loop so a confused model can't spin indefinitely.

**Truncation.** Trial summaries are cut at 800 characters and eligibility criteria at 1,500 — long enough to answer from, short enough to keep requests cheap.

**Error handling.** Tool exceptions are caught and returned to the model as `{"error": ...}` rather than crashing the loop, so the model can recover: retry with different arguments, or tell the user it failed.

**Model choice.** Claude Haiku. Tool selection over three well-described tools doesn't need a larger model, and a full run costs a fraction of a cent.

## Setup

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

Create a `.env` file:

```
ANTHROPIC_API_KEY=your-key-here
```

Then:

```bash
python agent.py "your question"
```

No key is needed for ClinicalTrials.gov — that API is public.

## Example runs

See `example1.txt` and `example2.txt` for full traces, including the `[tool]` lines showing which tools fired with which arguments.

## Limitations

- Results are capped at what one search returns; the agent does not paginate, though it flags when the result set is likely incomplete.
- Phase filtering only applies to interventional trials. Observational studies have no phase and come back with an empty `phases` field.
- Eligibility criteria are free text and truncated, so summaries can miss criteria appearing late in a long list.
- Nothing here is medical advice or a substitute for reading the trial record.

## Files

```
agent.py          # tool definitions and the agent loop
tools.py          # the three ClinicalTrials.gov functions
requirements.txt
example1.txt      # eligibility question, multi-tool trace
example2.txt      # phase-filtered search, single-tool trace
```
