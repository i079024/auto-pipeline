# 🏗️ AI-Enhanced DevSecOps Pipeline - Architecture & Workflow

## Overview

This document provides visual representations of the system architecture, data flow, and component interactions.

---

## 🎯 System Architecture

### High-Level Architecture

```mermaid
graph TB
    subgraph "Developer Tools"
        DEV[Developer]
        GIT[Git Repository<br/>GitHub]
    end
    
    subgraph "CI/CD Pipeline"
        JENKINS[Jenkins<br/>:8080]
        SONAR[SonarQube<br/>:9000]
    end
    
    subgraph "AI Analysis Layer"
        N8N[n8n Workflow<br/>:5678]
        MCP[MCP HTTP Wrapper<br/>:3001]
        SPEC[Speculator Bot<br/>Risk Analysis]
        AICORE[SAP AI Core<br/>Claude Sonnet 4]
    end
    
    subgraph "Output"
        PR[GitHub PR<br/>with AI Analysis]
        EMAIL[Email Notification]
    end
    
    DEV -->|Push Code| GIT
    GIT -->|Webhook| JENKINS
    JENKINS -->|Build & Test| SONAR
    JENKINS -->|Trigger Analysis| N8N
    N8N -->|Risk Analysis| MCP
    N8N -->|Get Commit| GIT
    MCP -->|Local Analysis| SPEC
    MCP -->|AI Analysis| AICORE
    N8N -->|Create PR| PR
    N8N -->|Notify| EMAIL
    
    style AICORE fill:#e1f5ff
    style MCP fill:#fff3e0
    style N8N fill:#f3e5f5
    style JENKINS fill:#e8f5e9
```

---

## 🔄 Detailed Workflow Sequence

### Complete Pipeline Flow

```mermaid
sequenceDiagram
    participant Dev as Developer
    participant Git as GitHub
    participant Jen as Jenkins
    participant Son as SonarQube
    participant n8n as n8n Workflow
    participant MCP as MCP Wrapper
    participant Spec as Speculator Bot
    participant AI as SAP AI Core<br/>(Claude)
    
    Dev->>Git: Push commit
    Git->>Jen: Webhook trigger
    
    activate Jen
    Jen->>Jen: Checkout code
    Jen->>Jen: Run unit tests
    Jen->>Son: Quality scan
    Son-->>Jen: Quality report
    Jen->>n8n: POST webhook<br/>(commit data)
    deactivate Jen
    
    activate n8n
    n8n->>n8n: Extract build data
    
    par Parallel Analysis
        n8n->>MCP: Risk analysis request
        activate MCP
        MCP->>Spec: Analyze commit
        Spec-->>MCP: Risk metrics
        MCP-->>n8n: Risk report
        deactivate MCP
    and
        n8n->>Git: Fetch commit details
        Git-->>n8n: Code diff
    end
    
    n8n->>MCP: LLM analysis request<br/>(with code diff)
    activate MCP
    MCP->>AI: Send prompt
    activate AI
    AI-->>MCP: AI analysis
    deactivate AI
    MCP-->>n8n: Structured analysis
    deactivate MCP
    
    n8n->>n8n: Parse & format results
    
    alt Has Improvements
        n8n->>Git: Create branch
        n8n->>Git: Create PR
        Git-->>Dev: PR notification
    end
    
    n8n->>Dev: Email notification
    deactivate n8n
```

---

## 🏛️ Component Architecture

### MCP Server Architecture

```mermaid
classDiagram
    class MCPHTTPWrapper {
        +Flask app
        +port: 3001
        +analyze_code()
        +mcp_analyze()
        +health()
        -get_bot()
        -generate_llm_prompt()
    }
    
    class SpeculatorBot {
        +repo_path: str
        +config: dict
        +speculate(commit_hash)
        -analyze_changes()
        -assess_risk()
        -select_tests()
    }
    
    class ChangeAnalyzer {
        +analyze_diff()
        +get_changed_files()
        +calculate_complexity()
    }
    
    class RiskPredictor {
        +predict_risk()
        +calculate_score()
        +get_risk_factors()
    }
    
    class TestSelector {
        +select_tests()
        +prioritize_tests()
        +estimate_time()
    }
    
    class AICoreLLMClient {
        +config: dict
        +access_token: str
        +authenticate()
        +get_deployment_url()
        +analyze_with_llm()
    }
    
    MCPHTTPWrapper --> SpeculatorBot
    MCPHTTPWrapper --> AICoreLLMClient
    SpeculatorBot --> ChangeAnalyzer
    SpeculatorBot --> RiskPredictor
    SpeculatorBot --> TestSelector
    AICoreLLMClient --> SAP_AI_Core
    
    class SAP_AI_Core {
        <<external>>
        +Claude Sonnet 4
        +OAuth Authentication
        +Inference API
    }
```

