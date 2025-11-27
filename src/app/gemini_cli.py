"""Simple CLI to query Gemini and (if available) use Google Search tool.

Usage:
  python -m app.gemini_cli --prompt "Find one recent remote Python job and return JSON" -m gemini-2.5-flash-preview-09-2025

The script prefers the legacy `google.genai` package when present and will
attempt the `google.generativeai` chat path as a fallback.
"""

import argparse
import os
import json
import sys


def main():
    p = argparse.ArgumentParser(description="Simple Gemini CLI with web-search tool support")
    p.add_argument("--prompt", "-p", required=True, help="Prompt to send to Gemini")
    p.add_argument(
        "--model", "-m", default=os.getenv("GEMINI_MODEL") or "gemini-2.5-flash-preview-09-2025", help="Model name"
    )
    p.add_argument("--key", "-k", default=None, help="Gemini API key (overrides GEMINI_API_KEY/GOOGLE_API_KEY)")
    p.add_argument("--raw-file", default=None, help="Write raw repr(response) to this file")
    p.add_argument(
        "--no-tool",
        action="store_true",
        help="Do not request use of the google_search tool (useful if key lacks tool access)",
    )
    args = p.parse_args()

    key = args.key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        print("No GEMINI_API_KEY/GOOGLE_API_KEY found in environment or --key; aborting", file=sys.stderr)
        sys.exit(2)

    genai = None
    genai_name = None
    # Try legacy package first
    try:
        from google import genai as _genai  # type: ignore

        genai = _genai
        genai_name = "google.genai"
    except Exception:
        try:
            import google.generativeai as _g2  # type: ignore

            genai = _g2
            genai_name = "google.generativeai"
        except Exception:
            genai = None
            genai_name = None

    if genai is None:
        print("No supported Gemini SDK installed (google.genai or google.generativeai)", file=sys.stderr)
        sys.exit(3)

    print(f"Using SDK: {genai_name}")

    # If legacy client exists, try to call client.models.generate_content with google_search tool enabled
    if genai_name == "google.genai" and hasattr(genai, "Client"):
        try:
            client = genai.Client(api_key=key)
            cfg = None
            types_mod = getattr(genai, "types", None)
            if not args.no_tool:
                if types_mod is not None:
                    try:
                        # Some server/tool combos reject `response_mime_type='application/json'` when tools are used.
                        # Omit the mime type and ask the model to return only JSON in the instruction.
                        cfg = types_mod.GenerateContentConfig(
                            system_instruction="Use the google_search tool and return a JSON array of results. Only return JSON.",
                            tools=[{"google_search": {}}],
                        )
                    except Exception:
                        cfg = None

            if cfg is not None:
                resp = client.models.generate_content(model=args.model, contents=args.prompt, config=cfg)
            else:
                resp = client.models.generate_content(model=args.model, contents=args.prompt)

            # Try to extract textual output from response (candidates -> content -> parts[0].text)
            text = None
            try:
                if hasattr(resp, "candidates") and getattr(resp, "candidates"):
                    cand = getattr(resp, "candidates")[0]
                    if hasattr(cand, "content"):
                        cont = getattr(cand, "content")
                        if hasattr(cont, "parts") and len(getattr(cont, "parts")) > 0:
                            text = getattr(cont, "parts")[0].text
                        else:
                            text = str(cont)
                elif hasattr(resp, "text"):
                    text = getattr(resp, "text")
            except Exception:
                text = None

            raw = repr(resp)
            if args.raw_file:
                try:
                    with open(args.raw_file, "w", encoding="utf-8") as fh:
                        fh.write(raw)
                    print(f"Wrote raw response repr to {args.raw_file}")
                except Exception as e:
                    print("Failed to write raw file:", e)

            if text:
                print("--- RAW TEXT OUTPUT ---")
                print(text)
                # If the model returned JSON, pretty-print it
                try:
                    parsed = json.loads(text)
                    print("--- PARSED JSON ---")
                    print(json.dumps(parsed, indent=2))
                except Exception:
                    pass
            else:
                print("No extractable text from response; raw repr below:\n")
                print(raw)

            return
        except Exception as e:
            print("Legacy client call failed:", e, file=sys.stderr)

    # Fallback: try chat.create pattern for google.generativeai
    if genai_name == "google.generativeai" and hasattr(genai, "chat") and hasattr(genai.chat, "create"):
        try:
            try:
                if hasattr(genai, "configure"):
                    genai.configure(api_key=key)
            except Exception:
                pass
            out = genai.chat.create(model=args.model, messages=[{"role": "user", "content": args.prompt}])
            raw = repr(out)
            if args.raw_file:
                try:
                    with open(args.raw_file, "w", encoding="utf-8") as fh:
                        fh.write(raw)
                    print(f"Wrote raw response repr to {args.raw_file}")
                except Exception as e:
                    print("Failed to write raw file:", e)

            # Extract text
            text = None
            try:
                if hasattr(out, "candidates") and out.candidates:
                    text = out.candidates[0].content
                elif hasattr(out, "message"):
                    text = getattr(out, "message").get("content", None)
            except Exception:
                text = None

            if text:
                print("--- RAW TEXT OUTPUT ---")
                print(text)
                try:
                    parsed = json.loads(text)
                    print("--- PARSED JSON ---")
                    print(json.dumps(parsed, indent=2))
                except Exception:
                    pass
            else:
                print("No extractable text; raw repr below:\n")
                print(raw)

            return
        except Exception as e:
            print("Chat.create fallback failed:", e, file=sys.stderr)

    print("No supported call pattern succeeded for installed SDK", file=sys.stderr)
    sys.exit(4)


if __name__ == "__main__":
    main()
