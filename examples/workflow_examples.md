# Real-World Workflow Examples

This document shows how to use Speculator Bot with MCP in real development workflows.

## 🔄 Daily Development Workflows

### Workflow 1: Pre-Commit Check

**Scenario**: Before committing code, check if it's safe

**Steps**:
1. Stage your changes: `git add .`
2. Ask Claude: **"Analyze the risk of my staged changes"**
3. Review the risk score and recommendations
4. If acceptable, commit: `git commit -m "..."`

**Claude's Response Example**:
```
I've analyzed your staged changes:

Risk Assessment:
- Risk Score: 0.32 (LOW)
- Files Changed: 3
- No high-risk files detected

Recommendations:
✓ Change appears low-risk
✓ Standard review process recommended
✓ Estimated test time: 4.5 minutes

You're good to commit! 👍
```

---

### Workflow 2: Pull Request Review

**Scenario**: Reviewing a teammate's PR

**Steps**:
1. Checkout the PR branch: `git checkout feature/payment-refactor`
2. Ask Claude: **"Analyze deployment risk for the last commit"**
3. Ask: **"Which tests should we run for this PR?"**
4. Run the suggested tests
5. Review high-risk files more carefully

**Example Conversation**:
```
You: "Analyze deployment risk for commit abc123"

Claude: 
Risk Analysis for commit abc123:
- Risk Score: 0.75 (HIGH)
- High Risk Files:
  • src/payment/processor.py (0.82)
  • src/payment/gateway.py (0.68)

Concerns:
⚠️ payment/processor.py has 5 historical failures
⚠️ Large change (250 lines added)
⚠️ Modifies critical payment processing logic

Recommendations:
1. Thorough code review required
2. Test in staging first
3. Have rollback plan ready

You: "Which tests should we run?"

Claude:
Selected 12 critical tests:
1. Payment Processing - Credit Card ✓
2. Payment Processing - Refund ✓
3. Payment Gateway Integration ✓
4. Security - SQL Injection ✓
...

Total time: 8.5 minutes
Coverage: 95%
```

---

### Workflow 3: Release Preparation

**Scenario**: Preparing for production release

**Steps**:
1. Checkout release branch: `git checkout release/v2.5`
2. Ask Claude: **"Analyze all changes between v2.4 and v2.5"**
3. Ask: **"Generate a deployment risk report for this release"**
4. Review the HTML report with stakeholders
5. Make go/no-go decision

**Example**:
```
You: "Compare risk between tag v2.4 and current HEAD"

Claude:
Release Risk Analysis (v2.4 → v2.5):

Total Changes:
- 47 files modified
- 1,234 lines added
- 567 lines removed

Risk Distribution:
- Critical: 2 files
- High: 5 files
- Medium: 12 files
- Low: 28 files

Critical Files:
1. src/auth/session.py (0.85) - Session management changes
2. src/database/migration_045.sql (0.90) - Schema changes

Overall Risk: 0.58 (MEDIUM-HIGH)

Recommendation:
⚠️ DEPLOY WITH CAUTION
- Focus testing on auth and database
- Staged rollout recommended
- Monitor session metrics post-deploy

You: "Export this as an HTML report for the team"

Claude: ✓ Report exported to release_v2.5_analysis.html
```

---

### Workflow 4: Hotfix Validation

**Scenario**: Quick validation of urgent hotfix

**Steps**:
1. Create hotfix branch: `git checkout -b hotfix/payment-bug`
2. Make the fix
3. Ask Claude: **"Quick risk check on my hotfix"**
4. If low risk, fast-track to production

**Example**:
```
You: "This is a hotfix for the payment timeout issue. 
      Analyze the risk of my change."

Claude:
Hotfix Risk Analysis:

Changes:
- 1 file: src/payment/timeout_config.py
- 3 lines changed (configuration only)

Risk: 0.15 (MINIMAL) ✓

Risk Factors:
- Configuration-only change: Low risk
- No code logic modified
- File has no failure history

Recommended Tests:
1. Payment timeout test (12s)
2. Payment integration test (25s)
Total: ~40 seconds

Recommendation:
✅ SAFE FOR HOTFIX
- Minimal risk change
- Run 2 quick tests
- Can fast-track to production
```

