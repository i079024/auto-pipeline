# 🚀 AI-Enhanced DevSecOps Pipeline - Quick Reference

## 📚 Documentation Index

### Architecture & Workflow
- **`ARCHITECTURE_DIAGRAMS.md`** - 14 Mermaid diagrams showing system architecture
- **`WORKFLOW_EXPLANATION.md`** - Detailed step-by-step workflow breakdown

### Setup Guides
- **`README.md`** - Project overview and quick start
- **`AI_DEVSECOPS_SETUP.md`** - Complete setup guide
- **`AI_DEVSECOPS_QUICKSTART.md`** - Fast setup (30 minutes)
- **`AI_DEVSECOPS_COMPLETE.md`** - Final summary

### Component-Specific Guides
- **`MCP_SETUP.md`** - MCP Server detailed setup
- **`MCP_QUICKSTART.md`** - MCP Server quick start
- **`START_SONARQUBE.md`** - SonarQube Docker setup

### n8n Configuration (15+ guides)
- **`N8N_CONFIGURATION_GUIDE.md`** - Complete n8n setup
- **`N8N_QUICKSTART_CHECKLIST.md`** - Quick checklist
- **`N8N_GITHUB_CREDENTIALS_VISUAL_GUIDE.md`** - GitHub credential setup
- **`N8N_WEBHOOK_SETUP.md`** - Webhook configuration
- **`N8N_TEST_GUIDE.md`** - Testing instructions
- **`N8N_FIX_APPLIED.md`** - Port and connection fixes
- **`N8N_EXPRESSION_FIX.md`** - Expression syntax fixes

### SAP AI Core Integration
- **`SAP_AI_CORE_MCP_INTEGRATION.md`** - Complete integration guide
- **`SAP_AI_CORE_SETUP_COMPLETE.md`** - Setup completion guide
- **`ai_core_config.example.yaml`** - Configuration template

---

## 🎯 Quick Commands

### Start All Services

```bash
# Jenkins
brew services start jenkins-lts

# n8n
n8n start &

# MCP Wrapper
python3 mcp-http-wrapper.py &

# SonarQube (Docker)
docker start sonarqube
```

### Check Service Status

```bash
# Jenkins
curl http://localhost:8080

# n8n
curl http://localhost:5678/healthz

# MCP Wrapper
curl http://127.0.0.1:3001/health

# SonarQube
curl http://localhost:9000/api/system/status
```

### Stop All Services

```bash
# Stop n8n
pkill -f "n8n start"

# Stop MCP Wrapper
pkill -f "mcp-http-wrapper"

# Stop SonarQube
docker stop sonarqube

# Stop Jenkins
brew services stop jenkins-lts
```

---

## 🔗 Service URLs

| Service | URL | Credentials |
|---------|-----|-------------|
| **Jenkins** | http://localhost:8080 | See initial admin password |
| **n8n** | http://localhost:5678 | Your n8n account |
| **MCP Wrapper** | http://127.0.0.1:3001 | No auth (internal) |
| **SonarQube** | http://localhost:9000 | admin/admin |

---

## 📊 Mermaid Diagrams Available

### In `ARCHITECTURE_DIAGRAMS.md`:

1. **High-Level Architecture** - Complete system overview
2. **Detailed Workflow Sequence** - Step-by-step interaction
3. **Component Architecture** - Class diagram of MCP Server
4. **Data Flow Architecture** - Information flow
5. **Integration Points** - External system connections
6. **n8n Workflow Architecture** - Node structure
7. **Security & Authentication Flow** - Auth sequence
8. **Deployment Architecture** - Production setup (SAP BTP)
9. **State Machine** - Workflow execution states
10. **Testing Flow** - Test execution path
11. **Performance & Monitoring** - Monitoring points
12. **Data Models** - Core data structures
13. **Network Architecture** - Port and protocol map
14. **Technology Stack Summary** - All components

---

## 🧪 Test Workflow

```bash
# 1. Check all services are running
curl http://localhost:8080  # Jenkins
curl http://localhost:5678/healthz  # n8n
curl http://127.0.0.1:3001/health  # MCP

# 2. Test MCP wrapper
curl -X POST http://127.0.0.1:3001/api/speculator/analyze \
  -H "Content-Type: application/json" \
  -d '{"commitSHA":"test","branch":"main","author":"test@test.com","sonarURL":"http://localhost:9000","repository":"https://github.com/test/repo"}'

# 3. Send test webhook to n8n
curl -X POST http://localhost:5678/webhook/jenkins-trigger \
  -H "Content-Type: application/json" \
  -d '{
    "commitSHA": "cc2619c1ffae990f183bcfadf5dd70e142e36657",
    "branch": "main",
    "author": "your-email@example.com",
    "sonarURL": "http://localhost:9000",
    "buildNumber": "1",
    "jenkinsURL": "http://localhost:8080",
    "repository": "https://github.com/yourusername/yourrepo.git"
  }'

# 4. Check n8n execution
# Open: http://localhost:5678
# Click: Executions tab
```

