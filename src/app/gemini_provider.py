"""Google Gemini provider for AI-powered job ranking.

Provides a wrapper for `google-generativeai` package.
"""

import json
import os
import time
import traceback
from typing import Any, Dict

try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False

# Support either the newer `google.generativeai` package or the older
# `google.genai` package (legacy). Try to import both and prefer the
# one that's available.
genai = None
genai_name = None
try:
    # try legacy path used in your old repo: `from google import genai`
    from google import genai as _genai  # type: ignore

    genai = _genai
    genai_name = "google.genai"
except Exception:
    try:
        import google.generativeai as _genai2  # type: ignore

        genai = _genai2
        genai_name = "google.generativeai"
    except Exception:
        genai = None
        genai_name = None


class GeminiProvider:
    """Minimal Gemini provider wrapper.

    Usage:
      - Install: `pip install "job-lead-starter[gemini]"`
      - Set `GOOGLE_API_KEY` environment variable
    """

    def __init__(self, api_key: str | None = None, model: str | None = None, request_timeout: int = 90):
        """Initialize Gemini provider.

        Args:
            api_key: Google API key for Gemini (falls back to env vars)
            model: Model name to use (default: gemini-2.5-flash-preview-09-2025)
            request_timeout: Request timeout in seconds (default: 90)
        """
        # Accept either GEMINI_API_KEY (preferred) or GOOGLE_API_KEY for backward compatibility
        self.api_key = api_key or os.getenv(
            "GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise RuntimeError(
                "GOOGLE_API_KEY not set; Gemini provider requires a key")
        if genai is None:
            raise RuntimeError(
                "google-generativeai package not installed; install optional 'gemini' extras")

        # Some SDK variants provide a module-level `configure`; call it only if present.
        try:
            if hasattr(genai, "configure"):
                genai.configure(api_key=self.api_key)
        except Exception:
            # Non-fatal: some SDKs may not need configure or may error here;
            # fallback to passing the key directly to client constructors.
            pass
        # Default to a modern model that supports google_search tool; allow overriding
        self.model = model or "gemini-2.5-flash-preview-09-2025"
        self.request_timeout = request_timeout

    def evaluate(self, job: Dict[str, Any], resume_text: str) -> Dict[str, Any]:
        """Evaluate a job using the Gemini client.

        Returns a dict with `score` (0-100) and `reasoning`.
        """
        prompt = (
            "You are an expert career advisor evaluating job fit for a candidate.\n\n"
            "Analyze how well this job matches the candidate's profile based on:\n"
            "1. REQUIRED SKILLS MATCH (40 points): How many required skills does the candidate have?\n"
            "2. EXPERIENCE LEVEL (25 points): Does the seniority level match (junior/mid/senior)?\n"
            "3. DOMAIN KNOWLEDGE (20 points): Relevant industry/domain experience?\n"
            "4. ROLE FIT (15 points): Does the role align with career trajectory?\n\n"
            f"CANDIDATE RESUME:\n{resume_text}\n\n"
            f"JOB POSTING:\n"
            f"Title: {job.get('title', '')}\n"
            f"Company: {job.get('company', '')}\n"
            f"Location: {job.get('location', '')}\n"
            f"Description: {job.get('description', job.get('summary', ''))}\n\n"
            "Provide a score (0-100) and detailed reasoning explaining:\n"
            "- Which key skills match (list 3-5 specific skills)\n"
            "- Experience level alignment\n"
            "- Any significant gaps or mismatches\n\n"
            'Return ONLY this JSON: {"score": <0-100>, "reasoning": "<detailed explanation>"}'
        )

        try:
            # Try google.genai Client first (newer SDK)
            if genai_name == "google.genai" and hasattr(genai, "Client"):
                client = genai.Client(api_key=self.api_key)
                resp = client.models.generate_content(
                    model=self.model, contents=prompt)
                # Extract text from response
                text = ""
                try:
                    if hasattr(resp, "candidates") and getattr(resp, "candidates"):
                        cand = getattr(resp, "candidates")[0]
                        if hasattr(cand, "content") and hasattr(cand.content, "parts") and cand.content.parts:
                            text = getattr(cand.content.parts[0], "text", "")
                        else:
                            text = str(cand)
                    elif hasattr(resp, "text"):
                        text = getattr(resp, "text")
                    else:
                        text = str(resp)
                except Exception:
                    text = str(resp)
            # Try google.generativeai.GenerativeModel (older SDK)
            elif genai_name == "google.generativeai" and hasattr(genai, "GenerativeModel"):
                try:
                    if hasattr(genai, "configure"):
                        genai.configure(api_key=self.api_key)
                except Exception:
                    # Safe to ignore configuration errors - model can be used without explicit configuration
                    pass
                model = genai.GenerativeModel(self.model)
                resp = model.generate_content(prompt)
                text = resp.text if hasattr(resp, "text") else str(resp)
            else:
                # Fallback for google.generativeai chat pattern
                if hasattr(genai, "chat") and hasattr(genai.chat, "create"):
                    try:
                        if hasattr(genai, "configure"):
                            genai.configure(api_key=self.api_key)
                    except Exception:
                        pass
                    out = genai.chat.create(model=self.model, messages=[
                                            {"role": "user", "content": prompt}])
                    text = ""
                    if hasattr(out, "candidates") and out.candidates:
                        text = out.candidates[0].content
                    elif hasattr(out, "message"):
                        text = getattr(out, "message").get("content", "")
                    else:
                        text = str(out)
                else:
                    return {"score": 50, "reasoning": "No supported call pattern for evaluation."}

            # Attempt to extract JSON substring
            import json

            start = text.find("{")
            end = text.rfind("}")
            if start != -1 and end != -1 and end > start:
                try:
                    payload = json.loads(text[start: end + 1])
                    return {"score": int(payload.get("score", 50)), "reasoning": payload.get("reasoning", "")}
                except Exception:
                    pass
        except Exception:
            pass
        return {"score": 50, "reasoning": "Could not parse Gemini response; ensure API key and model are correct."}

    def rank_jobs_batch(self, jobs: list[Dict[str, Any]], resume_text: str, top_n: int = 10) -> list[Dict[str, Any]]:
        """Rank multiple jobs in a single API call and return top N with scores.

        This is much faster than calling evaluate() for each job individually.
        Args:
            jobs: List of job dicts with title, company, location, summary/description
            resume_text: Candidate's resume text
            top_n: Number of top jobs to return

        Returns:
            List of top N jobs with added 'score' and 'reasoning' fields, sorted by score descending
        """
        if not jobs:
            return []

        # Limit to reasonable batch size (Gemini has token limits)
        max_batch = 50
        if len(jobs) > max_batch:
            jobs = jobs[:max_batch]

        # Build prompt with all jobs
        jobs_text = ""
        for i, job in enumerate(jobs, 1):
            jobs_text += f"\n{i}. {job.get('title', 'Unknown')} at {job.get('company', 'Unknown')}\n"
            jobs_text += f"   Location: {job.get('location', 'Unknown')}\n"
            desc = job.get("summary", job.get("description", ""))[:300]
            jobs_text += f"   Description: {desc}...\n"

        prompt = (
            f"You are an expert career advisor. Rank these {len(jobs)} jobs for this candidate based on:\n\n"
            "EVALUATION CRITERIA (total 100 points):\n"
            "1. Required Skills Match (40 pts): Technical skills, tools, languages\n"
            "2. Experience Level Fit (25 pts): Junior/Mid/Senior alignment\n"
            "3. Domain/Industry Match (20 pts): Relevant sector experience\n"
            "4. Role Alignment (15 pts): Career growth and trajectory fit\n\n"
            f"CANDIDATE RESUME:\n{resume_text[:3000]}\n\n"
            f"JOBS TO RANK:{jobs_text}\n\n"
            f"Return the top {min(top_n, len(jobs))} jobs as a JSON array. For each job, explain:\n"
            "- Specific matching skills (name 3-5)\\n"
            "- Experience level match\\n"
            "- Why this job ranks where it does\\n\\n"
            'Format: [{{"index": 1, "score": 85, "reasoning": "Strong match: '
            'Python, AWS, Docker. Senior level aligns. Missing: Kubernetes"}}, ...]\\n'
            "Return ONLY the JSON array, nothing else."
        )

        try:
            # Use same API pattern as evaluate
            text = ""
            if genai_name == "google.genai" and hasattr(genai, "Client"):
                client = genai.Client(api_key=self.api_key)
                resp = client.models.generate_content(
                    model=self.model, contents=prompt)
                if hasattr(resp, "text"):
                    text = resp.text
                elif hasattr(resp, "candidates") and resp.candidates:
                    cand = resp.candidates[0]
                    if hasattr(cand.content, "parts") and cand.content.parts:
                        text = cand.content.parts[0].text
            elif genai_name == "google.generativeai" and hasattr(genai, "GenerativeModel"):
                if hasattr(genai, "configure"):
                    genai.configure(api_key=self.api_key)
                model = genai.GenerativeModel(self.model)
                resp = model.generate_content(prompt)
                text = resp.text if hasattr(resp, "text") else str(resp)
            else:
                # Fallback - return jobs with default scores
                for job in jobs[:top_n]:
                    job["score"] = 50
                    job["reasoning"] = "Batch ranking unavailable"
                return jobs[:top_n]

            # Parse JSON response
            import json

            # Find JSON array
            start = text.find("[")
            end = text.rfind("]")
            if start != -1 and end != -1 and end > start:
                rankings = json.loads(text[start: end + 1])

                # Apply rankings to jobs
                ranked_jobs = []
                for ranking in rankings[:top_n]:
                    # Convert 1-based to 0-based
                    idx = ranking.get("index", 0) - 1
                    if 0 <= idx < len(jobs):
                        job = jobs[idx].copy()
                        job["score"] = int(ranking.get("score", 50))
                        job["reasoning"] = ranking.get("reasoning", "")
                        ranked_jobs.append(job)

                # Sort by score descending
                ranked_jobs.sort(key=lambda x: x.get("score", 0), reverse=True)
                return ranked_jobs[:top_n]

        except Exception as e:
            error_msg = str(e)
            print(f"Batch ranking failed: {error_msg}")
            raise

    def generate_job_leads(
        self, query: str, resume_text: str, count: int = 5, model: str | None = None, verbose: bool = False
    ) -> list[Dict[str, Any]]:
        """Generate job leads using Gemini and attempt to return a list of job dicts.

        The method asks the model to return a JSON array matching a simple schema:
        [{"title":..., "company":..., "location":..., "summary":..., "link":...}, ...]
        """
        prompt = (
            f"Use the google_search tool to find {count} job postings for: {query}\n\n"
            "Requirements:\n"
            "- Find specific job postings with direct links (not general career pages)\n"
            "- Each job should have a unique URL, preferably with a job ID\n"
            "- Avoid linking to homepage or /careers pages without a specific job\n\n"
            f"Return a JSON array with {count} jobs in this format:\n"
            '[{"title": "job title", "company": "company", "location": "city, state", '
            '"summary": "description", "link": "https://direct-job-url"}]\n\n'
            f"Context about candidate:\n{resume_text[:1000]}\n\n"
            "Return ONLY the JSON array."
        )

        try:
            # Allow overriding the model per-call
            use_model = model or self.model
            if verbose:
                print(
                    f"gemini_provider: entering generate_job_leads (model={use_model})")
                try:
                    print("gemini_provider: detected genai_name=", genai_name)
                    print("gemini_provider: genai attributes preview:",
                          dir(genai)[:80])
                    print("gemini_provider: has Client?",
                          hasattr(genai, "Client"))
                    print("gemini_provider: has chat?", hasattr(genai, "chat"))
                    chat_obj = getattr(genai, "chat", None)
                    print(
                        "gemini_provider: chat.create exists?",
                        hasattr(
                            chat_obj, "create") if chat_obj is not None else False,
                    )
                    # Also write a full dir() and repr() to a timestamped file for deeper inspection
                    try:
                        ts = int(time.time())
                        os.makedirs("logs", exist_ok=True)
                        fname_dir = f"logs/gemini_dir_{ts}.txt"
                        try:
                            with open(fname_dir, "w", encoding="utf-8") as fh:
                                fh.write(f"genai_name: {genai_name}\n\n")
                                try:
                                    fh.write("repr(genai):\n")
                                    fh.write(repr(genai))
                                except Exception as _e:
                                    fh.write(f"repr(genai) failed: {_e}\n")
                                fh.write("\n\nfull dir(genai):\n")
                                try:
                                    fh.write("\n".join(sorted(dir(genai))))
                                except Exception:
                                    fh.write("<failed to list dir(genai)>\n")
                            print(
                                f"gemini_provider: wrote genai dir/repr to {fname_dir}")
                        except Exception as _e:
                            print(
                                "gemini_provider: failed to write genai dir file:", _e)
                    except Exception:
                        pass
                except Exception:
                    pass

            # If the legacy client is available (your working app used `genai.Client`), prefer that
            if genai is None:
                return []

            # Case A: `google.genai` style with Client and models.generate_content
            if hasattr(genai, "Client"):
                try:
                    # Configure httpx client with timeout
                    import httpx
                    http_options = httpx.Timeout(timeout=self.request_timeout)
                    client = genai.Client(api_key=self.api_key, http_options={
                                          "timeout": http_options})
                    # Note: google_search tool disabled due to MALFORMED_FUNCTION_CALL errors
                    # and redirect URLs instead of direct links. Simple prompting works better.
                    if verbose:
                        print(
                            f"gemini_provider: calling generate_content on {use_model} (timeout={self.request_timeout}s)")
                    try:
                        resp = client.models.generate_content(
                            model=use_model, contents=prompt)
                        if verbose:
                            print(
                                f"gemini_provider: response type: {type(resp)}, repr: {repr(resp)[:200]}")
                    except Exception as api_err:
                        print(f"ERROR calling Gemini API: {api_err}")
                        traceback.print_exc()
                        return []

                    # Robustly extract text from various response shapes returned by the
                    # legacy client. The response may contain `candidates` with
                    # `.content.parts[*].text` or a `text` attribute or a `message`.
                    text = ""
                    raw_response = str(resp)
                    try:
                        if hasattr(resp, "candidates") and getattr(resp, "candidates"):
                            cand = getattr(resp, "candidates")[0]
                            # candidate.content.parts[0].text is common
                            if hasattr(cand, "content"):
                                cont = getattr(cand, "content")
                                if hasattr(cont, "parts") and len(getattr(cont, "parts")) > 0:
                                    p0 = getattr(cont, "parts")[0]
                                    text = getattr(p0, "text", str(p0))
                                else:
                                    text = str(cont)
                            else:
                                text = str(cand)
                        elif hasattr(resp, "message"):
                            m = getattr(resp, "message")
                            try:
                                text = m.get("content", str(m))
                            except Exception:
                                text = str(m)
                        elif hasattr(resp, "text"):
                            text = getattr(resp, "text")
                        else:
                            text = str(resp)
                        # prefer extracted text for raw_response when available
                        if text:
                            raw_response = text
                    except Exception:
                        # keep best-effort raw_response
                        pass

                    # If no text was extracted, try the streaming API variant.
                    if not text:
                        try:
                            # generate_content_stream yields chunks we can concat
                            stream_text = ""
                            for chunk in client.models.generate_content_stream(model=use_model, contents=prompt):
                                try:
                                    # chunk may have .candidates or .text
                                    if hasattr(chunk, "candidates") and getattr(chunk, "candidates"):
                                        cand = getattr(chunk, "candidates")[0]
                                        if (
                                            hasattr(cand, "content")
                                            and hasattr(cand.content, "parts")
                                            and cand.content.parts
                                        ):
                                            part_text = getattr(
                                                cand.content.parts[0], "text", "")
                                            stream_text += part_text
                                        else:
                                            stream_text += str(cand)
                                    elif hasattr(chunk, "text") and getattr(chunk, "text"):
                                        stream_text += getattr(chunk, "text")
                                    else:
                                        stream_text += str(chunk)
                                except Exception:
                                    stream_text += str(chunk)

                            if stream_text:
                                text = stream_text
                                raw_response = stream_text
                        except Exception:
                            # streaming not available or failed; continue
                            pass
                    if verbose:
                        ts = int(time.time())
                        os.makedirs("logs", exist_ok=True)
                        fname = f"logs/last_gemini_response_{ts}.txt"
                        print(
                            "gemini_provider: used legacy genai.Client; model=", use_model)
                        # print a short preview to the console
                        try:
                            preview = raw_response[:4000] + "\n...\n" if len(
                                raw_response) > 4000 else raw_response
                        except Exception:
                            preview = repr(raw_response)[:4000]
                        print("gemini_provider: raw response preview:\n", preview)
                        # Print resp object diagnostics
                        try:
                            print("gemini_provider: resp type:", type(resp))
                            try:
                                print("gemini_provider: resp dir preview:",
                                      dir(resp)[:50])
                            except Exception:
                                pass
                            # Try to access common attributes
                            for attr in ("candidates", "message", "text", "content"):
                                try:
                                    if hasattr(resp, attr):
                                        val = getattr(resp, attr)
                                        print(
                                            f"gemini_provider: resp.{attr} -> type={type(val)} repr_preview=",
                                            repr(val)[:200],
                                        )
                                    else:
                                        print(
                                            f"gemini_provider: resp has no attribute {attr}")
                                except Exception:
                                    traceback.print_exc()
                        except Exception:
                            traceback.print_exc()
                        # Save full repr to file for offline inspection
                        try:
                            with open(fname, "w", encoding="utf-8") as fh:
                                fh.write(repr(resp))
                            print(
                                f"gemini_provider: wrote raw repr to {fname}")
                        except Exception as e:
                            print(
                                "gemini_provider: failed to write raw repr file:", e)
                except Exception:
                    text = ""

            # Case B: `google.generativeai` chat-style API
            elif hasattr(genai, "chat") and hasattr(genai.chat, "create"):
                out = genai.chat.create(model=self.model, messages=[
                                        {"role": "user", "content": prompt}])
                text = ""
                if hasattr(out, "candidates") and out.candidates:
                    text = out.candidates[0].content
                elif hasattr(out, "message"):
                    text = getattr(out, "message").get("content", "")
                else:
                    text = str(out)
                raw_response = str(out)
                if verbose:
                    import os

                    ts = int(time.time())
                    os.makedirs("logs", exist_ok=True)
                    fname = f"logs/gemini_response_{ts}.txt"
                    os.makedirs("logs", exist_ok=True)
                    fname = f"logs/gemini_response_{ts}.txt"
                    print("gemini_provider: used chat.create; model=", use_model)
                    try:
                        preview = raw_response[:4000] + "\n...\n" if len(
                            raw_response) > 4000 else raw_response
                    except Exception:
                        preview = repr(raw_response)[:4000]
                    print("gemini_provider: raw response preview:\n", preview)
                    try:
                        print("gemini_provider: out type:", type(out))
                        try:
                            print("gemini_provider: out dir preview:",
                                  dir(out)[:50])
                        except Exception:
                            pass
                        # Try to print candidate/text structure
                        try:
                            if hasattr(out, "candidates"):
                                print("gemini_provider: out.candidates type:", type(
                                    out.candidates))
                                try:
                                    print("gemini_provider: out.candidates[0] repr:", repr(
                                        out.candidates[0])[:400])
                                except Exception:
                                    pass
                            if hasattr(out, "message"):
                                print("gemini_provider: out.message repr:",
                                      repr(getattr(out, "message"))[:400])
                        except Exception:
                            traceback.print_exc()
                    except Exception:
                        traceback.print_exc()
                    try:
                        with open(fname, "w", encoding="utf-8") as fh:
                            fh.write(repr(out))
                        print(f"gemini_provider: wrote raw repr to {fname}")
                    except Exception as e:
                        print("gemini_provider: failed to write raw repr file:", e)

            # Case C: `google.generativeai` with GenerativeModel and google_search tool
            elif genai_name == "google.generativeai" and hasattr(genai, "GenerativeModel"):
                try:
                    if verbose:
                        print(
                            "gemini_provider: using google.generativeai.GenerativeModel with google_search")

                    # Configure google_search tool as a dictionary
                    # Note: google.generativeai SDK doesn't support google_search tool yet
                    # It only supports 'code_execution' as a string tool
                    # We'll call without tools and rely on model's knowledge
                    model = genai.GenerativeModel(use_model)

                    if verbose:
                        print(
                            "gemini_provider: created GenerativeModel (note: google_search not available in this SDK)"
                        )

                    response = model.generate_content(prompt)
                    text = response.text if hasattr(
                        response, "text") else str(response)
                    raw_response = str(response)

                    if verbose:
                        ts = int(time.time())
                        os.makedirs("logs", exist_ok=True)
                        fname = f"logs/generativemodel_response_{ts}.txt"
                        print(
                            "gemini_provider: used GenerativeModel; model=", use_model)
                        try:
                            preview = raw_response[:4000] + "\n...\n" if len(
                                raw_response) > 4000 else raw_response
                        except Exception:
                            preview = repr(raw_response)[:4000]
                        print("gemini_provider: raw response preview:\n", preview)
                        try:
                            with open(fname, "w", encoding="utf-8") as fh:
                                fh.write(repr(response))
                            print(
                                f"gemini_provider: wrote raw repr to {fname}")
                        except Exception as e:
                            print(
                                "gemini_provider: failed to write raw repr file:", e)

                except Exception as gm_err:
                    if verbose:
                        print(
                            f"gemini_provider: GenerativeModel call failed: {gm_err}")

                        traceback.print_exc()
                    text = ""

            else:
                return []

            # Clean out markdown fences
            if text.startswith("```json") or text.startswith("```"):
                # reuse the same cleaning heuristics as the legacy app
                text = text.strip()
                if text.startswith("```"):
                    start = text.find("\n")
                    if start != -1:
                        text = text[start:].strip()
                    else:
                        text = text[3:].strip()
                if text.endswith("```"):
                    text = text[:-3].strip()

            # Attempt to find JSON array in the text
            import json

            start = text.find("[")
            end = text.rfind("]")
            jobs = []
            if start != -1 and end != -1 and end > start:
                try:
                    payload = json.loads(text[start: end + 1])
                    if isinstance(payload, list):
                        jobs = payload
                except Exception:
                    jobs = []

            # Fallback: if tool-enabled call returned 0 jobs, retry without tools
            if not jobs and hasattr(genai, "Client"):
                if verbose:
                    print(
                        "gemini_provider: tool call returned 0 jobs; retrying without tools")
                try:
                    simple_prompt = (
                        "Generate a JSON array of job postings based on this profile and query.\n"
                        f"Return EXACTLY {count} job objects with keys: title, company, location, summary, link.\n"
                        f"CANDIDATE PROFILE:\n{resume_text}\n\n"
                        f"QUERY:\n{query}\n\n"
                        "Return ONLY the JSON array, no markdown or other text."
                    )
                    client = genai.Client(api_key=self.api_key)
                    resp = client.models.generate_content(
                        model=use_model, contents=simple_prompt)
                    text2 = getattr(resp, "text", str(resp))
                    start = text2.find("[")
                    end = text2.rfind("]")
                    if start != -1 and end != -1 and end > start:
                        try:
                            payload = json.loads(text2[start: end + 1])
                            if isinstance(payload, list):
                                jobs = payload
                        except Exception:
                            pass
                except Exception as fallback_err:
                    if verbose:
                        print(
                            f"gemini_provider: fallback failed: {fallback_err}")

            return jobs
        except Exception as e:
            if verbose:
                print("gemini_provider: exception in generate_job_leads:", e)
                traceback.print_exc()
            # On any failure return empty list; caller will fallback
            return []

        return []


