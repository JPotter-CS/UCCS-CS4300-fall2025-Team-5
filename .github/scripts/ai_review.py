#!/usr/bin/env python3
import argparse, os, textwrap
from openai import OpenAI

if not os.environ.get("OPENAI_API_KEY"):
    print("AI review skipped: OPENAI_API_KEY not set.")
    raise SystemExit(0)

p = argparse.ArgumentParser()
p.add_argument("--repo", required=True)
p.add_argument("--pr", required=True)
p.add_argument("--base", required=True)
p.add_argument("--head", required=True)
p.add_argument("--diff-file", required=True)
args = p.parse_args()

with open(args.diff_file, "r", encoding="utf-8", errors="ignore") as f:
    diff = f.read()

instructions = textwrap.dedent(f"""
You are a senior reviewer. Review ONLY this git diff for quality, security, performance, and style.
Output:
- Summary (≤6 lines)
- Blocking issues (file:line, risk, minimal fix)
- Suggestions
- Security notes
- Tests to add/adjust
Do not invent files/lines.
Repo {args.repo}, PR #{args.pr}, base={args.base}, head={args.head}.
""").strip()

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
resp = client.responses.create(
    model="gpt-5",
    instructions=instructions,
    input=[{"role":"user","content": f"Git diff:\n\n{diff}"}],
)
print(resp.output_text)