---

## 📊 Data Flow Architecture

### Information Flow Through Pipeline

```mermaid
flowchart LR
    subgraph Input
        A[Commit Data]
        B[Code Diff]
        C[Build Metadata]
    end
    
    subgraph Processing
        D[Extract Data]
        E[Risk Analysis]
        F[AI Analysis]
        G[Format Results]
    end
    
    subgraph Output
        H[Risk Score]
        I[Recommendations]
        J[Test Suggestions]
        K[Security Fixes]
        L[GitHub PR]
    end
    
    A --> D
    B --> D
    C --> D
    
    D --> E
    D --> F
    
    E --> G
    F --> G
    
    G --> H
    G --> I
    G --> J
    G --> K
    
    H --> L
    I --> L
    J --> L
    K --> L
    
    style E fill:#ffecb3
    style F fill:#c8e6c9
    style L fill:#b3e5fc
```

---

## 🔌 Integration Points

### External System Connections

```mermaid
graph TB
    subgraph "Internal Systems"
        MCP[MCP Wrapper<br/>:3001]
        N8N[n8n<br/>:5678]
        JENKINS[Jenkins<br/>:8080]
        SONAR[SonarQube<br/>:9000]
    end
    
    subgraph "External Services"
        GITHUB[GitHub<br/>API]
        AICORE[SAP AI Core<br/>Claude API]
        EMAIL[SMTP Server]
    end
    
    subgraph "Authentication"
        GHTOKEN[GitHub Token]
        AITOKEN[AI Core OAuth]
        SMTPAUTH[SMTP Credentials]
    end
    
    N8N -->|REST API| MCP
    MCP -->|OAuth 2.0| AICORE
    N8N -->|Token Auth| GITHUB
    N8N -->|Basic Auth| EMAIL
    JENKINS -->|Webhook| N8N
    JENKINS -->|HTTP| SONAR
    
    GITHUB -.->|Uses| GHTOKEN
    AICORE -.->|Uses| AITOKEN
    EMAIL -.->|Uses| SMTPAUTH
    
    style AICORE fill:#e1f5ff
    style GITHUB fill:#f0f0f0
    style EMAIL fill:#fff9c4
```

---

## 🧩 n8n Workflow Architecture

### Workflow Node Structure

```mermaid
graph LR
    A[Webhook Trigger] --> B[Extract Data]
    B --> C[Speculator Analysis]
    C --> D[Fetch Git Commit]
    D --> E[LLM Analysis]
    E --> F[Parse Results]
    F --> G{Has Improvements?}
    G -->|Yes| H[Create Branch]
    H --> I[Create PR]
    I --> J[Send Email]
    G -->|No| J
    
    style A fill:#4caf50
    style C fill:#ff9800
    style E fill:#2196f3
    style I fill:#9c27b0
```

---

## 🔐 Security & Authentication Flow

### Authentication Architecture

```mermaid
sequenceDiagram
    participant N8N as n8n Workflow
    participant MCP as MCP Wrapper
    participant AI as SAP AI Core
    participant Git as GitHub API
    
    Note over N8N,Git: Authentication Setup
    
    N8N->>Git: Request with GitHub Token
    Git->>Git: Validate token
    Git-->>N8N: Authorized response
    
    MCP->>AI: Request OAuth token
    AI->>AI: Validate client credentials
    AI-->>MCP: Access token (expires 1h)
    
    MCP->>AI: API request + Bearer token
    AI->>AI: Validate token
    AI-->>MCP: API response
    
    Note over MCP,AI: Token refresh on expiry
    
    MCP->>AI: Refresh token request
    AI-->>MCP: New access token
```

