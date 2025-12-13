"""
Streamlit Dashboard for Cyber Defense Simulator
Visualizes simulation results and agent performance

Run with: streamlit run dashboard/app.py
"""

import streamlit as st
import plotly.graph_objects as go
import plotly.express as px
import pandas as pd
import json
from pathlib import Path
import sys
import logging

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

# Setup logging for dashboard simulations
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('simulation.log', mode='a')  # Append mode
    ],
    force=True  # Override any existing configuration
)

# Import with error handling
API_AVAILABLE = False
DIRECT_MODE = False
ATTACK_TYPE_AVAILABLE = False

# Try to import API client
try:
    from cyber_defense_simulator.api.client import SimulatorAPIClient
    API_AVAILABLE = True
except ImportError:
    API_AVAILABLE = False

# Always try to import direct mode dependencies
try:
    from cyber_defense_simulator.core.orchestrator import CyberDefenseOrchestrator
    from cyber_defense_simulator.core.data_models import AttackType
    DIRECT_MODE = True
    ATTACK_TYPE_AVAILABLE = True
except ImportError as e:
    DIRECT_MODE = False
    ATTACK_TYPE_AVAILABLE = False
    AttackType = None

# Check if we have at least one mode available
IMPORTS_OK = API_AVAILABLE or DIRECT_MODE

# If neither mode is available, we'll show an error in the main function


# Page configuration
st.set_page_config(
    page_title="Cyber Defense Simulator Dashboard",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)


def load_results(results_dir: Path):
    """Load simulation results from directory"""
    try:
        # Load metrics
        with open(results_dir / "metrics.json") as f:
            metrics = json.load(f)
        
        # Load episodes
        with open(results_dir / "episodes.json") as f:
            episodes = json.load(f)
        
        return metrics, episodes
    except Exception as e:
        st.error(f"Error loading results: {e}")
        return None, None