---

### Workflow 5: Refactoring Safety Check

**Scenario**: Large refactoring - ensure nothing breaks

**Steps**:
1. Complete refactoring
2. Ask Claude: **"I refactored the auth module. What's the risk?"**
3. Ask: **"What tests MUST pass before I can merge this?"**
4. Run critical tests first

**Example**:
```
You: "I refactored the entire authentication module. 
      What's the deployment risk?"

Claude:
Refactoring Risk Analysis:

Changes Detected:
- 8 files in src/auth/
- Heavy refactoring (500+ lines changed)
- No external API changes detected ✓

Risk Score: 0.52 (MEDIUM)

Positive Signals:
✓ No changes to public interfaces
✓ Test coverage maintained
✓ No database schema changes

Concerns:
⚠️ Large change to critical auth system
⚠️ Complex logic changes detected

MUST-RUN Tests (Critical):
1. User Authentication - Login
2. User Authentication - Password Reset  
3. Session Management
4. Security - SQL Injection
5. API - User Endpoints

SHOULD-RUN Tests (High Priority):
6. Unit - Validation Utils
7. Integration - User CRUD
...

Total Critical Tests: 5 (est. 3.2 min)
Total Recommended: 18 (est. 10.5 min)

Recommendation:
✓ REFACTORING APPEARS SAFE
- Run all 18 recommended tests
- Monitor auth metrics post-deploy
- Consider staged rollout
```

---

## 🎯 Specialized Workflows

### Database Migration Workflow

**Scenario**: Validating database changes

```
You: "I have a database migration. Check the risk."

Claude:
Database Migration Analysis:

Schema Changes Detected:
- ADD COLUMN: users.last_login_ip (VARCHAR)
- CREATE INDEX: idx_users_last_login
- MODIFY COLUMN: orders.status (VARCHAR → ENUM)

Risk Assessment: 0.45 (MEDIUM)

Impact Analysis:
✓ ADD COLUMN: Low risk (nullable, has default)
✓ CREATE INDEX: Performance improvement expected
⚠️ MODIFY COLUMN: Breaking change potential

Query Impact:
- SELECT queries: +5% performance (index)
- INSERT queries: -3% performance (index overhead)
- Queries using orders.status: REQUIRES CODE UPDATE

Critical Checks:
1. Verify all code using orders.status
2. Test with production-like data volume
3. Plan for rollback scenario
4. Check replication lag

Recommendation:
⚠️ CAREFUL DEPLOYMENT NEEDED
- Update application code first
- Test migration in staging with prod data
- Schedule during low-traffic window
```

---

### CI/CD Integration Workflow

**In Your CI/CD Pipeline**:

```bash
# In your .github/workflows/ or Jenkins pipeline

# Step 1: Run Speculator Bot
speculator analyze \
  --commit $COMMIT_SHA \
  --test-catalog tests.json \
  --output speculator_report.json \
  --format json

# Step 2: Parse results
RISK_SCORE=$(jq -r '.deployment_risk_score' speculator_report.json)

# Step 3: Make decisions
if (( $(echo "$RISK_SCORE >= 0.8" | bc -l) )); then
    echo "❌ BLOCK: Critical risk detected"
    exit 1
elif (( $(echo "$RISK_SCORE >= 0.6" | bc -l) )); then
    echo "⚠️ WARN: High risk - requires approval"
    # Trigger manual approval
    create_approval_request
else
    echo "✅ PASS: Risk acceptable"
fi

# Step 4: Run selected tests
jq -r '.test_selection.selected_tests[].test_path' speculator_report.json | \
  xargs pytest
```

