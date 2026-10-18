import json
import os

from anthropic import Anthropic
from dotenv import load_dotenv

from tools import search_trials, get_trial_details, summarize_eligibility

load_dotenv()
client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])

MODEL = "claude-haiku-5-5"
MAX_TURNS = 5

TOOLS = [
    {
        "name": "search_trials",
        "description": "Search clinical trials by condition. Returns NCT IDs, titles, status and phases.",
        "input_schema": {
            "type": "object",
            "properties": {
                "condition": {"type": "string"},
                "phase": {"type": "string", "description": "e.g. PHASE3"},
                "status": {"type": "string", "description": "e.g. RECRUITING, COMPLETED"},
                "max_results": {"type": "integer"},
            },
            "required": ["condition"],
        },
    },
    {
        "name": "get_trial_details",
        "description": "Full details for one trial: enrollment, sponsor, summary, conditions.",
        "input_schema": {
            "type": "object",
            "properties": {"nct_id": {"type": "string"}},
            "required": ["nct_id"],
        },
    },
    {
        "name": "summarize_eligibility",
        "description": "Eligibility criteria, age range and sex for one trial.",
        "input_schema": {
            "type": "object",
            "properties": {"nct_id": {"type": "string"}},
            "required": ["nct_id"],
        },
    },
]

REGISTRY = {
    "search_trials": search_trials,
    "get_trial_details": get_trial_details,
    "summarize_eligibility": summarize_eligibility,
}


def run(question):
    messages = [{"role": "user", "content": question}]

    for turn in range(MAX_TURNS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=2048,
            tools=TOOLS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            return "".join(b.text for b in response.content if b.type == "text")

        messages.append({"role": "assistant", "content": response.content})

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            print(f"  [tool] {block.name}({block.input})")
            try:
                output = REGISTRY[block.name](**block.input)
            except Exception as exc:
                output = {"error": str(exc)}
            results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": json.dumps(output),
            })

        messages.append({"role": "user", "content": results})

    return "Hit the turn limit without finishing."


if __name__ == "__main__":
    import sys
    print(run(" ".join(sys.argv[1:]) or "What phase 3 trials are recruiting for chronic kidney disease?"))