# Task: Fix PR #90 Test Failures

**Agent**: Ollama (qwen2.5-coder:32b)
**Priority**: HIGH
**Estimated Time**: 15-30 minutes
**Branch**: copilot/sub-pr-89 (PR #90)

## Context

PR #90 has failing tests after merge resolution. Two test fixes were attempted but CI still failing.

**CI Run**: Latest run shows 1 failing check (CI/build-and-test, 1m8s duration)
**Branch**: copilot/sub-pr-89
**PR**: #90 - "[AI] feat: Complete email webhook integration with job tracking"

## Recent Fixes Applied

1. **test_email_processor.py**: Added 50ms delay to `test_match_job_by_company_and_title` for test isolation
2. **test_gemini_cli.py**: Fixed `test_cli_exits_if_no_sdk_installed` by importing module before reload

## Task Requirements

1. **Check latest CI failure logs**:
   ```powershell
   gh run list --branch copilot/sub-pr-89 --limit 1 --json databaseId --jq '.[0].databaseId'
   gh run view <run_id> --log-failed
   ```

2. **Analyze root cause**:
   - Same tests failing or different ones?
   - Test isolation issues (shared data/leads.json)?
   - Import errors or assertion failures?
   - Merge conflict resolution side effects?

3. **Implement fix**:
   - Add proper test isolation (delays, tracker resets, tmp_path usage)
   - Fix any import or module issues
   - Ensure tests pass locally: `uv run pytest tests/test_email_processor.py tests/test_gemini_cli.py -v`

4. **Commit and push**:
   ```powershell
   git add <modified_files>
   git commit -m "[AI] fix: Resolve test failures in PR #90

   - <describe fix>
   - Ensures proper test isolation
   - Verified with local pytest run" --no-verify
   git push origin copilot/sub-pr-89
   ```

5. **Verify CI passes**:
   - Wait for CI run to complete
   - Check `gh pr checks 90`
   - Report success or next steps

## Success Criteria

- [ ] All tests passing in CI
- [ ] No test isolation issues
- [ ] PR #90 ready to merge
- [ ] Commit includes [AI] attribution tag

## Notes

- Use `--no-verify` to skip slow local pre-commit hooks
- Focus on test isolation - likely cause is shared state between parallel tests
- Previous similar issue fixed with 100ms delay in test_tracked_jobs_ui.py
- Check if xdist_group needed for test grouping

## Reference Files

- `tests/test_email_processor.py` (email processing tests)
- `tests/test_gemini_cli.py` (CLI tests)
- `tests/test_tracked_jobs_ui.py` (example of previous fix)
- `.pre-commit-config.yaml` (hook configuration)
