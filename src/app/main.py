"""Minimal starter CLI linking job search and evaluation providers."""

import argparse
import os
import json
from typing import Dict

from dotenv import load_dotenv

load_dotenv()

try:
    from .gemini_provider import GeminiProvider
except Exception:
    GeminiProvider = None  # optional


def fetch_jobs(query: str):
    """Minimal job fetcher — replace with real integration.

    For now this returns a small hard-coded list similar to previous demos.
    """
    sample = [
        {
            "id": "1",
            "title": "Senior Python Developer",
            "company": "TechCorp",
            "location": "Remote",
            "description": "Python, Django, Docker, AWS",
        },
        {
            "id": "2",
            "title": "DevOps Engineer",
            "company": "CloudServices",
            "location": "Austin, TX",
            "description": "Kubernetes, Terraform, AWS, CI/CD",
        },
        {
            "id": "3",
            "title": "ML Engineer",
            "company": "AI Systems",
            "location": "New York, NY",
            "description": "Python, TensorFlow, LLM experience",
        },
    ]
    q = query.lower()
    return [j for j in sample if q in j["title"].lower() or q in j["description"].lower()]


def format_resume(skills, roles, locations, text=None):
    parts = []
    if text:
        parts.append(text)
    if skills:
        parts.append("Skills: " + ", ".join(skills))
    if roles:
        parts.append("Desired roles: " + ", ".join(roles))
    if locations:
        parts.append("Desired locations: " + ", ".join(locations))
    return "\n".join(parts)


def run_search(args):
    resume_text = format_resume(args.skills, args.roles, args.locations, args.resume)
    jobs = fetch_jobs(args.query)

    # Choose provider: Gemini if key present, else built-in template
    provider = None
    if args.provider == "gemini":
        if GeminiProvider is None:
            print("Gemini provider not installed. Install optional deps")
            return 1
        try:
            provider = GeminiProvider()
        except Exception as e:
            print("Gemini provider init error:", e)
            return 1

    # Fallback simple scoring using keyword counts
    results = []
    for job in jobs:
        if provider:
            out = provider.evaluate(job, resume_text)
            score = int(out.get("score", 50))
            reasoning = out.get("reasoning", "")
        else:
            # Basic scoring: count keyword overlap
            matches = sum(1 for s in args.skills if s.lower() in job["description"].lower())
            total = max(len(args.skills), 1)
            score = int((matches / total) * 100)
            reasoning = f"{matches} skill matches of {total}"

        results.append({"job": job, "score": score, "reasoning": reasoning})

    print(json.dumps({"query": args.query, "results": results}, indent=2))
    return 0


def build_parser():
    p = argparse.ArgumentParser(prog="job-starter")
    sub = p.add_subparsers(dest="cmd")

    sub_map = {}

    search = sub.add_parser("search")
    search.add_argument("--query", "-q", required=True)
    search.add_argument("--skills", "-s", nargs="*", default=["Python", "Docker"])
    search.add_argument("--roles", "-r", nargs="*", default=["Engineer"])
    search.add_argument("--locations", "-l", nargs="*", default=["Remote"])
    search.add_argument("--provider", "-p", choices=["mock", "gemini"], default="mock")
    search.add_argument("--resume", help="Optional free-text resume to include in evaluation", default=None)
    sub_map["search"] = search

    health = sub.add_parser("health")
    sub_map["health"] = health

    help_p = sub.add_parser("help", help="Show full help or help for a specific subcommand")
    help_p.add_argument("command", nargs="?", help="Command to show help for (default: full help)")
    sub_map["help"] = help_p

    # Add 'find' command to generate job leads
    find_p = sub.add_parser("find", help="Generate job leads (uses Gemini when available)")
    find_p.add_argument("--query", "-q", required=True, help="Query to search for")
    find_p.add_argument("--resume", help="Resume text or path to file; used for evaluation", default=None)
    find_p.add_argument("--count", "-n", type=int, default=5, help="Number of leads to request")
    find_p.add_argument("--model", "-m", help="Optional model name to request (overrides default)")
    find_p.add_argument("--evaluate", action="store_true", help="Score each job against resume (requires --resume)")
    find_p.add_argument("--verbose", "-v", action="store_true", help="Print raw AI response and debug info")
    find_p.add_argument("--save", "-o", help="Optional file path to save results (JSON); defaults to leads.json")
    sub_map["find"] = find_p

    probe_p = sub.add_parser("probe", help="Run a simple Gemini probe prompt and print raw response")
    probe_p.add_argument("--prompt", "-p", help="Prompt to send to Gemini", required=False)
    probe_p.add_argument("--model", "-m", help="Optional model name to request")
    probe_p.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    sub_map["probe"] = probe_p

    return p, sub_map


def main(argv=None):
    parser, sub_map = build_parser()
    args = parser.parse_args(argv)
    if args.cmd == "search":
        return run_search(args)
    elif args.cmd == "health":
        print("ok")
        return 0
    elif args.cmd == "help":
        cmd = getattr(args, "command", None)
        if cmd:
            sp = sub_map.get(cmd)
            if not sp:
                print(f"No such command: {cmd}")
                return 2
            sp.print_help()
            return 0
        print(parser.format_help())
        return 0
    elif args.cmd == "find":
        # lazy import to avoid optional deps at module import time
        from .job_finder import generate_job_leads, save_to_file

        # Handle resume: accept text or read from file
        resume_text = None
        if args.resume:
            if os.path.isfile(args.resume):
                with open(args.resume, "r", encoding="utf-8") as fh:
                    resume_text = fh.read()
            else:
                # Assume it's inline text
                resume_text = args.resume
        if not resume_text:
            # Default placeholder
            resume_text = "No resume provided."

        # Generate leads with optional evaluation
        evaluate = getattr(args, "evaluate", False)
        leads = generate_job_leads(
            args.query,
            resume_text,
            count=args.count,
            model=getattr(args, "model", None),
            verbose=getattr(args, "verbose", False),
            evaluate=evaluate,
        )

        import json

        print(json.dumps({"query": args.query, "leads": leads}, indent=2))

        # Save to file (default: leads.json)
        save_path = args.save or "leads.json"
        save_to_file(leads, save_path)
        return 0
    elif args.cmd == "probe":
        from .gemini_provider import simple_gemini_query

        prompt = (
            args.prompt
            or 'Return a JSON array with one example job: [{"title": "Test", "company": "X", "summary": "S", "url": "http://example.com"}]'
        )
        try:
            resp = simple_gemini_query(
                prompt, model=getattr(args, "model", None), verbose=getattr(args, "verbose", False)
            )
            print("--- RAW RESPONSE ---")
            print(resp)
            return 0
        except Exception as e:
            print("Probe failed:", e)
            return 2
    else:
        parser.print_help()
        return 0


if __name__ == "__main__":
    raise SystemExit(main())
