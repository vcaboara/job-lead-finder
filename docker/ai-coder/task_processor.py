#!/usr/bin/env python3
"""
AI Coder - Autonomous task processor using Aider + Ollama
Watches .ai-tasks/*.md and executes tasks autonomously
"""

import logging
import os
import subprocess
import time
from pathlib import Path
from typing import Optional

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)


class TaskProcessor:
    def __init__(self):
        self.workspace = Path("/workspace")
        self.tasks_dir = self.workspace / ".ai-tasks"
        self.ollama_url = os.getenv("OLLAMA_BASE_URL", "http://host.docker.internal:11434")
        self.model = os.getenv("OLLAMA_MODEL", "qwen2.5-coder:32b")
        self.check_interval = int(os.getenv("CHECK_INTERVAL", "30"))

        # Ensure tasks directory exists
        self.tasks_dir.mkdir(exist_ok=True)

    def get_pending_task(self) -> Optional[Path]:
        """Find the first unprocessed task file"""
        for task_file in sorted(self.tasks_dir.glob("*.md")):
            # Skip if .processed or .failed file exists
            if not (task_file.with_suffix(".md.processed").exists() or task_file.with_suffix(".md.failed").exists()):
                return task_file
        return None

    def execute_task(self, task_file: Path) -> bool:
        """Execute a task using Aider"""
        try:
            logger.info(f"Processing task: {task_file.name}")

            # Read task instructions
            task_content = task_file.read_text(encoding="utf-8")
            logger.info(f"Task content:\n{task_content[:500]}...")

            # Set environment variables for Aider
            env = os.environ.copy()
            env["OLLAMA_API_BASE"] = self.ollama_url

            # Prepare aider command
            cmd = [
                "aider",
                "--yes-always",  # Auto-confirm all changes
                "--model",
                f"ollama/{self.model}",
                "--message",
                task_content,
            ]

            logger.info(f"Executing: {' '.join(cmd)}")
            logger.info(f"Ollama endpoint: {self.ollama_url}")

            # Run aider
            result = subprocess.run(
                cmd, cwd=self.workspace, capture_output=True, text=True, timeout=600, env=env  # 10 minute timeout
            )

            if result.returncode == 0:
                logger.info("Task completed successfully")
                logger.info(f"Aider output:\n{result.stdout}")

                # Commit changes
                self.commit_changes(task_file.stem)

                # Mark as processed
                task_file.rename(task_file.with_suffix(".md.processed"))
                return True
            else:
                logger.error(f"Task failed with exit code {result.returncode}")
                logger.error(f"Error output:\n{result.stderr}")

                # Mark as failed
                task_file.rename(task_file.with_suffix(".md.failed"))
                return False

        except subprocess.TimeoutExpired:
            logger.error("Task execution timed out")
            task_file.rename(task_file.with_suffix(".md.failed"))
            return False
        except Exception as e:
            logger.error(f"Task execution error: {e}", exc_info=True)
            task_file.rename(task_file.with_suffix(".md.failed"))
            return False

    def commit_changes(self, task_name: str):
        """Commit changes with proper attribution"""
        try:
            # Stage all changes
            subprocess.run(["git", "add", "-A"], cwd=self.workspace, check=True)

            # Create commit message with AI attribution
            commit_msg = f"""[AI] feat: {task_name}

---
AI-Generated-By: Aider + Ollama ({self.model})
"""

            # Commit (bypass pre-commit for now - let PR review catch issues)
            subprocess.run(["git", "commit", "-m", commit_msg, "--no-verify"], cwd=self.workspace, check=True)

            logger.info(f"Committed changes for task: {task_name}")

        except subprocess.CalledProcessError as e:
            logger.warning(f"Failed to commit changes: {e}")

    def run(self):
        """Main loop - watch for tasks and process them"""
        logger.info("AI Coder started")
        logger.info(f"Workspace: {self.workspace}")
        logger.info(f"Tasks directory: {self.tasks_dir}")
        logger.info(f"Ollama URL: {self.ollama_url}")
        logger.info(f"Model: {self.model}")
        logger.info(f"Check interval: {self.check_interval}s")

        while True:
            try:
                # Check for pending tasks
                task_file = self.get_pending_task()

                if task_file:
                    logger.info(f"Found pending task: {task_file.name}")
                    self.execute_task(task_file)
                else:
                    logger.debug("No pending tasks")

                # Wait before next check
                time.sleep(self.check_interval)

            except KeyboardInterrupt:
                logger.info("Shutting down...")
                break
            except Exception as e:
                logger.error(f"Error in main loop: {e}", exc_info=True)
                time.sleep(self.check_interval)


if __name__ == "__main__":
    processor = TaskProcessor()
    processor.run()
