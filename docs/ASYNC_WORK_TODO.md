# Async Work Setup TODO

**Goal:** Enable giving work to AI without being at VSCode window (Slack, GitHub Issues, etc.)

## Current State
- ✅ GitHub Issues with `ai-task` label → AI creates PR
- ✅ PR reviews automated via GitHub Actions
- ❌ No Slack integration
- ❌ No async task queue

## Options

### 1. Slack Integration (Recommended)
**Setup:**
- Install Slack app with bot token
- Add slash commands: `/ai-task`, `/ai-review`, `/ai-search-jobs`
- Bot monitors channel for @mentions
- Replies with progress updates and results

**Benefits:**
- Natural conversation interface
- Real-time notifications
- Mobile access
- Team collaboration

**Implementation:**
```python
# src/app/slack_bot.py
from slack_sdk import WebClient
from slack_sdk.socket_mode import SocketModeClient
from slack_sdk.socket_mode.request import SocketModeRequest
from slack_sdk.socket_mode.response import SocketModeResponse

# Listen for slash commands and mentions
# Forward to existing AI workflows
```

**Required:**
- Slack app credentials (SLACK_BOT_TOKEN, SLACK_APP_TOKEN)
- Socket mode enabled for real-time events
- Docker service for slack bot

### 2. GitHub Issues (Already Working)
**Current:**
- Create issue with `ai-task` label
- AI dispatcher creates PR automatically

**Enhancements:**
- Add issue templates for common tasks
- Support issue comments for iterations
- Add `/ai` comment command for ad-hoc requests

### 3. Email Integration
**Setup:**
- Monitor Gmail/Outlook for emails to specific address
- Parse email body for task description
- Reply with progress updates

**Benefits:**
- No new tools needed
- Works from anywhere
- Can forward existing emails

### 4. Discord Bot
Similar to Slack but for Discord servers.

### 5. Web Dashboard with Task Queue
- Submit tasks via web form
- Queue jobs in background
- Check status/results later

## Recommended Approach

**Phase 1: Enhance GitHub Issues (Quick)**
- ✅ Already working
- Add issue templates
- Add comment-based commands

**Phase 2: Slack Integration (Best UX)**
- Real-time interaction
- Mobile friendly
- Team collaboration

**Phase 3: Email (Optional)**
- Backup channel
- Non-technical users

## Tasks

### High Priority
- [ ] Create GitHub issue templates for common AI tasks
- [ ] Add support for `/ai` comment commands in issues
- [ ] Document how to use GitHub issues for async work

### Medium Priority
- [ ] Set up Slack app and bot
- [ ] Create `slack_bot.py` service
- [ ] Add Slack integration to docker-compose.yml
- [ ] Test slash commands: `/ai-task`, `/ai-review`, `/ai-deploy`
- [ ] Add Slack notification to existing workflows

### Low Priority
- [ ] Email integration for task submission
- [ ] Discord bot for server communities
- [ ] Web task queue dashboard

## Immediate Next Steps

1. **GitHub Issue Templates** (15 min)
   - Create `.github/ISSUE_TEMPLATE/ai-task.yml`
   - Add fields: task type, description, priority
   - Auto-add `ai-task` label

2. **Document Async Workflow** (10 min)
   - Update README with "Remote Work" section
   - Show how to create tasks from mobile
   - Link to issue templates

3. **Slack App Setup** (30 min)
   - Create Slack app at api.slack.com
   - Enable Socket Mode
   - Add bot scopes: chat:write, commands
   - Get tokens for .env

## Example Workflows

### GitHub Issue
```
Title: Fix dark theme colors to match lovable.dev
Label: ai-task
Body:
The current dark theme is too light. Check the screenshot at
https://resume-quest-06.lovable.app/ and match those exact colors.

Background should be much darker (~hsl(222 47% 6%))
```

### Slack Command
```
/ai-task Fix the dark theme colors to match lovable.dev screenshot
```

### Slack Mention
```
@JobFlow-AI can you update the README to include deployment instructions?
```

## Related Files
- `.github/workflows/ai-task-dispatcher.yml` - Existing AI task automation
- `src/app/worker.py` - Background job processing
- `src/app/background_scheduler.py` - Task scheduling

## Notes
- Consider rate limits for API calls
- Add authentication for sensitive operations
- Log all AI-generated work for audit
- Allow cancellation of in-progress tasks
