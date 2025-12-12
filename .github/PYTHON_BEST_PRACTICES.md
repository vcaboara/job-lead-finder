# Python Best Practices for AI-Generated Code

## Essential Python Magic Methods

Magic methods (dunder methods) enable Python objects to integrate seamlessly with built-in language features. Use these to make classes more Pythonic:

### 1. Object Representation
- **`__str__(self)`**: Human-readable string for `str()` and `print()`
  ```python
  def __str__(self):
      return f"User({self.name}, {self.email})"
  ```
- **`__repr__(self)`**: Unambiguous representation for debugging
  ```python
  def __repr__(self):
      return f"User(id={self.id}, name={self.name!r}, email={self.email!r})"
  ```

### 2. Comparison Operators
Implement for sortable objects:
- **`__eq__(self, other)`**: Equality (`==`)
- **`__lt__(self, other)`**: Less than (`<`)
- **`__le__(self, other)`**: Less than or equal (`<=`)
- **`__gt__(self, other)`**: Greater than (`>`)
- **`__ge__(self, other)`**: Greater than or equal (`>=`)
  ```python
  def __eq__(self, other):
      if not isinstance(other, Job):
          return NotImplemented
      return self.id == other.id

  def __lt__(self, other):
      if not isinstance(other, Job):
          return NotImplemented
      return self.created_at < other.created_at
  ```

### 3. Container Methods
Make objects behave like containers:
- **`__len__(self)`**: Return length for `len()`
- **`__getitem__(self, key)`**: Enable indexing `obj[key]`
- **`__setitem__(self, key, value)`**: Enable assignment `obj[key] = value`
- **`__delitem__(self, key)`**: Enable deletion `del obj[key]`
- **`__contains__(self, item)`**: Enable `in` operator
  ```python
  def __len__(self):
      return len(self.jobs)

  def __getitem__(self, index):
      return self.jobs[index]

  def __contains__(self, job_id):
      return job_id in self.job_ids
  ```

### 4. Context Managers
Enable `with` statement usage:
- **`__enter__(self)`**: Setup when entering context
- **`__exit__(self, exc_type, exc_val, exc_tb)`**: Cleanup when exiting
  ```python
  def __enter__(self):
      self.connection = self.connect()
      return self

  def __exit__(self, exc_type, exc_val, exc_tb):
      if self.connection:
          self.connection.close()
      return False  # Don't suppress exceptions
  ```

### 5. Callable Objects
Make objects callable like functions:
- **`__call__(self, *args, **kwargs)`**: Enable `obj()` syntax
  ```python
  class JobFilter:
      def __init__(self, status):
          self.status = status

      def __call__(self, job):
          return job.status == self.status

  # Usage: active_filter = JobFilter("active")
  # active_jobs = list(filter(active_filter, jobs))
  ```

### 6. Arithmetic Operators
Implement for numeric-like objects:
- **`__add__(self, other)`**: Addition (`+`)
- **`__sub__(self, other)`**: Subtraction (`-`)
- **`__mul__(self, other)`**: Multiplication (`*`)
- **`__truediv__(self, other)`**: Division (`/`)

### 7. Iteration Support
- **`__iter__(self)`**: Return iterator for `for` loops
- **`__next__(self)`**: Get next item in iteration
  ```python
  def __iter__(self):
      return iter(self.jobs)
  ```

### Best Practices for Magic Methods
1. **Always return `NotImplemented`** for unsupported types in comparison/arithmetic
2. **Implement `__repr__` for all classes** - essential for debugging
3. **Make `__str__` user-friendly**, `__repr__` developer-friendly
4. **Use `@functools.total_ordering`** if implementing comparisons (only need `__eq__` and one other)
5. **Context managers should be exception-safe** - cleanup in `__exit__` even on errors

## Clean Code Principles

### 1. Naming Conventions
**Follow PEP 8 strictly:**
- **snake_case**: Functions, variables, methods
- **UPPER_SNAKE_CASE**: Constants
- **PascalCase**: Classes
- **_leading_underscore**: Internal/private
  ```python
  # Good
  class JobTracker:
      MAX_RETRIES = 3

      def __init__(self):
          self._jobs = {}  # Internal

      def get_active_jobs(self):
          return [j for j in self._jobs.values() if j.is_active]

  # Bad
  class jobTracker:  # Wrong case
      maxRetries = 3  # Should be UPPER_SNAKE_CASE

      def GetActiveJobs(self):  # Wrong case
          return [j for j in self.Jobs.values()]  # Inconsistent
  ```