---

## 📦 Deployment Architecture

### Production Deployment (SAP BTP)

```mermaid
graph TB
    subgraph "SAP BTP Cloud Foundry"
        subgraph "App Instance 1"
            MCP1[MCP Wrapper]
            N8N1[n8n]
        end
        
        subgraph "App Instance 2"
            MCP2[MCP Wrapper]
            N8N2[n8n]
        end
        
        LB[Load Balancer]
    end
    
    subgraph "SAP AI Core"
        AI[Claude Deployment]
    end
    
    subgraph "External"
        GIT[GitHub]
        JENKINS[Jenkins]
    end
    
    subgraph "Services"
        DB[(PostgreSQL)]
        REDIS[Redis Cache]
        LOGS[Logging Service]
    end
    
    JENKINS --> LB
    GIT --> LB
    LB --> MCP1
    LB --> MCP2
    LB --> N8N1
    LB --> N8N2
    
    MCP1 --> AI
    MCP2 --> AI
    N8N1 --> GIT
    N8N2 --> GIT
    
    MCP1 -.-> DB
    MCP2 -.-> DB
    MCP1 -.-> REDIS
    MCP2 -.-> REDIS
    
    MCP1 -.-> LOGS
    MCP2 -.-> LOGS
    N8N1 -.-> LOGS
    N8N2 -.-> LOGS
    
    style AI fill:#e1f5ff
    style LB fill:#fff3e0
```

---

## 🔄 State Machine

### Workflow Execution States

```mermaid
stateDiagram-v2
    [*] --> Triggered: Webhook received
    Triggered --> Extracting: Parse payload
    Extracting --> Analyzing: Data validated
    
    Analyzing --> RiskAnalysis: Run Speculator
    Analyzing --> FetchingCode: Get from GitHub
    
    RiskAnalysis --> AIAnalysis: Risk calculated
    FetchingCode --> AIAnalysis: Code retrieved
    
    AIAnalysis --> Parsing: AI response received
    Parsing --> Evaluating: Results structured
    
    Evaluating --> CreatingPR: Improvements found
    Evaluating --> Notifying: No improvements
    
    CreatingPR --> Notifying: PR created
    Notifying --> [*]: Email sent
    
    Analyzing --> Failed: Error occurred
    AIAnalysis --> Failed: AI error
    Failed --> [*]: Error logged
```

---

## 🧪 Testing Flow

### Test Execution Path

```mermaid
flowchart TD
    Start([Test Start]) --> Input[Prepare Test Data]
    Input --> API[Test API Endpoint]
    
    API --> Check1{Connection OK?}
    Check1 -->|No| Fail1[Connection Failed]
    Check1 -->|Yes| Auth[Test Authentication]
    
    Auth --> Check2{Auth OK?}
    Check2 -->|No| Fail2[Auth Failed]
    Check2 -->|Yes| Analysis[Test Analysis]
    
    Analysis --> Check3{Analysis OK?}
    Check3 -->|No| Fail3[Analysis Failed]
    Check3 -->|Yes| Validate[Validate Response]
    
    Validate --> Check4{Valid Format?}
    Check4 -->|No| Fail4[Invalid Response]
    Check4 -->|Yes| Success[Test Passed]
    
    Fail1 --> Report[Generate Report]
    Fail2 --> Report
    Fail3 --> Report
    Fail4 --> Report
    Success --> Report
    
    Report --> End([Test End])
    
    style Success fill:#4caf50
    style Fail1 fill:#f44336
    style Fail2 fill:#f44336
    style Fail3 fill:#f44336
    style Fail4 fill:#f44336
```

---

## 📈 Performance & Monitoring

### System Monitoring Points