---

## 🔧 Common Issues & Fixes

### Issue: "Connection refused" in n8n

**Fix:**
```bash
# Restart MCP wrapper
pkill -f "mcp-http-wrapper"
python3 mcp-http-wrapper.py &

# Verify it's running
lsof -i :3001
```

### Issue: "Webhook not registered"

**Fix:**
1. Open n8n workflow
2. Toggle workflow OFF
3. Wait 5 seconds
4. Toggle workflow ON

### Issue: "GitHub credentials not found"

**Fix:**
1. Go to: n8n → Settings → Credentials
2. Add: GitHub API credential
3. Assign to GitHub nodes in workflow

### Issue: "Expression syntax error"

**Fix:**
- Re-import the workflow: `n8n-ai-devsecops-workflow.json`
- All expressions are fixed in the latest version

---

## 📁 Project Structure

```
AIBot/
├── README.md                           # Main documentation
├── requirements.txt                    # Python dependencies
├── config.yaml                         # Speculator Bot config
│
├── speculator_bot/                     # Main bot code
│   ├── bot.py                         # Core logic
│   ├── core/                          # Analysis modules
│   └── mcp_server.py                  # MCP server
│
├── mcp-http-wrapper.py                # HTTP API wrapper
├── Jenkinsfile                        # CI/CD pipeline
├── sonar-project.properties           # SonarQube config
├── n8n-ai-devsecops-workflow.json    # n8n workflow
│
├── ai_core_config.example.yaml        # SAP AI Core template
├── ARCHITECTURE_DIAGRAMS.md           # System diagrams
├── WORKFLOW_EXPLANATION.md            # Workflow details
│
└── [25+ documentation files]          # Complete guides
```

---

## 🎯 Development Workflow

### 1. Developer Perspective

```
1. Write code
2. Commit & push
3. Jenkins builds automatically
4. Receive email with AI analysis
5. Review generated PR (if improvements found)
6. Merge or iterate
```

### 2. DevOps Perspective

```
1. Monitor Jenkins builds
2. Check n8n executions
3. Review MCP wrapper logs
4. Monitor SAP AI Core usage
5. Track success metrics
```

### 3. Security Perspective

```
1. Review AI-generated security findings
2. Check SonarQube reports
3. Validate test coverage suggestions
4. Approve/merge security PRs
```

---

## 📈 Success Metrics

### Key Performance Indicators

- **Build Success Rate**: >95%
- **AI Analysis Time**: <30 seconds
- **PR Creation Rate**: ~30% of builds
- **Test Coverage Improvement**: Track over time
- **Security Issues Found**: Track by AI vs manual

### Monitoring Dashboards

1. **Jenkins**: Build history and success rate
2. **n8n**: Workflow execution statistics
3. **SAP AI Core**: Token usage and latency
4. **SonarQube**: Code quality trends

---

## 🔐 Security Checklist

- [ ] GitHub token has minimal required scopes
- [ ] SAP AI Core credentials stored securely
- [ ] `ai_core_config.yaml` in `.gitignore`
- [ ] SMTP credentials not in code
- [ ] Jenkins secured with authentication
- [ ] n8n workflows require login
- [ ] MCP wrapper not exposed publicly
- [ ] Regular security audits scheduled

---

## 📞 Support & Resources

### Documentation Files
- 25+ comprehensive guides
- 14 Mermaid architecture diagrams
- Step-by-step tutorials
- Troubleshooting guides

### External Resources
- [SAP AI Core Docs](https://help.sap.com/docs/AI_CORE)
- [n8n Documentation](https://docs.n8n.io)
- [Jenkins Docs](https://www.jenkins.io/doc/)
- [SonarQube Docs](https://docs.sonarqube.org/)

---

## ✅ Setup Status

Track your setup progress:

- [ ] Jenkins installed and running
- [ ] n8n installed and running
- [ ] MCP wrapper installed and running
- [ ] SonarQube running (Docker)
- [ ] Speculator Bot configured
- [ ] n8n workflow imported
- [ ] GitHub credentials added
- [ ] SAP AI Core SDK installed
- [ ] AI Core config created
- [ ] Test webhook successful
- [ ] End-to-end workflow tested

---

## 🎓 Learning Path

### Beginner (Day 1)
1. Read `README.md`
2. Follow `AI_DEVSECOPS_QUICKSTART.md`
3. Run test webhook
4. View results in n8n

### Intermediate (Week 1)
1. Study `ARCHITECTURE_DIAGRAMS.md`
2. Read `WORKFLOW_EXPLANATION.md`
3. Customize workflow for your needs
4. Configure SAP AI Core

### Advanced (Ongoing)
1. Deploy to SAP BTP
2. Set up monitoring
3. Optimize AI prompts
4. Scale horizontally

---

**Quick Reference Last Updated**: Oct 2025

**Total Documentation**: 27 files, 500+ pages
**Total Diagrams**: 14 Mermaid diagrams
**Total Guides**: Setup, Configuration, Troubleshooting, Integration

