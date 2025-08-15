import numpy as np
import math
import time
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import json

@dataclass
class FourDimensionalState:
    """Four-dimensional state vector for MMU tetrahedron oscillation"""
    w1_projection: float      # Observable space projection
    w2_energy: float         # Energy input
    w3_spin: float           # Spin angular momentum
    w4_mass: float           # Mass projection
    
    def to_dict(self) -> Dict:
        return asdict(self)
    
    def magnitude(self) -> float:
        """Calculate 4D magnitude of state vector"""
        return math.sqrt(self.w1_projection**2 + self.w2_energy**2 + 
                        self.w3_spin**2 + self.w4_mass**2)

@dataclass
class OscillationParameters:
    """Parameters controlling tetrahedron oscillation behavior"""
    base_frequency: float = 1.0      # Base oscillation frequency (Hz)
    amplitude_w1: float = 1.0        # Projection amplitude
    amplitude_w2: float = 1.5        # Energy amplitude  
    amplitude_w3: float = 0.8        # Spin amplitude
    amplitude_w4: float = 1.2        # Mass amplitude
    phase_w1: float = 0.0           # Projection phase offset
    phase_w2: float = math.pi/4     # Energy phase offset
    phase_w3: float = math.pi/2     # Spin phase offset
    phase_w4: float = 3*math.pi/4   # Mass phase offset
    damping_factor: float = 0.98    # Damping coefficient
    coupling_strength: float = 0.1   # Inter-dimensional coupling

class TetrahedronOscillator:
    """Single tetrahedron particle with 4D oscillation dynamics"""
    
    def __init__(self, particle_id: str, params: OscillationParameters):
        self.particle_id = particle_id
        self.params = params
        self.creation_time = time.time()
        self.current_time = 0.0
        self.dt = 0.016  # 60 FPS update rate
        
        # Initialize state
        self.current_state = FourDimensionalState(
            w1_projection=0.0,
            w2_energy=1.0,
            w3_spin=0.0, 
            w4_mass=1.0
        )
        
        # Oscillation history for analysis
        self.state_history: List[Tuple[float, FourDimensionalState]] = []
        self.max_history = 1000
        
        # Derived properties
        self.stability_factor = 1.0
        self.energy_total = 0.0
        self.phase_coherence = 1.0
        
    def update_oscillations(self, dt: float) -> None:
        """Update 4D oscillation state based on MMU dynamics"""
        self.current_time += dt
        t = self.current_time
        
        # Calculate base oscillations for each dimension
        w1_base = self.params.amplitude_w1 * math.sin(
            2 * math.pi * self.params.base_frequency * t + self.params.phase_w1
        )
        
        w2_base = self.params.amplitude_w2 * math.sin(
            2 * math.pi * self.params.base_frequency * 1.2 * t + self.params.phase_w2
        )
        
        w3_base = self.params.amplitude_w3 * math.sin(
            2 * math.pi * self.params.base_frequency * 0.8 * t + self.params.phase_w3
        )
        
        w4_base = self.params.amplitude_w4 * math.sin(
            2 * math.pi * self.params.base_frequency * 1.1 * t + self.params.phase_w4
        )
        
        # Apply inter-dimensional coupling (MMU theory)
        coupling = self.params.coupling_strength
        
        # w1 (projection) influenced by energy and mass
        w1_coupled = w1_base + coupling * (self.current_state.w2_energy * 0.3 + 
                                          self.current_state.w4_mass * 0.2)
        
        # w2 (energy) influenced by spin and projection  
        w2_coupled = w2_base + coupling * (self.current_state.w3_spin * 0.4 +
                                          self.current_state.w1_projection * 0.1)
        
        # w3 (spin) influenced by energy and exhibits higher frequency
        w3_coupled = w3_base + coupling * (self.current_state.w2_energy * 0.5) + \
                    0.3 * math.sin(6 * math.pi * self.params.base_frequency * t)
        
        # w4 (mass) most stable, slight coupling to projection
        w4_coupled = w4_base + coupling * (self.current_state.w1_projection * 0.15)
        
        # Apply damping for stability
        damping = self.params.damping_factor
        
        # Update state with momentum conservation
        self.current_state.w1_projection = w1_coupled * damping
        self.current_state.w2_energy = w2_coupled * damping
        self.current_state.w3_spin = w3_coupled * damping  
        self.current_state.w4_mass = w4_coupled * damping
        
        # Calculate derived properties
        self._calculate_stability()
        self._calculate_total_energy()
        self._calculate_phase_coherence()
        
        # Store history
        self._store_state_history()
    
    def _calculate_stability(self) -> None:
        """Calculate stability factor based on 4D state balance"""
        state_magnitude = self.current_state.magnitude()
        
        # Stability decreases if any dimension dominates
        w1_ratio = abs(self.current_state.w1_projection) / (state_magnitude + 1e-6)
        w2_ratio = abs(self.current_state.w2_energy) / (state_magnitude + 1e-6)
        w3_ratio = abs(self.current_state.w3_spin) / (state_magnitude + 1e-6)
        w4_ratio = abs(self.current_state.w4_mass) / (state_magnitude + 1e-6)
        
        # Ideal balance is 0.25 for each dimension
        balance_factor = 1.0 - abs(0.25 - w1_ratio) - abs(0.25 - w2_ratio) - \
                        abs(0.25 - w3_ratio) - abs(0.25 - w4_ratio)
        
        self.stability_factor = max(0.0, min(1.0, balance_factor))
    
    def _calculate_total_energy(self) -> None:
        """Calculate total system energy in 4D space"""
        # Kinetic energy approximation from oscillation amplitudes
        kinetic = 0.5 * (self.current_state.w1_projection**2 + 
                        self.current_state.w2_energy**2 +
                        self.current_state.w3_spin**2 + 
                        self.current_state.w4_mass**2)
        
        # Potential energy from dimensional coupling
        potential = 0.25 * self.params.coupling_strength * (
            self.current_state.w1_projection * self.current_state.w2_energy +
            self.current_state.w2_energy * self.current_state.w3_spin +
            self.current_state.w3_spin * self.current_state.w4_mass +
            self.current_state.w4_mass * self.current_state.w1_projection
        )
        
        self.energy_total = kinetic + potential
    
    def _calculate_phase_coherence(self) -> None:
        """Calculate phase coherence across 4 dimensions"""
        if len(self.state_history) < 10:
            self.phase_coherence = 1.0
            return
            
        # Analyze last 10 states for phase relationship
        recent_states = self.state_history[-10:]
        
        # Calculate phase differences
        phase_diffs = []
        for i in range(1, len(recent_states)):
            prev_state = recent_states[i-1][1]
            curr_state = recent_states[i][1]
            
            # Simple phase difference estimation
            diff = abs(curr_state.w1_projection - prev_state.w1_projection) + \
                   abs(curr_state.w2_energy - prev_state.w2_energy) + \
                   abs(curr_state.w3_spin - prev_state.w3_spin) + \
                   abs(curr_state.w4_mass - prev_state.w4_mass)
            
            phase_diffs.append(diff)
        
        # Coherence inversely related to phase variation
        avg_diff = sum(phase_diffs) / len(phase_diffs)
        self.phase_coherence = max(0.0, min(1.0, 1.0 - avg_diff / 4.0))
    
    def _store_state_history(self) -> None:
        """Store current state in history buffer"""
        self.state_history.append((self.current_time, 
                                  FourDimensionalState(**asdict(self.current_state))))
        
        # Maintain history size limit
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
    
    def get_oscillation_data(self) -> Dict:
        """Get current oscillation data for visualization"""
        return {
            'particle_id': self.particle_id,
            'timestamp': self.current_time,
            'state': self.current_state.to_dict(),
            'derived_properties': {
                'stability_factor': self.stability_factor,
                'energy_total': self.energy_total,
                'phase_coherence': self.phase_coherence,
                'state_magnitude': self.current_state.magnitude()
            },
            'parameters': asdict(self.params)
        }
    
    def get_history_data(self, last_n: int = 100) -> List[Dict]:
        """Get historical oscillation data for analysis"""
        history_slice = self.state_history[-last_n:] if last_n else self.state_history
        
        return [{
            'time': t,
            'state': state.to_dict(),
            'magnitude': state.magnitude()
        } for t, state in history_slice]