**Ask Claude to Review CI Results**:
```
You: "The CI ran and generated this report: [paste speculator_report.json]
      Should we deploy?"

Claude: [Analyzes the full JSON report]
Based on the CI analysis:

Risk Score: 0.44 (MEDIUM)
Tests Run: 23/23 passed ✓
Coverage: 89%

Decision: ✅ SAFE TO DEPLOY

Rationale:
- All selected tests passed
- Risk within acceptable range
- Good test coverage of changes
- No critical files modified

Post-Deploy Monitoring:
- Watch error rates for 1 hour
- Monitor payment processing metrics
- Have rollback ready
```

---

## 🔧 Advanced Usage Patterns

### Pattern 1: Risk Trend Analysis

```
You: "Show me the risk trend for the last 5 commits"

Claude: [Uses analyze_risk for each commit]
Risk Trend (Last 5 Commits):

commit abc123: 0.65 (HIGH) ⬆️
commit def456: 0.52 (MEDIUM) 
commit ghi789: 0.48 (MEDIUM)
commit jkl012: 0.33 (LOW) ⬇️
commit mno345: 0.28 (LOW)

Trend: INCREASING RISK ⚠️

Analysis:
- Risk jumped 25% in last commit
- New high-risk file: payment/processor.py
- Increasing complexity detected

Recommendation:
- Review recent changes to payment module
- Consider breaking into smaller commits
- Add more test coverage
```

---

### Pattern 2: Comparative Analysis

```
You: "Compare the risk between my feature branch and main"

Claude:
Branch Comparison: feature/new-api vs main

Feature Branch:
- Risk Score: 0.58
- Files Changed: 12
- High Risk: 3 files

Main Branch:
- Risk Score: 0.35
- Stable baseline

Delta Analysis:
- Risk increased by 66% ⚠️
- 3 new high-risk files added
- 156% increase in code complexity

High-Risk Additions:
1. api/v2/endpoints.py (new)
2. api/v2/validators.py (new)
3. database/schema_v2.sql (new)

Recommendation:
⚠️ Feature branch riskier than main
- Add integration tests for new API
- Review new endpoints thoroughly
- Consider splitting into smaller PRs
```

---

## 💡 Pro Tips

### Tip 1: Context Matters
```
❌ "Check my code"
✅ "Analyze risk for the payment refactoring in commit abc123"
```

### Tip 2: Chain Commands
```
You: "Analyze my changes, select the critical tests, 
      and export a report for my manager"

Claude: [Does all three in sequence]
```

### Tip 3: Ask for Explanations
```
You: "Why is payment/processor.py high risk?"

Claude: Breaks down the specific risk factors
```

### Tip 4: Use for Learning
```
You: "Teach me what makes a change high risk"

Claude: Explains risk factors with examples from your code
```

---

## 🎓 Learning Workflows

### New Team Member Onboarding

```
You: "I'm new to this codebase. What are the most 
      critical files I should be careful with?"

Claude: [Reads historical data and configuration]
Critical Files in This Codebase:

High-Risk Areas:
1. src/payment/ - Payment processing
   - 15 historical failures
   - Handle with extreme care
   
2. src/auth/ - Authentication
   - Critical for security
   - Requires thorough testing

3. src/database/migrations/ - Schema changes
   - Can affect production data
   - Always test rollback

Tips for New Contributors:
- Changes to payment/ always need senior review
- Auth changes require security review
- Small PRs preferred over large ones
- Always run full test suite for critical areas
```

---

## 📊 Reporting Workflows

### Weekly Risk Report

```
You: "Generate a risk report for all commits this week"

Claude: [Analyzes all commits from the week]

Weekly Risk Report (Oct 7-13, 2025):

Summary:
- Total Commits: 47
- Average Risk: 0.42
- High Risk Commits: 3
- Critical Files Modified: 8

Riskiest Changes:
1. Payment timeout refactor (0.82)
2. Database schema update (0.76)
3. Auth session changes (0.69)

Team Performance:
- 89% of commits were low/medium risk ✓
- Good test coverage maintained
- 3 commits needed rollback ⚠️

Recommendations:
- Focus on payment module stability
- Add more unit tests to auth
- Consider pair programming for critical changes
```

---

**Ready to use these workflows?** Just restart Claude Desktop and try any of these examples! 🚀

