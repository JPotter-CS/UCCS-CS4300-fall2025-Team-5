#!/usr/bin/env python3
import argparse, os, json, textwrap
from openai import OpenAI

parser = argparse.ArgumentParser()
parser.add_argument("--repo", required=True)
parser.add_argument("--pr", required=True)
parser.add_argument("--base", required=True)
parser.add_argument("--head", required=True)
parser.add_argument("--diff-file", required=True)
args = parser.parse_args()

with open(args.diff_file, "r", encoding="utf-8", errors="ignore") as f:
    diff = f.read()

# Guardrails prompt: short, actionable, reproducible
instructions = textwrap.dedent(f"""
You are a senior reviewer. Review ONLY the provided Git diff for quality, security, performance, and style.
Output a concise PR comment with:
- Overall summary (max 6 lines)
- Blocking issues (numbered, each with file:line, the risk, and a minimal fix)
- Nice-to-have suggestions (short list)
- Security notes (if any)
- Tests to add/adjust
Do not invent files or lines that are not in the diff. If the diff is too small, say so briefly.
Repository: {args.repo}, PR #{args.pr}, base={args.base}, head={args.head}.
""").strip()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# Responses API is the current recommendation for programmatic usage.
# Choose a strong model for code review. (You can swap "gpt-5" for another supported coding model.)
resp = client.responses.create(
    model="gpt-5",
    instructions=instructions,
    input=[{"role": "user", "content": f"Here is the Git diff:\n\n{diff}"}],
    temperature=0.2,
)

# Extract plain text
text = resp.output_text
print(text)