class ParticleOscillationSimulation:
    """Main simulation engine for multiple tetrahedron oscillators"""
    
    def __init__(self):
        self.oscillators: Dict[str, TetrahedronOscillator] = {}
        self.simulation_time = 0.0
        self.is_running = False
        self.update_rate = 60  # FPS
        self.dt = 1.0 / self.update_rate
        
        # Global simulation parameters  
        self.global_coupling = 0.05
        self.environmental_noise = 0.01
        
        # Performance metrics
        self.update_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
    
    def create_oscillator(self, particle_id: str, 
                         params: Optional[OscillationParameters] = None) -> str:
        """Create new tetrahedron oscillator"""
        if params is None:
            # Create random parameters for variety
            params = OscillationParameters(
                base_frequency=np.random.uniform(0.5, 2.0),
                amplitude_w1=np.random.uniform(0.8, 1.2),
                amplitude_w2=np.random.uniform(1.0, 1.8),
                amplitude_w3=np.random.uniform(0.6, 1.0),
                amplitude_w4=np.random.uniform(1.0, 1.4),
                phase_w1=np.random.uniform(0, 2*math.pi),
                phase_w2=np.random.uniform(0, 2*math.pi),
                phase_w3=np.random.uniform(0, 2*math.pi), 
                phase_w4=np.random.uniform(0, 2*math.pi),
                coupling_strength=np.random.uniform(0.05, 0.15)
            )
        
        oscillator = TetrahedronOscillator(particle_id, params)
        self.oscillators[particle_id] = oscillator
        
        return particle_id
    
    def remove_oscillator(self, particle_id: str) -> bool:
        """Remove oscillator from simulation"""
        if particle_id in self.oscillators:
            del self.oscillators[particle_id]
            return True
        return False
    
    def update_simulation(self) -> None:
        """Update all oscillators in simulation"""
        if not self.is_running:
            return
            
        # Update simulation time
        self.simulation_time += self.dt
        
        # Apply global coupling between oscillators
        self._apply_global_coupling()
        
        # Update each oscillator
        for oscillator in self.oscillators.values():
            # Add environmental noise
            noise_factor = 1.0 + np.random.normal(0, self.environmental_noise)
            modified_dt = self.dt * noise_factor
            
            oscillator.update_oscillations(modified_dt)
        
        # Update performance metrics
        self._update_performance_metrics()
    
    def _apply_global_coupling(self) -> None:
        """Apply coupling effects between oscillators"""
        if len(self.oscillators) < 2:
            return
            
        oscillator_list = list(self.oscillators.values())
        
        for i, osc1 in enumerate(oscillator_list):
            for j, osc2 in enumerate(oscillator_list[i+1:], i+1):
                # Calculate coupling influence
                coupling_w2 = self.global_coupling * (
                    osc2.current_state.w2_energy - osc1.current_state.w2_energy
                ) * 0.1
                
                coupling_w3 = self.global_coupling * (
                    osc2.current_state.w3_spin - osc1.current_state.w3_spin  
                ) * 0.05
                
                # Apply bidirectional coupling
                osc1.current_state.w2_energy += coupling_w2
                osc1.current_state.w3_spin += coupling_w3
                
                osc2.current_state.w2_energy -= coupling_w2
                osc2.current_state.w3_spin -= coupling_w3
    
    def _update_performance_metrics(self) -> None:
        """Update simulation performance metrics"""
        self.update_count += 1
        
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.update_count / (current_time - self.last_fps_time)
            self.update_count = 0
            self.last_fps_time = current_time
    
    def start_simulation(self) -> None:
        """Start the oscillation simulation"""
        self.is_running = True
    
    def stop_simulation(self) -> None:
        """Stop the oscillation simulation"""
        self.is_running = False
    
    def reset_simulation(self) -> None:
        """Reset simulation to initial state"""
        self.simulation_time = 0.0
        self.is_running = False
        self.oscillators.clear()
    
    def get_simulation_state(self) -> Dict:
        """Get complete simulation state"""
        oscillator_data = {}
        total_energy = 0.0
        avg_stability = 0.0
        
        for osc_id, oscillator in self.oscillators.items():
            osc_data = oscillator.get_oscillation_data()
            oscillator_data[osc_id] = osc_data
            total_energy += osc_data['derived_properties']['energy_total']
            avg_stability += osc_data['derived_properties']['stability_factor']
        
        if len(self.oscillators) > 0:
            avg_stability /= len(self.oscillators)
        
        return {
            'simulation_time': self.simulation_time,
            'is_running': self.is_running,
            'oscillator_count': len(self.oscillators),
            'oscillators': oscillator_data,
            'global_metrics': {
                'total_energy': total_energy,
                'average_stability': avg_stability,
                'current_fps': self.current_fps,
                'global_coupling': self.global_coupling,
                'environmental_noise': self.environmental_noise
            }
        }
    
    def get_visualization_data(self) -> Dict:
        """Get data optimized for real-time visualization"""
        viz_data = {
            'timestamp': self.simulation_time,
            'particles': []
        }
        
        for osc_id, oscillator in self.oscillators.items():
            state = oscillator.current_state
            particle_viz = {
                'id': osc_id,
                'position': {
                    'x': state.w1_projection,
                    'y': state.w2_energy, 
                    'z': state.w3_spin
                },
                'mass': state.w4_mass,
                'stability': oscillator.stability_factor,
                'energy': oscillator.energy_total,
                'coherence': oscillator.phase_coherence,
                'magnitude': state.magnitude(),
                'color_intensity': min(1.0, abs(state.w2_energy) / 2.0)
            }
            viz_data['particles'].append(particle_viz)
        
        return viz_data

# Example usage and testing
if __name__ == "__main__":
    # Create simulation
    sim = ParticleOscillationSimulation()
    
    # Create test oscillators
    for i in range(3):
        particle_id = f"tetrahedron_{i}"
        sim.create_oscillator(particle_id)
    
    # Run simulation for testing
    sim.start_simulation()
    
    print("Running Particle Oscillation Simulation...")
    print("Press Ctrl+C to stop")
    
    try:
        while True:
            sim.update_simulation()
            
            # Print status every second
            if int(sim.simulation_time * 10) % 10 == 0:
                state = sim.get_simulation_state()
                print(f"Time: {sim.simulation_time:.1f}s, "
                      f"Particles: {state['oscillator_count']}, "
                      f"FPS: {state['global_metrics']['current_fps']:.1f}, "
                      f"Total Energy: {state['global_metrics']['total_energy']:.2f}")
            
            time.sleep(sim.dt)
            
    except KeyboardInterrupt:
        print("\nSimulation stopped")
        sim.stop_simulation()