```mermaid
graph TB
    subgraph "Monitoring Points"
        M1[API Response Time]
        M2[AI Core Latency]
        M3[GitHub API Rate]
        M4[Workflow Success Rate]
        M5[Error Count]
    end
    
    subgraph "Data Collection"
        L1[Application Logs]
        L2[Metrics Exporter]
        L3[Health Checks]
    end
    
    subgraph "Visualization"
        D1[Grafana Dashboard]
        D2[Alert Manager]
        D3[Log Aggregator]
    end
    
    M1 --> L2
    M2 --> L2
    M3 --> L2
    M4 --> L2
    M5 --> L1
    
    L1 --> D3
    L2 --> D1
    L3 --> D2
    
    D1 --> Alert{Threshold<br/>Exceeded?}
    Alert -->|Yes| D2
    
    style Alert fill:#ff9800
    style D2 fill:#f44336
```

---

## 🗄️ Data Models

### Core Data Structures

```mermaid
classDiagram
    class CommitData {
        +string commitSHA
        +string branch
        +string author
        +string repository
        +string sonarURL
        +int buildNumber
        +string jenkinsURL
    }
    
    class RiskAnalysis {
        +float deploymentRiskScore
        +string riskLevel
        +ChangeSummary changeSummary
        +RiskAnalysis riskAnalysis
        +TestSelection testSelection
    }
    
    class ChangeSummary {
        +int filesChanged
        +int linesAdded
        +int linesRemoved
        +int criticalFiles
    }
    
    class AIAnalysis {
        +string changeIntroduced
        +GapAnalysis[] gapAnalysis
        +TestCoverage[] testCoverage
        +SecurityFix[] securityFixes
    }
    
    class GapAnalysis {
        +string category
        +string concern
        +string recommendation
    }
    
    class TestCoverage {
        +string priority
        +string suggestion
        +string reasoning
    }
    
    class SecurityFix {
        +string type
        +string priority
        +string action
    }
    
    class PROutput {
        +string newBranchName
        +string prTitle
        +string prBody
        +string baseBranch
        +string commitSHA
        +bool hasImprovements
    }
    
    CommitData --> RiskAnalysis
    CommitData --> AIAnalysis
    RiskAnalysis --> ChangeSummary
    AIAnalysis --> GapAnalysis
    AIAnalysis --> TestCoverage
    AIAnalysis --> SecurityFix
    RiskAnalysis --> PROutput
    AIAnalysis --> PROutput
```

---

## 🌐 Network Architecture

### Port and Protocol Map

```mermaid
graph LR
    subgraph "Public Internet"
        EXT[External Users]
    end
    
    subgraph "Network Layer"
        FW[Firewall]
        PROXY[Corporate Proxy]
    end
    
    subgraph "Services"
        J[Jenkins<br/>:8080 HTTP]
        N[n8n<br/>:5678 HTTP]
        M[MCP<br/>:3001 HTTP]
        S[SonarQube<br/>:9000 HTTP]
    end
    
    subgraph "External APIs"
        G[GitHub<br/>HTTPS:443]
        A[AI Core<br/>HTTPS:443]
    end
    
    EXT -->|HTTPS| FW
    FW -->|HTTP| J
    FW -->|HTTP| N
    
    J -->|HTTP| N
    N -->|HTTP| M
    J -->|HTTP| S
    
    N -.->|HTTPS| PROXY
    M -.->|HTTPS| PROXY
    PROXY -.->|HTTPS| G
    PROXY -.->|HTTPS| A
    
    style FW fill:#ff9800
    style PROXY fill:#ffeb3b
```

---

## 📝 Summary

### Key Architecture Patterns

1. **Microservices**: Each component (Jenkins, n8n, MCP, SonarQube) is independently deployable
2. **Event-Driven**: Webhook-based triggers drive the workflow
3. **API Gateway**: n8n acts as orchestrator for all services
4. **Separation of Concerns**: Analysis, AI, and automation are separated
5. **Scalability**: Can scale horizontally on SAP BTP
6. **Security**: OAuth 2.0 and token-based authentication throughout

### Technology Stack

- **CI/CD**: Jenkins, Git
- **Orchestration**: n8n
- **Analysis**: Python (Speculator Bot)
- **AI**: SAP AI Core (Claude Sonnet 4)
- **Quality**: SonarQube
- **Container**: Docker
- **Cloud**: SAP BTP (Cloud Foundry / Kyma)

---

**All diagrams are in Mermaid format and can be viewed in:**
- GitHub (native support)
- VS Code (with Mermaid extension)
- Mermaid Live Editor: https://mermaid.live