def simple_gemini_query(
    prompt: str, api_key: str | None = None, model: str | None = None, verbose: bool = False
) -> str:
    """Run a simple prompt against the available Gemini SDK and return a raw string response.

    This helper attempts multiple SDK call shapes:
      1. Legacy `google.genai` client: `Client(...).models.generate_content(...)`
      2. Newer `google.generativeai` chat API: `chat.create(...)`

    Returns the raw text (or repr) of the SDK response. Raises RuntimeError if no SDK is available.
    """
    key = api_key or os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    if not key:
        raise RuntimeError(
            "No GEMINI_API_KEY/GOOGLE_API_KEY found in environment; cannot call Gemini")

    if genai is None:
        raise RuntimeError(
            "No supported Gemini SDK (google.genai or google.generativeai) is installed")

    use_model = model or os.getenv(
        "GEMINI_MODEL") or "gemini-2.5-flash-preview-09-2025"

    # Try legacy client call first if present
    if hasattr(genai, "Client"):
        try:
            client = genai.Client(api_key=key)
            # best-effort: call with or without types/config
            try:
                resp = client.models.generate_content(
                    model=use_model, contents=prompt)
            except Exception:
                # fallback with minimal args
                resp = client.models.generate_content(
                    model=use_model, contents=prompt)
            # Try to extract text attribute
            text = getattr(resp, "text", None)
            if text is None:
                return str(resp)
            return text
        except Exception as e:
            if verbose:
                print("simple_gemini_query: legacy client call failed:", e)
            # fall through to other call shapes

    # Try chat-style API if available
    if hasattr(genai, "chat") and hasattr(genai.chat, "create"):
        try:
            # configure if supported
            try:
                if hasattr(genai, "configure"):
                    genai.configure(api_key=key)
            except Exception:
                pass
            out = genai.chat.create(model=use_model, messages=[
                                    {"role": "user", "content": prompt}])
            # best-effort to extract text
            if hasattr(out, "candidates") and out.candidates:
                return out.candidates[0].content
            if hasattr(out, "message"):
                m = getattr(out, "message")
                # message may be dict-like
                try:
                    return m.get("content", str(m))
                except Exception:
                    return str(m)
            return str(out)
        except Exception as e:
            if verbose:
                print("simple_gemini_query: chat.create call failed:", e)

    # Try additional possible entrypoints that some genai packages expose
    tried = []
    # module-level generate_text / generate
    for fn_name in ("generate_text", "generate", "generate_content"):
        if hasattr(genai, fn_name):
            try:
                tried.append(fn_name)
                fn = getattr(genai, fn_name)
                # try common kwarg names
                for kwargs in (
                    {"model": use_model, "prompt": prompt},
                    {"model": use_model, "contents": prompt},
                    {"model": use_model, "contents": [prompt]},
                    {"prompt": prompt},
                ):
                    try:
                        resp = fn(**kwargs)
                        if verbose:
                            print(
                                f"simple_gemini_query: used genai.{fn_name} with kwargs={kwargs}")
                        text = getattr(resp, "text", None) or str(resp)
                        return text
                    except Exception as e:
                        if verbose:
                            print(
                                f"simple_gemini_query: attempt genai.{fn_name} with {kwargs} failed: {e}")
            except Exception:
                pass

    # Try genai.models.generate or genai.models.generate_content
    models_obj = getattr(genai, "models", None)
    if models_obj is not None:
        for attr in ("generate_content", "generate", "generate_text"):
            if hasattr(models_obj, attr):
                try:
                    fn = getattr(models_obj, attr)
                    resp = fn(model=use_model, contents=prompt)
                    if verbose:
                        print(f"simple_gemini_query: used genai.models.{attr}")
                    text = getattr(resp, "text", None) or str(resp)
                    return text
                except Exception as e:
                    if verbose:
                        print(
                            f"simple_gemini_query: genai.models.{attr} failed: {e}")

    # Try get_model(...).generate style
    if hasattr(genai, "get_model"):
        try:
            m = genai.get_model(use_model)
            if hasattr(m, "generate"):
                try:
                    resp = m.generate(contents=prompt)
                    if verbose:
                        print(
                            "simple_gemini_query: used genai.get_model(...).generate")
                    text = getattr(resp, "text", None) or str(resp)
                    return text
                except Exception as e:
                    if verbose:
                        print("simple_gemini_query: model.generate failed:", e)
        except Exception:
            pass

    # If nothing worked, raise for the caller to inspect environment
    raise RuntimeError(
        f"Gemini SDK present but no supported call pattern succeeded. Tried: {tried}")
