#!/usr/bin/env python3
"""
Autonomous Task Executor
Reads TODOs, assigns to AI agents, monitors progress, creates PRs.
Integrates with Vibe Kanban, Vibe Check MCP, and AI Resource Monitor.
"""

import re
import sys
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    import httpx
except ImportError:
    print("Error: httpx not installed. Run: pip install httpx")
    sys.exit(1)


class TaskOrchestrator:
    """Orchestrate tasks across AI agents with minimal human interaction."""

    def __init__(self):
        self.kanban_url = "http://localhost:3001"
        self.vibe_check_url = "http://localhost:3000"
        self.monitor_url = "http://localhost:9000"
        self.todo_file = Path("docs/TODO.md")
        self.project_root = Path(__file__).parent.parent

    def parse_todos(self) -> List[Dict]:
        """Parse TODO.md and extract actionable tasks."""
        if not self.todo_file.exists():
            print(f"Error: {self.todo_file} not found")
            return []

        content = self.todo_file.read_text(encoding="utf-8")

        tasks = []
        current_priority = "P1"  # Default priority
        current_track = None
        in_section = False
        track_counter = 0

        for line in content.split("\n"):
            # Detect AI/ML Infrastructure section (start of relevant section)
            if "AI/ML Infrastructure & Automation" in line:
                in_section = True
                continue

            # Stop at Developer Experience or other major sections
            if in_section and line.startswith("### Developer Experience"):
                break

            if not in_section:
                continue

            # Detect task items (bullet points with checkboxes)
            if re.match(r"^- \[([ x])\]", line):
                # Extract checkbox state and text
                match = re.match(r"^- \[([ x])\]\s+\*\*(.+?)\*\*", line)
                if match:
                    is_complete = match.group(1) == "x"
                    task_name = match.group(2).strip()

                    # Create a new track for each major task
                    track_counter += 1
                    current_track = {
                        "id": track_counter,
                        "name": task_name,
                        "priority": current_priority,
                        "items": [],
                        "status": "completed" if is_complete else "not-started",
                        "completed": is_complete,
                    }
                    tasks.append(current_track)

            # Detect sub-items (indented lines under a task)
            elif current_track and line.strip().startswith("-") and not line.strip().startswith("- ["):
                # This is a sub-item/detail
                sub_text = line.strip()[1:].strip()
                if sub_text and not sub_text.startswith("**"):
                    current_track["items"].append(
                        {"description": sub_text, "completed": current_track.get("completed", False)}
                    )

        return tasks

    def get_resource_allocation(self) -> Dict:
        """Check AI resource availability from monitor service."""
        try:
            response = httpx.get(f"{self.monitor_url}/api/metrics", timeout=5)
            return response.json()
        except httpx.ConnectError:
            print("⚠️  Warning: AI Monitor not accessible at {}".format(self.monitor_url))
            return self._get_default_resources()
        except Exception as e:
            print("⚠️  Warning: Error fetching resources: {}".format(e))
            return self._get_default_resources()

    def _get_default_resources(self) -> Dict:
        """Return default resource allocation when monitor is unavailable."""
        return {
            "copilot": {"remaining": 1500, "daily": 0, "monthly": 0},
            "gemini": {"remaining": 20, "daily": 0},
            "ollama": {"status": "unknown"},
        }

    def assign_agent(self, track: Dict, resources: Dict) -> str:
        """Assign optimal AI agent based on task priority and available resources."""
        priority = track.get("priority", "P3")
        track_id = track.get("id", 0)

        # P0: Memory Bank - Use Gemini (free, good for documentation)
        if priority == "P0" or track_id == 1:
            if resources.get("gemini", {}).get("remaining", 0) > 5:
                return "gemini"

        # P1: High-priority implementation - Use Copilot if available
        if priority == "P1":
            if resources.get("copilot", {}).get("remaining", 0) > 50:
                return "copilot"

        # P2: Medium priority - Prefer local LLM if available
        if priority == "P2":
            ollama = resources.get("ollama", {})
            if ollama.get("status") == "running":
                return "local"

        # Fallback hierarchy: Local LLM > Gemini > Copilot
        if resources.get("ollama", {}).get("status") == "running":
            return "local"

        if resources.get("gemini", {}).get("remaining", 0) > 0:
            return "gemini"

        return "copilot"  # Last resort

    def create_kanban_task(self, track: Dict, agent: str) -> Optional[int]:
        """Create task in Vibe Kanban board."""
        try:
            response = httpx.post(
                f"{self.kanban_url}/api/tasks",
                json={
                    "title": track["name"],
                    "track": track["id"],
                    "priority": track["priority"],
                    "agent": agent,
                    "items": track["items"],
                    "status": "backlog",
                },
                timeout=5,
            )
            if response.status_code in [200, 201]:
                return response.json().get("id")
            elif response.status_code == 404:
                print("   ⚠️  Vibe Kanban API endpoint not found (is it running?)")
                return None
            else:
                print(f"   ⚠️  Vibe Kanban returned {response.status_code}: {response.text[:100]}")
                return None
        except httpx.ConnectError:
            print(f"   ⚠️  Vibe Kanban not accessible at {self.kanban_url}")
            print("      Check: docker compose ps | grep kanban")
            return None
        except Exception as e:
            print(f"   ⚠️  Error creating Kanban task: {e}")
            return None

    def print_execution_plan(self, tasks: List[Dict], resources: Dict):
        """Print the execution plan before starting."""
        print("\n" + "=" * 70)
        print("📋 EXECUTION PLAN")
        print("=" * 70)

        print("\n📊 Available Resources:")
        print(f"   Copilot Pro: {resources.get('copilot', {}).get('remaining', 0)}/1500 requests")
        print(f"   Gemini API:  {resources.get('gemini', {}).get('remaining', 0)}/20 requests (today)")
        ollama_status = resources.get("ollama", {}).get("status", "unknown")
        print(f"   Local LLM:   {ollama_status}")

        p0_tasks = [t for t in tasks if t["priority"] == "P0"]
        p1_tasks = [t for t in tasks if t["priority"] == "P1"]

        print("\n🎯 Tasks to Execute:")
        print("   P0 (Foundation): {} tracks".format(len(p0_tasks)))
        print("   P1 (High-Value): {} tracks".format(len(p1_tasks)))

        print("\n📝 Task Assignments:")
        for track in tasks:
            if track["priority"] in ["P0", "P1"]:
                agent = self.assign_agent(track, resources)
                completed = sum(1 for item in track["items"] if item["completed"])
                total = len(track["items"])

                print(f"   Track {track['id']}: {track['name']} ({track['priority']})")
                print(f"      → Agent: {agent.upper()}")
                print(f"      → Progress: {completed}/{total} items completed")

    def generate_guidance(self, track: Dict, agent: str) -> str:
        """Generate guidance text for AI agents to execute the track."""
        items_text = "\n".join(
            [f"   {idx}. {item['description']}" for idx, item in enumerate(track["items"], 1) if not item["completed"]]
        )

        guidance = f"""
# Task: {track['name']} (Priority: {track['priority']})

## Assigned Agent: {agent.upper()}

## Objectives:
{items_text}

## Context:
- Project: Job Lead Finder (Python 3.12, FastAPI, Docker)
- Memory Bank: memory/ directory contains project documentation
- Code Style: Follow black, isort, flake8 standards
- Testing: Use pytest, aim for >80% coverage

## Workflow:
1. Read relevant Memory Bank files for context
2. Implement each objective sequentially
3. Write tests for new code
4. Run tests locally: pytest -m ""
5. Validate with pre-commit hooks
6. Create commits with clear messages

## Success Criteria:
- All objectives completed
- Tests passing
- Code passes linting (black, flake8)
- Documentation updated if needed

## Output:
When complete, create a PR with:
- Title: "{track['name']}"
- Branch: auto/track-{track['id']}-{track['name'].lower().replace(' ', '-')[:30]}
- Description: Checklist of completed objectives
"""
        return guidance

    def run_autonomous_cycle(self, dry_run: bool = True):
        """Main autonomous execution cycle."""
        print("\n" + "=" * 70)
        print("🤖 AUTONOMOUS TASK EXECUTOR")
        print("=" * 70)
        print(f"   Mode: {'DRY RUN (Planning Only)' if dry_run else 'EXECUTION'}")
        print(f"   Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

        # 1. Parse TODOs
        print("\n📋 Step 1: Parsing tasks from docs/TODO.md...")
        tasks = self.parse_todos()
        if not tasks:
            print("   ⚠️  No tasks found")
            return

        print(f"   ✓ Found {len(tasks)} tracks")

        # 2. Check resources
        print("\n📊 Step 2: Checking AI resource availability...")
        resources = self.get_resource_allocation()

        # 3. Generate execution plan
        self.print_execution_plan(tasks, resources)

        # 4. Create Kanban tasks (if not dry run)
        if not dry_run:
            print("\n🎯 Step 3: Creating Kanban tasks...")
            for track in tasks:
                if track["priority"] in ["P0", "P1"]:
                    agent = self.assign_agent(track, resources)
                    task_id = self.create_kanban_task(track, agent)

                    if task_id:
                        print(f"   ✓ Track {track['id']}: Created (ID: {task_id})")
                    else:
                        print(f"   ⚠️  Track {track['id']}: Failed to create")

        # 5. Generate guidance files
        print("\n📝 Step 4: Generating AI guidance files...")
        guidance_dir = self.project_root / ".ai-tasks"
        guidance_dir.mkdir(exist_ok=True)

        for track in tasks:
            if track["priority"] in ["P0", "P1"]:
                agent = self.assign_agent(track, resources)
                guidance = self.generate_guidance(track, agent)

                guidance_file = guidance_dir / f"track-{track['id']}-{agent}.md"
                guidance_file.write_text(guidance, encoding="utf-8")
                print(f"   ✓ Created: {guidance_file.relative_to(self.project_root)}")

        # Summary
        print("\n" + "=" * 70)
        print("✅ AUTONOMOUS CYCLE COMPLETE")
        print("=" * 70)

        if dry_run:
            print("\n📌 Next Steps (DRY RUN):")
            print("   1. Review execution plan above")
            print("   2. Check generated guidance files in .ai-tasks/")
            print("   3. Run with --execute flag to start automation")
            print("\n   Command: python scripts/autonomous_task_executor.py --execute")
        else:
            print("\n📌 Monitoring Dashboards:")
            print(f"   • Vibe Kanban:    {self.kanban_url}")
            print(f"   • AI Monitor:     {self.monitor_url}")
            print(f"   • Vibe Check MCP: {self.vibe_check_url}")

            print("\n📁 AI Guidance Files:")
            print("   • Location: .ai-tasks/")
            print("   • Usage: Feed these to Claude/Copilot for execution")


def main():
    import argparse

    parser = argparse.ArgumentParser(description="Autonomous AI Task Executor")
    parser.add_argument(
        "--execute",
        action="store_true",
        help="Execute tasks (default is dry-run/planning mode)",
    )
    args = parser.parse_args()

    orchestrator = TaskOrchestrator()
    orchestrator.run_autonomous_cycle(dry_run=not args.execute)


if __name__ == "__main__":
    main()
