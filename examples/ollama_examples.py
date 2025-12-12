#!/usr/bin/env python3
"""
Example integrations of Ollama Code Assistant with job-lead-finder.
Demonstrates privacy-sensitive and batch operations using local LLMs.
"""

import json
import logging
import sys
from pathlib import Path

# Add scripts to path
sys.path.insert(0, str(Path(__file__).parent.parent / "scripts"))

from ollama_code_assistant import OllamaAssistant, recommend_model  # noqa: E402

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def example_resume_analysis():
    """
    Example: Analyze resume locally without sending to cloud.
    Privacy-sensitive operation ideal for local LLM.
    """
    logger.info("=== Resume Analysis (Privacy-Sensitive) ===")

    resume_path = Path("data/resume.txt")
    if not resume_path.exists():
        logger.warning(f"Resume not found at {resume_path}")
        return

    with open(resume_path, "r", encoding="utf-8") as f:
        resume_text = f.read()

    # Recommend best model for this task
    model = recommend_model("resume analysis", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    # Extract skills
    system_prompt = """You are a technical resume analyzer. Extract:
1. Programming languages and frameworks
2. Years of experience per technology
3. Key achievements
4. Certifications

Format as JSON:
{
  "skills": {"Python": "5+ years", "FastAPI": "2 years", ...},
  "achievements": ["..."],
  "certifications": ["..."]
}"""

    prompt = f"Analyze this resume:\n\n{resume_text[:4000]}"  # Limit for context

    result = assistant.query(prompt, system_prompt)

    logger.info("Resume Analysis Result:")
    print(result)

    return result


def example_job_description_batch_analysis():
    """
    Example: Batch analyze all job descriptions offline.
    High-volume operation without API costs.
    """
    logger.info("=== Batch Job Description Analysis ===")

    leads_path = Path("data/leads.json")
    if not leads_path.exists():
        logger.warning(f"Leads file not found at {leads_path}")
        return

    with open(leads_path, "r", encoding="utf-8") as f:
        leads = json.load(f)

    model = recommend_model("skill extraction", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    system_prompt = """Extract required technical skills from job description.
Return comma-separated list only. Example: Python, FastAPI, PostgreSQL, Docker"""

    analyzed_leads = []

    for idx, lead in enumerate(leads[:5], 1):  # Process first 5 for demo
        if "description" not in lead or not lead["description"]:
            continue

        logger.info(f"Analyzing job {idx}/{len(leads[:5])}: {lead.get('title', 'Unknown')}")

        prompt = f"Extract skills from:\n{lead['description'][:2000]}"

        skills_text = assistant.query(prompt, system_prompt)
        lead["extracted_skills"] = [s.strip() for s in skills_text.split(",")]

        analyzed_leads.append(lead)

    # Save results
    output_path = Path("data/leads_analyzed.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analyzed_leads, f, indent=2)

    logger.info(f"Saved analyzed leads to {output_path}")

    return analyzed_leads


def example_code_generation():
    """
    Example: Generate code for new feature using local LLM.
    Useful for boilerplate and repetitive code.
    """
    logger.info("=== Code Generation Example ===")

    model = recommend_model("code generation", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    system_prompt = """You are an expert Python developer. Generate clean, well-documented code
following these principles:
- Type hints for all parameters
- Google-style docstrings
- Error handling
- Logging
- Follow PEP 8

Return ONLY the code, no explanations."""

    prompt = """Create a Python class `JobMatcher` that:
1. Takes a resume dict and list of job dicts
2. Calculates match score (0-100) based on skill overlap
3. Returns top N matching jobs sorted by score
4. Uses dataclasses and type hints

Skills in resume/jobs are stored as lists of strings."""

    code = assistant.query(prompt, system_prompt)

    # Extract code from markdown if present
    if "```python" in code:
        code = code.split("```python")[1].split("```")[0].strip()
    elif "```" in code:
        code = code.split("```")[1].split("```")[0].strip()

    logger.info("Generated code:")
    print("\n" + code + "\n")

    # Save to file
    output_path = Path("src/app/job_matcher.py")
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(code)

    logger.info(f"Saved generated code to {output_path}")

    return code


def example_email_analysis():
    """
    Example: Analyze email content locally (privacy-sensitive).
    Part of email webhook integration workflow.
    """
    logger.info("=== Email Content Analysis ===")

    model = recommend_model("email classification", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    # Sample email content
    email_body = """
Hi,

Thank you for applying to the Senior Python Developer position at TechCorp.

We have reviewed your application and would like to schedule an interview.

Are you available for a video call next Tuesday at 2 PM EST?

Best regards,
Jane Smith
Talent Acquisition
TechCorp Inc.
"""

    system_prompt = """Classify email and extract information:
{
  "type": "job_listing|application_confirm|recruiter_outreach|interview_request|rejection",
  "company": "Company name",
  "action_required": "What user should do next",
  "urgency": "high|medium|low",
  "key_details": ["..."]
}"""

    prompt = f"Analyze this email:\n\n{email_body}"

    result = assistant.query(prompt, system_prompt)

    logger.info("Email Analysis:")
    print(result)

    return result


def example_code_review_integration():
    """
    Example: Review code changes before commit (CI/CD integration).
    """
    logger.info("=== Pre-Commit Code Review ===")

    # Get list of changed Python files (simulate git diff)
    changed_files = [Path("src/app/email_processor.py"), Path("src/app/email_parser.py")]

    model = recommend_model("code review", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    system_prompt = """You are a code reviewer. Check for:
1. Security vulnerabilities
2. Logic errors
3. Missing error handling
4. Performance issues

Respond with:
- "PASS" if no critical issues
- "WARN: <issue>" for non-critical
- "FAIL: <issue>" for critical

Keep response brief and actionable."""

    all_passed = True

    for file_path in changed_files:
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            continue

        logger.info(f"Reviewing {file_path}...")

        with open(file_path, "r", encoding="utf-8") as f:
            code = f.read()

        prompt = f"Review this code:\n\n```python\n{code[:4000]}\n```"  # Limit context

        result = assistant.query(prompt, system_prompt)

        if "FAIL" in result:
            logger.error(f"❌ {file_path.name}: {result}")
            all_passed = False
        elif "WARN" in result:
            logger.warning(f"⚠️ {file_path.name}: {result}")
        else:
            logger.info(f"✅ {file_path.name}: PASS")

    if all_passed:
        logger.info("✅ All files passed code review")
    else:
        logger.error("❌ Code review failed. Fix issues before committing.")

    return all_passed


def example_test_generation():
    """
    Example: Generate pytest tests for new module.
    """
    logger.info("=== Test Generation ===")

    # Target module to test
    module_path = Path("src/app/email_webhook.py")
    if not module_path.exists():
        logger.warning(f"Module not found: {module_path}")
        return

    model = recommend_model("test generation", available_vram_gb=12.0)
    assistant = OllamaAssistant(model)

    with open(module_path, "r", encoding="utf-8") as f:
        code = f.read()

    system_prompt = """Generate comprehensive pytest tests:
1. Test fixtures for setup
2. Unit tests for each method
3. Edge case testing
4. Error condition testing
5. Use pytest-mock for dependencies

Follow pytest best practices. Return ONLY the test code."""

    prompt = f"Generate pytest tests for:\n\n```python\n{code[:4000]}\n```"

    test_code = assistant.query(prompt, system_prompt)

    # Extract code
    if "```python" in test_code:
        test_code = test_code.split("```python")[1].split("```")[0].strip()
    elif "```" in test_code:
        test_code = test_code.split("```")[1].split("```")[0].strip()

    # Save test file
    test_filename = f"test_{module_path.stem}_generated.py"
    test_path = Path("tests") / test_filename

    with open(test_path, "w", encoding="utf-8") as f:
        f.write(test_code)

    logger.info(f"Generated test file: {test_path}")

    return test_code


def main():
    """Run example integrations"""

    print("\n" + "=" * 60)
    print("Ollama Code Assistant - Job Lead Finder Integration Examples")
    print("=" * 60 + "\n")

    examples = {
        "1": ("Resume Analysis (Privacy)", example_resume_analysis),
        "2": ("Batch Job Description Analysis", example_job_description_batch_analysis),
        "3": ("Code Generation", example_code_generation),
        "4": ("Email Analysis", example_email_analysis),
        "5": ("Pre-Commit Code Review", example_code_review_integration),
        "6": ("Test Generation", example_test_generation),
        "all": ("Run All Examples", None),
    }

    print("Available examples:")
    for key, (name, _) in examples.items():
        print(f"  {key}. {name}")
    print()

    choice = input("Select example (1-6 or 'all'): ").strip()

    if choice == "all":
        for key, (name, func) in examples.items():
            if func:  # Skip 'all' entry
                print(f"\n{'='*60}\n")
                try:
                    func()
                except Exception as e:
                    logger.error(f"Error in {name}: {e}", exc_info=True)
    elif choice in examples and examples[choice][1]:
        try:
            examples[choice][1]()
        except Exception as e:
            logger.error(f"Error: {e}", exc_info=True)
    else:
        print("Invalid choice")


if __name__ == "__main__":
    main()
