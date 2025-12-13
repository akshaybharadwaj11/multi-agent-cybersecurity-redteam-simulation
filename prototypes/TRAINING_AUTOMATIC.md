# 🤖 Automatic Training - Backend Only

## Overview

Training now happens **automatically in the backend** - no UI controls needed!

## How It Works

### Automatic Training Logic

When you run a simulation:
1. **Training Phase** (automatic, backend):
   - Uses 20% of total episodes for training
   - Minimum: 3 episodes
   - Maximum: 20 episodes
   - Example: 20 total episodes → 4 training + 16 simulation

2. **Simulation Phase**:
   - Remaining episodes run with trained RL agent
   - Better performance from trained agent
   - Continues learning during simulation

### Examples

```bash
# 5 episodes total
# → 3 training + 2 simulation

# 20 episodes total  
# → 4 training + 16 simulation

# 50 episodes total
# → 10 training + 40 simulation

# 100 episodes total
# → 20 training (max) + 80 simulation
```

## Usage

### Command Line:
```bash
# Training happens automatically
python3 run_simulation.py --episodes 20

# Quick test (3 training + 2 simulation)
python3 run_simulation.py --quick-test

# Skip training if needed
python3 run_simulation.py --no-train --episodes 10
```

### Dashboard:
- Just set "Number of Episodes"
- Training happens automatically in backend
- No training controls in UI
- See training progress in logs

## Benefits

✅ **Simpler UI** - No training controls needed  
✅ **Automatic** - Always optimal training amount  
✅ **Transparent** - Training shown in logs  
✅ **Flexible** - Scales with episode count  

## Training Output

You'll see in logs:
```
🤖 Automatic Training Phase: 4 episodes (backend)
Training Progress: Episode 2/4
  Epsilon: 0.0995, States: 3
✅ Training complete! RL agent trained on 4 episodes
   Final epsilon: 0.0990
   States explored: 5
   Q-value updates: 4

Training complete. Starting main simulation: 16 episodes...
```

## Skip Training

If you want to skip training:
```bash
python3 run_simulation.py --no-train --episodes 10
```

**Training is now fully automatic and happens in the backend!** 🚀