### 2. Function Design
**Keep functions small and focused:**
- **Single responsibility**: One function, one purpose
- **Max 20-30 lines**: If longer, extract helper functions
- **Max 3-4 parameters**: Use dataclasses/kwargs for more
- **Pure when possible**: Same input → same output, no side effects
  ```python
  # Good: Small, focused functions
  def calculate_score(job: Job, resume: Resume) -> float:
      """Calculate job match score (0-100)."""
      skills_score = _calculate_skills_match(job.required_skills, resume.skills)
      experience_score = _calculate_experience_match(job.years_required, resume.years)
      return (skills_score * 0.7) + (experience_score * 0.3)

  def _calculate_skills_match(required: set[str], candidate: set[str]) -> float:
      """Calculate skills overlap percentage."""
      if not required:
          return 100.0
      overlap = len(required & candidate)
      return (overlap / len(required)) * 100

  # Bad: Too long, multiple responsibilities
  def process_job(job_data, resume_text, config_file, output_path):
      # Parsing
      job = parse_job_data(job_data)
      resume = parse_resume(resume_text)
      # Scoring
      skills_overlap = len(set(job["skills"]) & set(resume["skills"]))
      score = (skills_overlap / len(job["skills"])) * 100
      # Validation
      if score < 50: return None
      # File I/O
      with open(config_file) as f: config = json.load(f)
      # More processing...
      # 50+ more lines...
  ```

### 3. Avoid Deep Nesting
**Use early returns, guard clauses:**
  ```python
  # Good: Flat structure with early returns
  def validate_job(job: dict) -> Optional[str]:
      """Validate job data. Returns error message if invalid."""
      if not job:
          return "Job data is missing"

      if "title" not in job:
          return "Job title is required"

      if not job["title"].strip():
          return "Job title cannot be empty"

      if "company" not in job:
          return "Company name is required"

      return None  # Valid

  # Bad: Deep nesting (callback hell)
  def validate_job(job):
      if job:
          if "title" in job:
              if job["title"].strip():
                  if "company" in job:
                      return None
                  else:
                      return "Company required"
              else:
                  return "Title empty"
          else:
              return "Title required"
      else:
          return "Job missing"
  ```

### 4. Use Type Hints
**Type hints improve readability and catch errors:**
  ```python
  from typing import List, Dict, Optional, Union
  from dataclasses import dataclass

  @dataclass
  class Job:
      id: str
      title: str
      company: str
      salary_min: Optional[int] = None
      salary_max: Optional[int] = None

  def filter_jobs(
      jobs: List[Job],
      min_salary: int,
      statuses: Optional[List[str]] = None
  ) -> List[Job]:
      """Filter jobs by salary and optional status list."""
      filtered = [j for j in jobs if j.salary_min and j.salary_min >= min_salary]

      if statuses:
          filtered = [j for j in filtered if j.status in statuses]

      return filtered
  ```

### 5. Prefer Comprehensions
**Use comprehensions for transformations:**
  ```python
  # Good: Clear, concise
  active_jobs = [j for j in jobs if j.is_active]
  job_ids = {j.id for j in jobs}  # Set comprehension
  job_map = {j.id: j for j in jobs}  # Dict comprehension

  # Bad: Verbose loops
  active_jobs = []
  for job in jobs:
      if job.is_active:
          active_jobs.append(job)
  ```

### 6. Use Context Managers
**Ensure resources are cleaned up:**
  ```python
  # Good: Automatic cleanup
  with open("jobs.json") as f:
      data = json.load(f)

  with DatabaseConnection() as db:
      db.save_jobs(jobs)

  # Bad: Manual cleanup (error-prone)
  f = open("jobs.json")
  data = json.load(f)
  f.close()  # Might not execute if error occurs
  ```

### 7. Error Handling
**Be specific with exceptions:**
  ```python
  # Good: Specific exceptions
  def load_config(path: str) -> Dict:
      try:
          with open(path) as f:
              return json.load(f)
      except FileNotFoundError:
          logger.error(f"Config file not found: {path}")
          return get_default_config()
      except json.JSONDecodeError as e:
          logger.error(f"Invalid JSON in config: {e}")
          raise ConfigError(f"Malformed config file: {path}") from e
      except PermissionError:
          logger.error(f"Permission denied reading config: {path}")
          raise

  # Bad: Bare except
  def load_config(path):
      try:
          with open(path) as f:
              return json.load(f)
      except:  # Catches everything, even KeyboardInterrupt!
          return {}
  ```

