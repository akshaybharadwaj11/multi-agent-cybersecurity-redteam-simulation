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

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.orchestrator import CyberDefenseOrchestrator
from core.data_models import AttackType


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
    
    # Title
    st.title("🛡️ Cyber Defense Simulator Dashboard")
    st.markdown("---")
    
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
    
    num_episodes = st.sidebar.slider(
        "Number of Episodes",
        min_value=5,
        max_value=100,
        value=20,
        step=5
    )
    
    attack_types = st.sidebar.multiselect(
        "Attack Types (empty = all)",
        options=[at.value for at in AttackType],
        default=[]
    )
    
    if st.sidebar.button("Run Simulation"):
        with st.spinner("Running simulation..."):
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            # Initialize orchestrator
            orchestrator = CyberDefenseOrchestrator()
            
            # Convert attack types
            attack_type_list = None
            if attack_types:
                attack_type_list = [AttackType(at) for at in attack_types]
            
            # Run simulation with progress updates
            metrics = orchestrator.run_simulation(
                num_episodes=num_episodes,
                attack_types=attack_type_list
            )
            
            progress_bar.progress(100)
            status_text.success("Simulation complete!")
            
            # Save results
            output_dir = Path("./results") / f"sim_{pd.Timestamp.now().strftime('%Y%m%d_%H%M%S')}"
            orchestrator.save_results(output_dir)
            
            st.session_state['results_dir'] = output_dir
            st.session_state['orchestrator'] = orchestrator
    
    # Display results
    if 'results_dir' in st.session_state:
        results_dir = st.session_state['results_dir']
        metrics, episodes = load_results(results_dir)
        
        if metrics and episodes:
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
                fig = plot_success_rate_by_attack(episodes)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            with col2:
                fig = plot_severity_distribution(episodes)
                if fig:
                    st.plotly_chart(fig, use_container_width=True)
            
            # Episode details
            st.markdown("---")
            st.header("📋 Episode Details")
            
            df = pd.DataFrame(episodes)
            df['success_emoji'] = df['success'].map({True: '✅', False: '❌'})
            
            display_df = df[[
                'episode_id', 'attack_type', 'severity',
                'action_taken', 'success_emoji', 'reward'
            ]]
            display_df.columns = [
                'Episode ID', 'Attack Type', 'Severity',
                'Action Taken', 'Success', 'Reward'
            ]
            
            st.dataframe(
                display_df.style.format({'Reward': '{:.3f}'}),
                use_container_width=True
            )
            
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
