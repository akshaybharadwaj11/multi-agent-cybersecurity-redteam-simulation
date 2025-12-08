"""
Cybersecurity RL Environment
Simulates network infrastructure for Red Team vs Blue Team scenarios
Uses CICIDS2017 dataset for realistic traffic patterns
"""

import gymnasium as gym
import numpy as np
import pandas as pd
from typing import Dict, Tuple, List
import networkx as nx
from enum import Enum


class NetworkState(Enum):
    """Network node states"""
    CLEAN = 0
    SUSPICIOUS = 1
    COMPROMISED = 2
    ISOLATED = 3


class CyberSecurityEnv(gym.Env):
    """
    Custom Gym environment for cybersecurity simulation
    State space: Network topology + traffic features from CICIDS2017
    Action space: Attack actions (Red) or Defense actions (Blue)
    """
    
    def __init__(
        self,
        dataset_path: str = None,
        n_nodes: int = 20,
        max_steps: int = 100,
        use_real_traffic: bool = True
    ):
        super().__init__()
        
        self.n_nodes = n_nodes
        self.max_steps = max_steps
        self.use_real_traffic = use_real_traffic
        
        # Load CICIDS2017 dataset
        if use_real_traffic and dataset_path:
            self.traffic_data = self._load_dataset(dataset_path)
            self.traffic_idx = 0
        else:
            self.traffic_data = None
        
        # Network topology (graph representation)
        self.network = self._create_network_topology()
        
        # State space: network features + traffic features
        # 78 features from CICIDS2017 + network state
        self.state_dim = 78 + n_nodes + 10  # traffic + node states + metadata
        self.observation_space = gym.spaces.Box(
            low=-np.inf,
            high=np.inf,
            shape=(self.state_dim,),
            dtype=np.float32
        )
        
        # Action spaces
        self.red_action_space = gym.spaces.Discrete(10)  # 10 attack actions
        self.blue_action_space = gym.spaces.Discrete(10)  # 10 defense actions
        
        # Initialize state
        self.node_states = [NetworkState.CLEAN] * n_nodes
        self.compromised_nodes = set()
        self.isolated_nodes = set()
        self.current_step = 0
        self.attack_history = []
        self.defense_history = []
        
    def _load_dataset(self, path: str) -> pd.DataFrame:
        """Load and preprocess CICIDS2017 dataset"""
        df = pd.read_csv(path)
        
        # Select key features
        feature_columns = [
            'Flow Duration', 'Total Fwd Packets', 'Total Backward Packets',
            'Total Length of Fwd Packets', 'Total Length of Bwd Packets',
            'Fwd Packet Length Max', 'Fwd Packet Length Min', 
            'Fwd Packet Length Mean', 'Fwd Packet Length Std',
            'Bwd Packet Length Max', 'Bwd Packet Length Min',
            'Bwd Packet Length Mean', 'Bwd Packet Length Std',
            'Flow Bytes/s', 'Flow Packets/s', 'Flow IAT Mean',
            'Flow IAT Std', 'Flow IAT Max', 'Flow IAT Min',
            'Fwd IAT Total', 'Fwd IAT Mean', 'Fwd IAT Std',
            'Fwd IAT Max', 'Fwd IAT Min', 'Bwd IAT Total',
            'Bwd IAT Mean', 'Bwd IAT Std', 'Bwd IAT Max', 'Bwd IAT Min',
            'Fwd PSH Flags', 'Bwd PSH Flags', 'Fwd URG Flags', 'Bwd URG Flags',
            'Fwd Header Length', 'Bwd Header Length', 'Fwd Packets/s',
            'Bwd Packets/s', 'Min Packet Length', 'Max Packet Length',
            'Packet Length Mean', 'Packet Length Std', 'Packet Length Variance',
            'FIN Flag Count', 'SYN Flag Count', 'RST Flag Count',
            'PSH Flag Count', 'ACK Flag Count', 'URG Flag Count',
            'CWE Flag Count', 'ECE Flag Count', 'Down/Up Ratio',
            'Average Packet Size', 'Avg Fwd Segment Size',
            'Avg Bwd Segment Size', 'Fwd Header Length.1',
            'Fwd Avg Bytes/Bulk', 'Fwd Avg Packets/Bulk',
            'Fwd Avg Bulk Rate', 'Bwd Avg Bytes/Bulk',
            'Bwd Avg Packets/Bulk', 'Bwd Avg Bulk Rate',
            'Subflow Fwd Packets', 'Subflow Fwd Bytes',
            'Subflow Bwd Packets', 'Subflow Bwd Bytes',
            'Init_Win_bytes_forward', 'Init_Win_bytes_backward',
            'act_data_pkt_fwd', 'min_seg_size_forward',
            'Active Mean', 'Active Std', 'Active Max', 'Active Min',
            'Idle Mean', 'Idle Std', 'Idle Max', 'Idle Min'
        ]
        
        # Handle missing columns
        available_features = [col for col in feature_columns if col in df.columns]
        df = df[available_features].fillna(0)
        
        # Normalize
        df = (df - df.mean()) / (df.std() + 1e-8)
        
        return df
    
    def _create_network_topology(self) -> nx.Graph:
        """Create network topology graph"""
        G = nx.Graph()
        
        # Add nodes with initial attributes
        for i in range(self.n_nodes):
            G.add_node(i, 
                      state=NetworkState.CLEAN,
                      criticality=np.random.uniform(0.5, 1.0),
                      vulnerability=np.random.uniform(0, 1))
        
        # Add edges (network connections)
        # Create a scale-free network (more realistic)
        edges = nx.barabasi_albert_graph(self.n_nodes, 2).edges()
        G.add_edges_from(edges)
        
        return G
    
    def _get_traffic_features(self) -> np.ndarray:
        """Get current traffic features from dataset or simulate"""
        if self.use_real_traffic and self.traffic_data is not None:
            # Get next row from dataset
            features = self.traffic_data.iloc[self.traffic_idx % len(self.traffic_data)].values
            self.traffic_idx += 1
            
            # Pad if necessary
            if len(features) < 78:
                features = np.pad(features, (0, 78 - len(features)))
            elif len(features) > 78:
                features = features[:78]
        else:
            # Simulate traffic features
            features = np.random.randn(78)
        
        return features.astype(np.float32)
    
    def _get_network_state_vector(self) -> np.ndarray:
        """Encode network state as vector"""
        state_vector = np.array([s.value for s in self.node_states], dtype=np.float32)
        return state_vector
    
    def _get_metadata_vector(self) -> np.ndarray:
        """Get metadata about current state"""
        metadata = np.array([
            len(self.compromised_nodes) / self.n_nodes,  # compromise rate
            len(self.isolated_nodes) / self.n_nodes,      # isolation rate
            self.current_step / self.max_steps,           # progress
            len(self.attack_history) / (self.current_step + 1),  # attack frequency
            len(self.defense_history) / (self.current_step + 1),  # defense frequency
            np.mean([self.network.nodes[n]['vulnerability'] 
                    for n in range(self.n_nodes)]),  # avg vulnerability
            np.mean([self.network.nodes[n]['criticality'] 
                    for n in self.compromised_nodes]) if self.compromised_nodes else 0,
            len(list(nx.connected_components(self.network))),  # network fragments
            0, 0  # reserved
        ], dtype=np.float32)
        
        return metadata
    
    def get_state(self) -> np.ndarray:
        """Get complete state observation"""
        traffic = self._get_traffic_features()
        network = self._get_network_state_vector()
        metadata = self._get_metadata_vector()
        
        state = np.concatenate([traffic, network, metadata])
        return state
    
    def reset(self, seed=None) -> Tuple[np.ndarray, Dict]:
        """Reset environment"""
        super().reset(seed=seed)
        
        # Reset network state
        self.node_states = [NetworkState.CLEAN] * self.n_nodes
        self.compromised_nodes = set()
        self.isolated_nodes = set()
        self.current_step = 0
        self.attack_history = []
        self.defense_history = []
        
        # Reset network graph
        for node in self.network.nodes():
            self.network.nodes[node]['state'] = NetworkState.CLEAN
        
        state = self.get_state()
        info = self._get_info()
        
        return state, info
    
    def step_red(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute red team (attack) action"""
        reward = 0.0
        done = False
        
        # Map action to attack
        if action == 0:  # port_scan
            reward = self._port_scan()
        elif action == 1:  # vulnerability_scan
            reward = self._vulnerability_scan()
        elif action == 2:  # exploit_webapp
            reward = self._exploit_webapp()
        elif action == 3:  # exploit_service
            reward = self._exploit_service()
        elif action == 4:  # privilege_escalation
            reward = self._privilege_escalation()
        elif action == 5:  # lateral_movement
            reward = self._lateral_movement()
        elif action == 6:  # data_exfiltration
            reward = self._data_exfiltration()
        elif action == 7:  # persistence
            reward = self._establish_persistence()
        elif action == 8:  # cover_tracks
            reward = self._cover_tracks()
        elif action == 9:  # wait
            reward = -0.01
        
        self.attack_history.append(action)
        self.current_step += 1
        
        # Check termination
        if self.current_step >= self.max_steps:
            done = True
        elif len(self.compromised_nodes) >= self.n_nodes * 0.8:
            reward += 10.0  # Major success
            done = True
        
        state = self.get_state()
        info = self._get_info()
        
        return state, reward, done, False, info
    
    def step_blue(self, action: int) -> Tuple[np.ndarray, float, bool, bool, Dict]:
        """Execute blue team (defense) action"""
        reward = 0.0
        done = False
        
        # Map action to defense
        if action == 0:  # monitor_traffic
            reward = self._monitor_traffic()
        elif action == 1:  # analyze_logs
            reward = self._analyze_logs()
        elif action == 2:  # block_ip
            reward = self._block_ip()
        elif action == 3:  # isolate_host
            reward = self._isolate_host()
        elif action == 4:  # patch_vulnerability
            reward = self._patch_vulnerability()
        elif action == 5:  # increase_monitoring
            reward = self._increase_monitoring()
        elif action == 6:  # deploy_honeypot
            reward = self._deploy_honeypot()
        elif action == 7:  # incident_response
            reward = self._incident_response()
        elif action == 8:  # threat_hunting
            reward = self._threat_hunting()
        elif action == 9:  # wait
            reward = -0.01
        
        self.defense_history.append(action)
        
        state = self.get_state()
        info = self._get_info()
        
        return state, reward, done, False, info
    
    # Attack implementations
    def _port_scan(self) -> float:
        """Reconnaissance: scan for open ports"""
        return 0.1 * (1 - len(self.compromised_nodes) / self.n_nodes)
    
    def _vulnerability_scan(self) -> float:
        """Identify vulnerabilities"""
        high_vuln_nodes = [n for n in range(self.n_nodes) 
                          if self.network.nodes[n]['vulnerability'] > 0.7
                          and n not in self.compromised_nodes]
        return 0.2 if high_vuln_nodes else 0.05
    
    def _exploit_webapp(self) -> float:
        """Attempt web application exploit"""
        target = np.random.choice([n for n in range(self.n_nodes) 
                                  if n not in self.compromised_nodes])
        vuln = self.network.nodes[target]['vulnerability']
        if np.random.random() < vuln:
            self.compromised_nodes.add(target)
            self.node_states[target] = NetworkState.COMPROMISED
            return 1.0 * self.network.nodes[target]['criticality']
        return -0.2
    
    def _exploit_service(self) -> float:
        """Exploit network service"""
        return self._exploit_webapp()  # Similar logic
    
    def _privilege_escalation(self) -> float:
        """Escalate privileges on compromised node"""
        if self.compromised_nodes:
            return 0.5
        return -0.1
    
    def _lateral_movement(self) -> float:
        """Move to adjacent nodes"""
        if not self.compromised_nodes:
            return -0.1
        
        # Find adjacent uncompromised nodes
        comp_node = list(self.compromised_nodes)[0]
        neighbors = list(self.network.neighbors(comp_node))
        targets = [n for n in neighbors if n not in self.compromised_nodes]
        
        if targets:
            target = np.random.choice(targets)
            if np.random.random() < 0.6:
                self.compromised_nodes.add(target)
                self.node_states[target] = NetworkState.COMPROMISED
                return 0.8
        return 0.0
    
    def _data_exfiltration(self) -> float:
        """Exfiltrate data"""
        if self.compromised_nodes:
            value = sum([self.network.nodes[n]['criticality'] 
                        for n in self.compromised_nodes])
            return value / len(self.compromised_nodes)
        return -0.1
    
    def _establish_persistence(self) -> float:
        """Maintain access"""
        return 0.3 if self.compromised_nodes else -0.1
    
    def _cover_tracks(self) -> float:
        """Hide malicious activity"""
        return 0.2 if self.attack_history else 0.0
    
    # Defense implementations
    def _monitor_traffic(self) -> float:
        """Monitor network traffic"""
        suspicious = len([n for n in range(self.n_nodes) 
                         if self.node_states[n] == NetworkState.SUSPICIOUS])
        return 0.1 * suspicious
    
    def _analyze_logs(self) -> float:
        """Analyze system logs"""
        if self.compromised_nodes:
            detected = np.random.random() < 0.3
            if detected:
                return 0.5
        return 0.1
    
    def _block_ip(self) -> float:
        """Block malicious IP"""
        if self.attack_history:
            return 0.3
        return -0.05
    
    def _isolate_host(self) -> float:
        """Isolate compromised host"""
        if self.compromised_nodes:
            node = list(self.compromised_nodes)[0]
            self.isolated_nodes.add(node)
            self.compromised_nodes.remove(node)
            self.node_states[node] = NetworkState.ISOLATED
            return 1.0
        return -0.1
    
    def _patch_vulnerability(self) -> float:
        """Patch system vulnerabilities"""
        for node in range(self.n_nodes):
            if self.network.nodes[node]['vulnerability'] > 0.5:
                self.network.nodes[node]['vulnerability'] *= 0.8
        return 0.4
    
    def _increase_monitoring(self) -> float:
        """Increase monitoring level"""
        return 0.2
    
    def _deploy_honeypot(self) -> float:
        """Deploy honeypot"""
        return 0.3
    
    def _incident_response(self) -> float:
        """Execute incident response"""
        if self.compromised_nodes:
            # Clean some compromised nodes
            to_clean = list(self.compromised_nodes)[:2]
            for node in to_clean:
                self.compromised_nodes.remove(node)
                self.node_states[node] = NetworkState.CLEAN
            return 1.5
        return 0.0
    
    def _threat_hunting(self) -> float:
        """Proactive threat hunting"""
        if self.compromised_nodes:
            if np.random.random() < 0.4:
                return 0.8
        return 0.1
    
    def _get_info(self) -> Dict:
        """Get environment info"""
        return {
            'compromised_nodes': len(self.compromised_nodes),
            'isolated_nodes': len(self.isolated_nodes),
            'attack_success_rate': len(self.compromised_nodes) / self.n_nodes,
            'defense_success_rate': (self.n_nodes - len(self.compromised_nodes)) / self.n_nodes,
            'current_step': self.current_step
        }