### 8. Use Dataclasses
**Reduce boilerplate for data objects:**
  ```python
  from dataclasses import dataclass, field
  from typing import List

  # Good: Clean, automatic __init__, __repr__, __eq__
  @dataclass
  class Job:
      id: str
      title: str
      company: str
      skills: List[str] = field(default_factory=list)
      salary: Optional[int] = None

      def __post_init__(self):
          """Validation after initialization."""
          if not self.title.strip():
              raise ValueError("Title cannot be empty")

  # Bad: Boilerplate class
  class Job:
      def __init__(self, id, title, company, skills=None, salary=None):
          self.id = id
          self.title = title
          self.company = company
          self.skills = skills if skills else []
          self.salary = salary

      def __repr__(self):
          return f"Job(id={self.id}, title={self.title}, ...)"

      def __eq__(self, other):
          # Many more lines...
  ```

### 9. Document with Docstrings
**Use clear, structured docstrings:**
  ```python
  def search_jobs(
      query: str,
      filters: Optional[Dict[str, Any]] = None,
      limit: int = 10
  ) -> List[Job]:
      """
      Search for jobs matching query and filters.

      Args:
          query: Search keywords (job title, skills, etc.)
          filters: Optional filters dict with keys:
              - location (str): City or remote
              - min_salary (int): Minimum salary
              - job_type (str): full-time, contract, etc.
          limit: Maximum number of results (default: 10)

      Returns:
          List of Job objects matching criteria, sorted by relevance.

      Raises:
          ValueError: If query is empty or limit < 1
          APIError: If external job API request fails

      Example:
          >>> jobs = search_jobs("Python developer", {"location": "remote"}, limit=5)
          >>> len(jobs)
          5
      """
      if not query.strip():
          raise ValueError("Search query cannot be empty")
      # Implementation...
  ```

### 10. Organize Imports
**Follow PEP 8 import order:**
  ```python
  # 1. Standard library
  import json
  import logging
  from pathlib import Path
  from typing import List, Optional

  # 2. Third-party
  import requests
  from flask import Flask, request

  # 3. Local application
  from app.models import Job, Company
  from app.utils import validate_email
  ```

## Anti-Patterns to Avoid

### 1. Mutable Default Arguments
  ```python
  # Bad: Mutable default shared across calls
  def add_job(job, jobs=[]):  # BUG!
      jobs.append(job)
      return jobs

  # Good: Use None and create new list
  def add_job(job, jobs=None):
      if jobs is None:
          jobs = []
      jobs.append(job)
      return jobs
  ```

### 2. Using `eval()` or `exec()`
  ```python
  # Bad: Security vulnerability
  user_code = request.form.get("code")
  eval(user_code)  # NEVER DO THIS!

  # Good: Use safe alternatives
  import ast
  result = ast.literal_eval(safe_string)  # Only for literals
  ```

### 3. Ignoring Python's "There's Only One Way"
  ```python
  # Bad: Checking type of boolean
  if success == True:

  # Good: Direct boolean check
  if success:

  # Bad: Checking length for emptiness
  if len(items) > 0:

  # Good: Truthiness check
  if items:
  ```

### 4. Not Using `pathlib`
  ```python
  # Bad: String concatenation for paths
  path = base_dir + "/" + subfolder + "/" + filename

  # Good: pathlib
  from pathlib import Path
  path = Path(base_dir) / subfolder / filename
  ```

### 5. Using `*` Imports
  ```python
  # Bad: Pollutes namespace, unclear origins
  from app.models import *
  from app.utils import *

  # Good: Explicit imports
  from app.models import Job, Company
  from app.utils import validate_email, format_salary
  ```

## Code Quality Checklist

Before committing AI-generated Python code, verify:

- [ ] **Naming**: snake_case, PascalCase, UPPER_CASE used correctly
- [ ] **Functions**: < 30 lines, single responsibility, < 4 parameters
- [ ] **Nesting**: Max 2-3 levels, use early returns
- [ ] **Type Hints**: All functions have typed signatures
- [ ] **Docstrings**: Public functions documented with Args/Returns/Raises
- [ ] **Error Handling**: Specific exceptions, no bare `except:`
- [ ] **Context Managers**: Used for file/connection handling
- [ ] **Comprehensions**: Used instead of simple loops
- [ ] **Magic Methods**: Implemented for custom classes (`__str__`, `__repr__`, etc.)
- [ ] **Imports**: Organized in standard order
- [ ] **Dataclasses**: Used for simple data containers
- [ ] **No Anti-Patterns**: No mutable defaults, `eval()`, `*` imports
- [ ] **Pythonic**: Follows Python idioms, not Java/C++ patterns
- [ ] **PEP 8 Compliant**: Passes `black` and `flake8` checks

## References

These guidelines synthesize best practices from:
- PEP 8 (Style Guide for Python Code)
- PEP 20 (The Zen of Python)
- Python Data Model (Magic Methods)
- Real Python tutorials
- Google Python Style Guide
- "Clean Code" principles adapted for Python
