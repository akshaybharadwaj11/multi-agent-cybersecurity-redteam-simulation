# 🤖 RL Agent Training Guide

## Overview

The RL (Reinforcement Learning) agent needs to be trained before it can effectively select optimal defense actions. Training allows the agent to:

- Explore different actions in various situations
- Learn which actions work best for different attack types
- Build a Q-table of state-action values
- Balance exploration vs exploitation

## Training Process

### Automatic Training

By default, training happens automatically when running simulations:

```bash
# Training happens automatically (10 episodes) before main simulation
python cyber_defense_simulator/main_entry.py --episodes 20
```

### Manual Training Control

```bash
# Explicitly train first
python cyber_defense_simulator/main_entry.py --train --training-episodes 15 --episodes 20

# Skip training (use untrained agent)
python cyber_defense_simulator/main_entry.py --no-train --episodes 10

# Quick test (minimal training)
python cyber_defense_simulator/main_entry.py --quick-test
```

## Training Phases

### Phase 1: Training (Exploration)
- RL agent explores different actions
- High epsilon (exploration rate)
- Learns Q-values for state-action pairs
- Builds knowledge base

### Phase 2: Simulation (Exploitation)
- RL agent uses learned knowledge
- Lower epsilon (more exploitation)
- Selects best-known actions
- Continues learning from new experiences

## Training Parameters

### Epsilon (Exploration Rate)
- **Initial**: 0.1 (10% random exploration)
- **Decay**: 0.995 per episode
- **Minimum**: 0.01 (1% exploration)

### Learning Rate
- **Default**: 0.1
- Controls how fast Q-values update
- Higher = faster learning, less stable
- Lower = slower learning, more stable

### Discount Factor
- **Default**: 0.95
- How much future rewards matter
- Higher = long-term thinking
- Lower = short-term focus

## Training Metrics

During training, you'll see:
- **States Explored**: Number of unique situations encountered
- **Q-value Updates**: Number of learning updates
- **Epsilon**: Current exploration rate
- **Average Q-value**: Average expected reward

## Best Practices

### For Quick Testing
```bash
--quick-test  # 3 training episodes, 5 simulation episodes
```

### For Development
```bash
--training-episodes 10 --episodes 20  # Balanced
```

### For Production
```bash
--training-episodes 50 --episodes 100  # Thorough training
```

### For Specific Attack Types
```bash
--train --training-episodes 15 --attack-types phishing credential_misuse
```

## Training Output

```
🤖 Training RL Agent: 10 episodes
Training Progress: Episode 5/10
  Epsilon: 0.0975, States: 8
Training Progress: Episode 10/10
  Epsilon: 0.0951, States: 12
✅ Training complete! RL agent trained on 10 episodes
   Final epsilon: 0.0951
   States explored: 12
   Q-value updates: 10
```

## After Training

The trained agent will:
- Make better action selections
- Have higher success rates
- Show improved learning curves
- Adapt faster to new situations

## Monitoring Training

Watch for:
- ✅ Increasing states explored
- ✅ Decreasing epsilon (less exploration needed)
- ✅ Improving average Q-values
- ✅ Better action selection over time

## Troubleshooting

**Agent not learning?**
- Increase training episodes
- Check reward function
- Verify state representation

**Too much exploration?**
- Increase epsilon decay
- Lower initial epsilon

**Too little exploration?**
- Decrease epsilon decay
- Raise initial epsilon

## Next Steps

After training:
1. Run simulations to see improved performance
2. Analyze learning curves
3. Adjust training parameters if needed
4. Save trained agent for reuse

**Training is essential for optimal RL agent performance!** 🚀