def plot_reward_history(metrics):
    """Plot reward over episodes"""
    if not metrics.get('reward_history'):
        return None
    
    fig = go.Figure()
    
    # Raw rewards
    fig.add_trace(go.Scatter(
        y=metrics['reward_history'],
        mode='lines',
        name='Episode Reward',
        line=dict(color='lightblue', width=1),
        opacity=0.5
    ))
    
    # Moving average
    window = min(10, len(metrics['reward_history']) // 4)
    if window > 1:
        rewards_series = pd.Series(metrics['reward_history'])
        moving_avg = rewards_series.rolling(window=window).mean()
        
        fig.add_trace(go.Scatter(
            y=moving_avg,
            mode='lines',
            name=f'{window}-Episode Moving Average',
            line=dict(color='blue', width=3)
        ))
    
    fig.update_layout(
        title="Learning Progress: Reward Over Time",
        xaxis_title="Episode",
        yaxis_title="Reward",
        hovermode='x unified',
        height=400
    )
    
    return fig


def plot_action_distribution(metrics):
    """Plot action selection distribution"""
    if not metrics.get('action_distribution'):
        return None
    
    actions = list(metrics['action_distribution'].keys())
    counts = list(metrics['action_distribution'].values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=actions,
            y=counts,
            text=counts,
            textposition='auto',
            marker_color='indianred'
        )
    ])
    
    fig.update_layout(
        title="Remediation Action Distribution",
        xaxis_title="Action",
        yaxis_title="Count",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig


def plot_attack_distribution(metrics):
    """Plot attack type distribution"""
    if not metrics.get('attack_distribution'):
        return None
    
    attacks = list(metrics['attack_distribution'].keys())
    counts = list(metrics['attack_distribution'].values())
    
    fig = go.Figure(data=[
        go.Bar(
            x=attacks,
            y=counts,
            text=counts,
            textposition='auto',
            marker_color='crimson'
        )
    ])
    
    fig.update_layout(
        title="Attack Type Distribution",
        xaxis_title="Attack Type",
        yaxis_title="Count",
        height=400,
        xaxis_tickangle=-45
    )
    
    return fig


def plot_success_rate_by_attack(episodes):
    """Plot success rate by attack type"""
    if not episodes:
        return None
    
    df = pd.DataFrame(episodes)
    
    # Group by attack type
    success_by_type = df.groupby('attack_type').agg({
        'success': ['sum', 'count', 'mean']
    }).reset_index()
    
    success_by_type.columns = ['attack_type', 'successful', 'total', 'success_rate']
    success_by_type['success_rate'] = success_by_type['success_rate'] * 100
    
    fig = go.Figure(data=[
        go.Bar(
            x=success_by_type['attack_type'],
            y=success_by_type['success_rate'],
            text=success_by_type['success_rate'].round(1).astype(str) + '%',
            textposition='auto',
            marker_color='lightgreen'
        )
    ])
    
    fig.update_layout(
        title="Defense Success Rate by Attack Type",
        xaxis_title="Attack Type",
        yaxis_title="Success Rate (%)",
        height=400
    )
    
    return fig


def plot_severity_distribution(episodes):
    """Plot incident severity distribution"""
    if not episodes:
        return None
    
    df = pd.DataFrame(episodes)
    severity_counts = df['severity'].value_counts()
    
    fig = go.Figure(data=[
        go.Pie(
            labels=severity_counts.index,
            values=severity_counts.values,
            hole=0.3,
            marker_colors=['red', 'orange', 'yellow', 'lightgreen']
        )
    ])
    
    fig.update_layout(
        title="Incident Severity Distribution",
        height=400
    )
    
    return fig


def main():
    """Main dashboard function"""
    
    # Check imports - need at least one mode
    if not IMPORTS_OK:
        st.title("🛡️ Cyber Defense Simulator Dashboard")
        st.error("❌ Dependencies not installed!")
        st.info("Please install dependencies:")
        st.code("pip install -r requirements.txt", language="bash")
        st.stop()
    
    # Show mode indicator
    if API_AVAILABLE and DIRECT_MODE:
        st.sidebar.info("🔌 API mode available (will fallback to direct if API not running)")
    elif DIRECT_MODE:
        st.sidebar.info("⚙️ Direct mode (API not available)")
    elif API_AVAILABLE:
        st.sidebar.info("🔌 API mode only (direct mode dependencies missing)")
    
    # Title with mode indicator
    st.title("🛡️ Cyber Defense Simulator Dashboard")
    st.markdown("**Red Team vs Blue Team Cybersecurity Simulation**")
    st.markdown("---")
    
    # Red Team vs Blue Team Flow Visualization
    st.markdown("### 🔄 Red Team vs Blue Team Flow")
    flow_col1, flow_col2, flow_col3, flow_col4, flow_col5, flow_col6 = st.columns(6)
    
    with flow_col1:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #fee; border-radius: 10px;'>
        <h4>🔴 Red Team</h4>
        <p>Generates Attacks</p>
        </div>
        """, unsafe_allow_html=True)
    
    with flow_col2:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #eef; border-radius: 10px;'>
        <h4>🔵 Detection</h4>
        <p>Finds Incidents</p>
        </div>
        """, unsafe_allow_html=True)
    
    with flow_col3:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #efe; border-radius: 10px;'>
        <h4>📚 RAG</h4>
        <p>Retrieves Knowledge</p>
        </div>
        """, unsafe_allow_html=True)
    
    with flow_col4:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #ffe; border-radius: 10px;'>
        <h4>💡 Remediation</h4>
        <p>Recommends Actions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with flow_col5:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #fef; border-radius: 10px;'>
        <h4>🤖 RL Agent</h4>
        <p>Selects Action</p>
        </div>
        """, unsafe_allow_html=True)
    
    with flow_col6:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: #eee; border-radius: 10px;'>
        <h4>⚖️ Environment</h4>
        <p>Feedback Loop</p>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Info box about the system
    with st.expander("ℹ️ About This Simulation", expanded=False):
        st.markdown("""
        ### 🎮 Simulation Modes
        
        **Red Team vs Blue Team (Default)**
        - 🔴 **Red Team Agent**: Generates realistic cyberattack scenarios
        - 🔵 **Blue Team Detection**: AI-powered incident detection from telemetry
        - 📚 **RAG Agent**: Retrieves security runbooks and threat intelligence
        - 💡 **Remediation Agent**: Recommends defense actions
        - 🤖 **RL Policy Agent**: Learns optimal defense strategies
        - ⚖️ **Environment**: Simulates outcomes and provides feedback
        
        ### 🔄 How It Works
        1. Red Team generates attack scenarios (phishing, credential misuse, lateral movement, etc.)
        2. System generates synthetic telemetry (logs, network traffic, process activity)
        3. Blue Team Detection Agent analyzes telemetry and creates incident reports
        4. RAG Agent retrieves relevant security knowledge and runbooks
        5. Remediation Agent recommends response actions
        6. RL Agent selects optimal action based on learned policies
        7. Environment simulates outcome and provides reward feedback
        8. RL Agent updates its policy for future decisions
        
        ### 📊 What You'll See
        - Attack scenarios and telemetry generation
        - Incident detection and severity scoring
        - Retrieved security knowledge and runbooks
        - Recommended remediation actions
        - RL agent decisions and learning progress
        - Success rates, rewards, and performance metrics
        """)
    
    # Sidebar
    st.sidebar.title("Controls")
    
    # Option 1: Load existing results
    st.sidebar.subheader("Load Results")
    results_path = st.sidebar.text_input(
        "Results Directory",
        value="./results"
    )
    
    if st.sidebar.button("Load Results"):
        results_dir = Path(results_path)
        if results_dir.exists():
            # Find latest results
            subdirs = [d for d in results_dir.iterdir() if d.is_dir()]
            if subdirs:
                latest = max(subdirs, key=lambda x: x.stat().st_mtime)
                st.session_state['results_dir'] = latest
                st.sidebar.success(f"Loaded: {latest.name}")
            else:
                st.sidebar.error("No results found")
        else:
            st.sidebar.error("Directory not found")
    
    # Option 2: Run new simulation
    st.sidebar.subheader("Run New Simulation")
    
    # Simulation Mode Selector
    simulation_mode = st.sidebar.radio(
        "🎮 Simulation Mode",
        options=["Red Team vs Blue Team", "Training Mode", "Custom"],
        help="Red Team vs Blue Team: Full adversarial simulation with all agents. Training happens automatically in the backend."
    )
    
    num_episodes = st.sidebar.slider(
        "Number of Episodes",
        min_value=5,
        max_value=100,
        value=20,
        step=5,
        help="Total episodes (includes automatic training phase)"
    )
    
    # Attack types selector
    if ATTACK_TYPE_AVAILABLE and AttackType:
        attack_type_options = [at.value for at in AttackType]
    else:
        # Fallback options if AttackType not available
        attack_type_options = ["phishing", "credential_misuse", "lateral_movement", "data_exfiltration"]
    
    attack_types = st.sidebar.multiselect(
        "Attack Types (empty = all)",
        options=attack_type_options,
        default=[]
    )
    
    # Show mode-specific info
    if simulation_mode == "Red Team vs Blue Team":
        st.sidebar.info("🔴 Red Team: Generates attacks\n🔵 Blue Team: Detects & responds\n🤖 RL Agent: Learns optimal defense")
    elif simulation_mode == "Training Mode":
        st.sidebar.info("📚 Focused training with specific scenarios")
    
    if st.sidebar.button("🚀 Run Simulation", type="primary"):
        try:
            with st.spinner("Running simulation..."):
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Use API if available, otherwise direct mode
                use_api_mode = False
                api_client = None
                
                if API_AVAILABLE:
                    # Try API mode first
                    status_text.info("🔌 Connecting to API backend...")
                    api_client = SimulatorAPIClient()
                    
                    # Check API health
                    if api_client.health_check():
                        use_api_mode = True
                        status_text.success("✅ Connected to API backend")
                    else:
                        # API not available, fall back to direct mode
                        status_text.warning("⚠️ API server not available. Using direct mode...")
                        api_client.close()
                        api_client = None
                
                if use_api_mode and api_client:
                    # API mode
                    # Show simulation mode info
                    if simulation_mode == "Red Team vs Blue Team":
                        status_text.info("🔴 Red Team generating attacks... 🔵 Blue Team preparing defense...")
                    
                    # Start simulation via API
                    progress_bar.progress(10)
                    response = api_client.run_simulation(
                        num_episodes=num_episodes,
                        attack_types=attack_types,
                        simulation_mode=simulation_mode
                    )
                    
                    simulation_id = response["simulation_id"]
                    status_text.info(f"🚀 Simulation {simulation_id} started. Waiting for completion...")
                    progress_bar.progress(30)
                    
                    # Wait for completion with progress updates
                    try:
                        results = api_client.wait_for_completion(simulation_id, poll_interval=2.0)
                        progress_bar.progress(100)
                        
                        # Store results in session state
                        output_dir = results.get('output_dir')
                        if output_dir:
                            st.session_state['results_dir'] = Path(output_dir)
                        st.session_state['metrics'] = results
                        st.session_state['simulation_mode'] = results.get('simulation_mode', simulation_mode)
                        st.session_state['simulation_id'] = simulation_id
                        
                        status_text.success(f"✅ Simulation complete! Mode: {st.session_state['simulation_mode']}")
                        
                    except TimeoutError:
                        st.warning("⏳ Simulation is taking longer than expected. Results will be available when complete.")
                        st.session_state['simulation_id'] = simulation_id
                        status_text.info(f"Simulation {simulation_id} is still running. Check back later.")
                    
                    api_client.close()
                    
                elif DIRECT_MODE:
                    # Direct mode (fallback)
                    status_text.info("⚙️ Running in direct mode...")
                    
                    # Log simulation start
                    logger = logging.getLogger(__name__)
                    logger.info("="*80)
                    logger.info(f"Dashboard: Starting simulation - {num_episodes} episodes, mode: {simulation_mode}")
                    logger.info("="*80)
                    
                    # Initialize orchestrator
                    try:
                        logger.info("Initializing orchestrator...")
                        orchestrator = CyberDefenseOrchestrator()
                        logger.info("Orchestrator initialized successfully")
                    except ValueError as e:
                        logger.error(f"Configuration Error: {e}")
                        st.error(f"❌ Configuration Error: {e}")
                        st.info("Please check your .env file and ensure OPENAI_API_KEY is set correctly.")
                        st.stop()
                    except Exception as e:
                        logger.error(f"Error initializing orchestrator: {e}", exc_info=True)
                        st.error(f"❌ Error initializing orchestrator: {e}")
                        st.info("Please check your dependencies and configuration.")
                        st.stop()
                    
                    # Convert attack types
                    attack_type_list = None
                    if attack_types and ATTACK_TYPE_AVAILABLE and AttackType:
                        try:
                            attack_type_list = [AttackType(at) for at in attack_types]
                            logger.info(f"Attack types: {[at.value for at in attack_type_list]}")
                        except Exception as e:
                            logger.warning(f"Error parsing attack types: {e}. Using all attack types.")
                            st.warning(f"⚠️ Error parsing attack types: {e}. Using all attack types.")
                            attack_type_list = None
                    
                    # Show simulation mode info
                    if simulation_mode == "Red Team vs Blue Team":
                        status_text.info("🔴 Red Team generating attacks... 🔵 Blue Team preparing defense...")
                    
                    # Run simulation with progress updates
                    progress_bar.progress(20)
                    try:
                        logger.info(f"Starting simulation with {num_episodes} episodes")
                        metrics = orchestrator.run_simulation(
                            num_episodes=num_episodes,
                            attack_types=attack_type_list
                        )
                        logger.info(f"Simulation completed. Total episodes: {metrics.total_episodes}")
                        
                        # Save results
                        output_dir = Path("./results") / f"sim_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
                        orchestrator.save_results(output_dir)
                        logger.info(f"Results saved to {output_dir}")
                        
                        st.session_state['results_dir'] = output_dir
                        st.session_state['orchestrator'] = orchestrator
                        st.session_state['simulation_mode'] = simulation_mode
                        
                        progress_bar.progress(100)
                        status_text.success(f"✅ Simulation complete! Mode: {simulation_mode}")
                    except Exception as e:
                        logger.error(f"Simulation failed: {e}", exc_info=True)
                        st.error(f"❌ Simulation failed: {e}")
                        st.exception(e)
                else:
                    st.error("❌ Neither API nor direct mode available. Please check dependencies.")
                    st.info("Install dependencies: `pip install -r requirements.txt`")
                    st.stop()
                    
        except Exception as e:
            st.error(f"❌ Simulation Error: {e}")
            st.exception(e)
    
    # Display results
    if 'results_dir' in st.session_state or 'metrics' in st.session_state:
        # Check if we have API results
        if 'metrics' in st.session_state and API_AVAILABLE:
            # Use API results directly
            api_metrics = st.session_state['metrics']
            
            # Convert API response to dashboard format
            metrics = {
                'total_episodes': api_metrics.get('total_episodes', 0),
                'successful_defenses': api_metrics.get('successful_defenses', 0),
                'failed_defenses': api_metrics.get('failed_defenses', 0),
                'false_positives': api_metrics.get('false_positives', 0),
                'average_reward': api_metrics.get('average_reward', 0.0),
                'average_time_to_remediate': api_metrics.get('average_time_to_remediate', 0.0),
                'detection_rate': api_metrics.get('detection_rate', 0.0),
                'reward_history': api_metrics.get('reward_history', []),
                'action_distribution': api_metrics.get('action_distribution', {}),
                'attack_distribution': api_metrics.get('attack_distribution', {}),
                'defense_strategies': api_metrics.get('defense_strategies', []),
                'episode_details': api_metrics.get('episode_details', [])
            }
            
            # Convert episode_details to episodes format if needed
            if metrics.get('episode_details') and not episodes:
                episodes = metrics['episode_details']
            
            # Try to load episodes from results directory if available
            episodes = []
            if 'results_dir' in st.session_state:
                results_dir = st.session_state['results_dir']
                _, episodes_data = load_results(results_dir)
                if episodes_data:
                    episodes = episodes_data.get('episodes', [])
        else:
            # Load from file system (direct mode or file-based)
            results_dir = st.session_state.get('results_dir')
            if results_dir:
                metrics, episodes_data = load_results(results_dir)
                if episodes_data:
                    episodes = episodes_data.get('episodes', []) if isinstance(episodes_data, dict) else episodes_data
                else:
                    episodes = []
            else:
                metrics = None
                episodes = []
        
        if metrics:
            # Show simulation mode if available
            if 'simulation_mode' in st.session_state:
                mode = st.session_state['simulation_mode']
                if mode == "Red Team vs Blue Team":
                    st.success(f"🎮 Simulation Mode: {mode} - Full adversarial simulation completed")
                else:
                    st.info(f"🎮 Simulation Mode: {mode}")
            
            # Main metrics
            st.header("📊 Overall Performance")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric(
                    "Total Episodes",
                    metrics['total_episodes']
                )
            
            with col2:
                success_rate = (
                    metrics['successful_defenses'] / metrics['total_episodes'] * 100
                )
                st.metric(
                    "Success Rate",
                    f"{success_rate:.1f}%"
                )
            
            with col3:
                st.metric(
                    "Average Reward",
                    f"{metrics['average_reward']:.3f}"
                )
            
            with col4:
                st.metric(
                    "Detection Rate",
                    f"{metrics['detection_rate']:.1%}"
                )
            
            st.markdown("---")
            
            # Visualizations
            st.header("📈 Detailed Analysis")
            
            # Row 1: Reward and Actions
            col1, col2 = st.columns(2)
            
            with col1:
                fig = plot_reward_history(metrics)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = plot_action_distribution(metrics)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Row 2: Attack types and Severity
            col1, col2 = st.columns(2)
            
            with col1:
                # Show attack distribution if available
                if metrics.get('attack_distribution'):
                    fig = plot_attack_distribution(metrics)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
                else:
                    fig = plot_success_rate_by_attack(episodes)
                    if fig:
                        st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = plot_severity_distribution(episodes)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Best Defense Strategies Section
            if metrics.get('defense_strategies'):
                st.markdown("---")
                st.header("🏆 Best Defense Strategies (RL Agent Learning)")
                st.markdown("**Successful defense strategies learned by the RL agent**")
                
                defense_df = pd.DataFrame(metrics['defense_strategies'])
                
                # Group by attack type and action
                strategy_summary = defense_df.groupby(['attack_type', 'action']).agg({
                    'reward': ['mean', 'count'],
                    'time_to_remediate': 'mean'
                }).reset_index()
                strategy_summary.columns = ['Attack Type', 'Action', 'Avg Reward', 'Count', 'Avg Time (min)']
                strategy_summary = strategy_summary.sort_values('Avg Reward', ascending=False)
                
                st.dataframe(strategy_summary, use_container_width=True, hide_index=True)
                
                # Top 5 strategies
                st.subheader("🎯 Top 5 Defense Strategies")
                for idx, row in strategy_summary.head(5).iterrows():
                    st.markdown(
                        f"**{row['Attack Type']}** → **{row['Action']}**: "
                        f"Avg Reward: {row['Avg Reward']:.3f}, "
                        f"Used {int(row['Count'])} times, "
                        f"Avg Response Time: {row['Avg Time (min)']:.1f} min"
                    )
            
            # Episode details with Red Team vs Blue Team context
            st.markdown("---")
            st.header("📋 Episode Details - Red Team vs Blue Team")
            
            df = pd.DataFrame(episodes)
            df['success_emoji'] = df['success'].map({True: '✅', False: '❌'})
            
            # Add team indicators
            df['team'] = df.apply(lambda row: 
                '🔴 Red Team' if row.get('attack_type') else '🔵 Blue Team', axis=1)
            
            display_df = df[[
                'episode_id', 'attack_type', 'severity',
                'action_taken', 'success_emoji', 'reward'
            ]]
            display_df.columns = [
                'Episode ID', '🔴 Attack Type', 'Severity',
                '🔵 Action Taken', 'Result', 'Reward'
            ]
            
            st.dataframe(
                display_df.style.format({'Reward': '{:.3f}'}),
                use_container_width=True,
                height=400
            )
            
            # Show Red Team vs Blue Team summary
            col1, col2 = st.columns(2)
            with col1:
                st.metric("🔴 Red Team Attacks", len(df))
                attack_types = df['attack_type'].value_counts()
                st.write("**Attack Distribution:**")
                for atype, count in attack_types.items():
                    st.write(f"- {atype}: {count}")
            
            with col2:
                successful = df['success_emoji'].str.contains('✅').sum()
                st.metric("🔵 Blue Team Success Rate", f"{successful}/{len(df)} ({successful/len(df)*100:.1f}%)")
                actions = df['action_taken'].value_counts()
                st.write("**Action Distribution:**")
                for action, count in actions.head(5).items():
                    st.write(f"- {action}: {count}")
            
            # Export options
            st.markdown("---")
            st.subheader("💾 Export Results")
            
            col1, col2 = st.columns(2)
            
            with col1:
                csv = df.to_csv(index=False)
                st.download_button(
                    label="Download Episodes CSV",
                    data=csv,
                    file_name="episodes.csv",
                    mime="text/csv"
                )
            
            with col2:
                metrics_json = json.dumps(metrics, indent=2)
                st.download_button(
                    label="Download Metrics JSON",
                    data=metrics_json,
                    file_name="metrics.json",
                    mime="application/json"
                )
    
    else:
        st.info("👈 Load existing results or run a new simulation from the sidebar")
        
        # Show example visualizations
        st.header("Example Dashboard")
        st.markdown("This is what you'll see after running a simulation:")
        
        # Mock data for demo
        example_rewards = [0.1 * i - 0.5 + (i % 3) * 0.2 for i in range(20)]
        example_metrics = {
            'reward_history': example_rewards,
            'action_distribution': {
                'BLOCK_IP': 8,
                'ISOLATE_HOST': 5,
                'LOCK_ACCOUNT': 4,
                'NOTIFY_TEAM': 3
            }
        }
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig = plot_reward_history(example_metrics)
            st.plotly_chart(fig, use_container_width=True)
        
        with col2:
            fig = plot_action_distribution(example_metrics)
            st.plotly_chart(fig, use_container_width=True)


if __name__ == "__main__":
    main()
