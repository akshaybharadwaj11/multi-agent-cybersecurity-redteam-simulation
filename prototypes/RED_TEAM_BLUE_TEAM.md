# 🔴🔵 Red Team vs Blue Team Simulation Mode

## Overview

The **Red Team vs Blue Team** simulation mode is the core feature of this cybersecurity simulator. It implements a complete adversarial simulation where:

- **🔴 Red Team** (Attacker) generates realistic cyberattack scenarios
- **🔵 Blue Team** (Defender) detects, analyzes, and responds to attacks

## Architecture Flow

```
┌─────────────────────────────────────────────┐
│         🔴 RED TEAM AGENT                   │
│  • Generates attack scenarios               │
│  • Creates synthetic telemetry              │
│  • Simulates attacker behavior              │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│      🔵 BLUE TEAM DETECTION AGENT           │
│  • Analyzes telemetry                       │
│  • Detects security incidents               │
│  • Creates incident reports                 │
│  • Assigns severity scores                  │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│            📚 RAG AGENT                     │
│  • Retrieves security runbooks              │
│  • Gets threat intelligence                 │
│  • Finds similar past incidents             │
│  • Provides context for decisions           │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│        💡 REMEDIATION AGENT                 │
│  • Recommends defense actions               │
│  • Evaluates multiple options               │
│  • Considers operational impact             │
│  • Uses retrieved knowledge                 │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│         🤖 RL POLICY AGENT                  │
│  • Selects optimal action                   │
│  • Learns from outcomes                     │
│  • Balances exploration/exploitation        │
│  • Updates policy over time                 │
└─────────────────────────────────────────────┘
                   │
                   ▼
┌─────────────────────────────────────────────┐
│      ⚖️ ENVIRONMENT / SIMULATOR             │
│  • Simulates action outcomes                │
│  • Calculates rewards                       │
│  • Provides feedback                        │
│  • Updates state                            │
└─────────────────────────────────────────────┘
                   │
                   └───► Feedback Loop ───┐
                                          │
                                          ▼
                              RL Agent Updates Policy
```

## How to Use

### In the Dashboard

1. **Select Mode**: Choose "Red Team vs Blue Team" from the simulation mode selector
2. **Configure**: Set number of episodes and attack types
3. **Run**: Click "Run Simulation"
4. **Watch**: See the complete Red Team vs Blue Team interaction
5. **Analyze**: View results showing:
   - Red Team attack success
   - Blue Team detection rates
   - Defense effectiveness
   - RL learning progress

### Attack Types Supported

- **Phishing**: Email-based attacks with malicious attachments
- **Credential Misuse**: Brute force, password spraying
- **Lateral Movement**: RDP, SMB, credential dumping
- **Data Exfiltration**: Unauthorized data transfer
- **Malware Execution**: Malicious code execution
- **Privilege Escalation**: Gaining higher access levels

### Blue Team Response Actions

- **BLOCK_IP**: Block source IP addresses
- **LOCK_ACCOUNT**: Lock compromised accounts
- **KILL_PROCESS**: Terminate malicious processes
- **ISOLATE_HOST**: Isolate affected systems
- **NOTIFY_TEAM**: Alert security team
- **SCAN_SYSTEM**: Run security scans
- **RESET_CREDENTIALS**: Force password resets
- **QUARANTINE_FILE**: Quarantine malicious files

## Metrics Tracked

### Red Team Metrics
- Attack scenarios generated
- Attack types used
- Success rates
- Techniques employed (MITRE ATT&CK)

### Blue Team Metrics
- Detection rate
- False positive rate
- Time to detect
- Incident severity distribution

### Defense Metrics
- Successful containment rate
- Average response time
- Action effectiveness
- RL learning progress

## Learning Component

The RL Agent learns optimal defense strategies by:
- Trying different actions in similar situations
- Receiving rewards for successful defenses
- Penalties for failures and false positives
- Updating Q-values over time
- Balancing exploration vs exploitation

## Example Scenario

1. **Red Team**: Generates phishing attack with malicious Excel attachment
2. **Telemetry**: System logs show Excel spawning PowerShell
3. **Blue Team Detection**: Identifies suspicious process chain
4. **RAG**: Retrieves phishing response runbook
5. **Remediation**: Recommends blocking sender, quarantining file, resetting credentials
6. **RL Agent**: Selects ISOLATE_HOST action (learned from past successes)
7. **Environment**: Simulates outcome - attack contained successfully
8. **Reward**: +1.0 for successful defense
9. **RL Update**: Increases Q-value for ISOLATE_HOST in similar states

## Benefits

✅ **Realistic Training**: Simulates real-world attack/defense scenarios  
✅ **Adaptive Learning**: RL agent improves over time  
✅ **Knowledge Integration**: RAG provides real security knowledge  
✅ **Explainable**: Full audit trail of decisions  
✅ **Scalable**: Can run hundreds of episodes  

## Next Steps

1. Run a simulation in the dashboard
2. Observe Red Team attack generation
3. Watch Blue Team detection and response
4. Analyze RL learning progress
5. Experiment with different attack types
6. Compare defense strategies

**The complete Red Team vs Blue Team simulation is ready to use!** 🚀

