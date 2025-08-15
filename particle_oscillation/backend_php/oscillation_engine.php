<?php

/**
 * Particle Oscillation Simulation - PHP Backend
 * Implementation of 4D tetrahedron oscillation based on MMU theory
 */

class FourDimensionalState {
    public float $w1_projection;  // Observable space projection
    public float $w2_energy;      // Energy input
    public float $w3_spin;        // Spin angular momentum
    public float $w4_mass;        // Mass projection
    
    public function __construct(
        float $w1_projection = 0.0,
        float $w2_energy = 1.0,
        float $w3_spin = 0.0,
        float $w4_mass = 1.0
    ) {
        $this->w1_projection = $w1_projection;
        $this->w2_energy = $w2_energy;
        $this->w3_spin = $w3_spin;
        $this->w4_mass = $w4_mass;
    }
    
    public function toArray(): array {
        return [
            'w1_projection' => $this->w1_projection,
            'w2_energy' => $this->w2_energy,
            'w3_spin' => $this->w3_spin,
            'w4_mass' => $this->w4_mass
        ];
    }
    
    public function magnitude(): float {
        return sqrt(
            $this->w1_projection ** 2 + 
            $this->w2_energy ** 2 +
            $this->w3_spin ** 2 + 
            $this->w4_mass ** 2
        );
    }
}

class OscillationParameters {
    public float $base_frequency;
    public float $amplitude_w1;
    public float $amplitude_w2;
    public float $amplitude_w3;
    public float $amplitude_w4;
    public float $phase_w1;
    public float $phase_w2;
    public float $phase_w3;
    public float $phase_w4;
    public float $damping_factor;
    public float $coupling_strength;
    
    public function __construct(
        float $base_frequency = 1.0,
        float $amplitude_w1 = 1.0,
        float $amplitude_w2 = 1.5,
        float $amplitude_w3 = 0.8,
        float $amplitude_w4 = 1.2,
        float $phase_w1 = 0.0,
        float $phase_w2 = M_PI / 4,
        float $phase_w3 = M_PI / 2,
        float $phase_w4 = 3 * M_PI / 4,
        float $damping_factor = 0.98,
        float $coupling_strength = 0.1
    ) {
        $this->base_frequency = $base_frequency;
        $this->amplitude_w1 = $amplitude_w1;
        $this->amplitude_w2 = $amplitude_w2;
        $this->amplitude_w3 = $amplitude_w3;
        $this->amplitude_w4 = $amplitude_w4;
        $this->phase_w1 = $phase_w1;
        $this->phase_w2 = $phase_w2;
        $this->phase_w3 = $phase_w3;
        $this->phase_w4 = $phase_w4;
        $this->damping_factor = $damping_factor;
        $this->coupling_strength = $coupling_strength;
    }
    
    public function toArray(): array {
        return [
            'base_frequency' => $this->base_frequency,
            'amplitude_w1' => $this->amplitude_w1,
            'amplitude_w2' => $this->amplitude_w2,
            'amplitude_w3' => $this->amplitude_w3,
            'amplitude_w4' => $this->amplitude_w4,
            'phase_w1' => $this->phase_w1,
            'phase_w2' => $this->phase_w2,
            'phase_w3' => $this->phase_w3,
            'phase_w4' => $this->phase_w4,
            'damping_factor' => $this->damping_factor,
            'coupling_strength' => $this->coupling_strength
        ];
    }
}

class TetrahedronOscillator {
    public string $particle_id;
    public OscillationParameters $params;
    public float $creation_time;
    public float $current_time;
    public float $dt;
    public FourDimensionalState $current_state;
    public array $state_history;
    public int $max_history;
    public float $stability_factor;
    public float $energy_total;
    public float $phase_coherence;
    
    public function __construct(string $particle_id, OscillationParameters $params) {
        $this->particle_id = $particle_id;
        $this->params = $params;
        $this->creation_time = microtime(true);
        $this->current_time = 0.0;
        $this->dt = 1.0 / 60.0; // 60 FPS
        
        $this->current_state = new FourDimensionalState();
        $this->state_history = [];
        $this->max_history = 1000;
        
        $this->stability_factor = 1.0;
        $this->energy_total = 0.0;
        $this->phase_coherence = 1.0;
    }
    
    public function updateOscillations(float $dt): void {
        $this->current_time += $dt;
        $t = $this->current_time;
        
        // Calculate base oscillations for each dimension
        $w1_base = $this->params->amplitude_w1 * sin(
            2 * M_PI * $this->params->base_frequency * $t + $this->params->phase_w1
        );
        
        $w2_base = $this->params->amplitude_w2 * sin(
            2 * M_PI * $this->params->base_frequency * 1.2 * $t + $this->params->phase_w2
        );
        
        $w3_base = $this->params->amplitude_w3 * sin(
            2 * M_PI * $this->params->base_frequency * 0.8 * $t + $this->params->phase_w3
        );
        
        $w4_base = $this->params->amplitude_w4 * sin(
            2 * M_PI * $this->params->base_frequency * 1.1 * $t + $this->params->phase_w4
        );
        
        // Apply inter-dimensional coupling (MMU theory)
        $coupling = $this->params->coupling_strength;
        
        // w1 (projection) influenced by energy and mass
        $w1_coupled = $w1_base + $coupling * (
            $this->current_state->w2_energy * 0.3 + 
            $this->current_state->w4_mass * 0.2
        );
        
        // w2 (energy) influenced by spin and projection
        $w2_coupled = $w2_base + $coupling * (
            $this->current_state->w3_spin * 0.4 +
            $this->current_state->w1_projection * 0.1
        );
        
        // w3 (spin) influenced by energy with higher frequency
        $w3_coupled = $w3_base + $coupling * ($this->current_state->w2_energy * 0.5) +
                     0.3 * sin(6 * M_PI * $this->params->base_frequency * $t);
        
        // w4 (mass) most stable, slight coupling to projection
        $w4_coupled = $w4_base + $coupling * ($this->current_state->w1_projection * 0.15);
        
        // Apply damping for stability
        $damping = $this->params->damping_factor;
        
        // Update state
        $this->current_state->w1_projection = $w1_coupled * $damping;
        $this->current_state->w2_energy = $w2_coupled * $damping;
        $this->current_state->w3_spin = $w3_coupled * $damping;
        $this->current_state->w4_mass = $w4_coupled * $damping;
        
        // Calculate derived properties
        $this->calculateStability();
        $this->calculateTotalEnergy();
        $this->calculatePhaseCoherence();
        
        // Store history
        $this->storeStateHistory();
    }
    
    private function calculateStability(): void {
        $state_magnitude = $this->current_state->magnitude();
        
        if ($state_magnitude == 0) {
            $this->stability_factor = 0.0;
            return;
        }
        
        // Calculate dimension ratios
        $w1_ratio = abs($this->current_state->w1_projection) / $state_magnitude;
        $w2_ratio = abs($this->current_state->w2_energy) / $state_magnitude;
        $w3_ratio = abs($this->current_state->w3_spin) / $state_magnitude;
        $w4_ratio = abs($this->current_state->w4_mass) / $state_magnitude;
        
        // Ideal balance is 0.25 for each dimension
        $balance_factor = 1.0 - abs(0.25 - $w1_ratio) - abs(0.25 - $w2_ratio) -
                         abs(0.25 - $w3_ratio) - abs(0.25 - $w4_ratio);
        
        $this->stability_factor = max(0.0, min(1.0, $balance_factor));
    }
    
    private function calculateTotalEnergy(): void {
        // Kinetic energy approximation
        $kinetic = 0.5 * (
            $this->current_state->w1_projection ** 2 +
            $this->current_state->w2_energy ** 2 +
            $this->current_state->w3_spin ** 2 +
            $this->current_state->w4_mass ** 2
        );
        
        // Potential energy from dimensional coupling
        $potential = 0.25 * $this->params->coupling_strength * (
            $this->current_state->w1_projection * $this->current_state->w2_energy +
            $this->current_state->w2_energy * $this->current_state->w3_spin +
            $this->current_state->w3_spin * $this->current_state->w4_mass +
            $this->current_state->w4_mass * $this->current_state->w1_projection
        );
        
        $this->energy_total = $kinetic + $potential;
    }
    
    private function calculatePhaseCoherence(): void {
        if (count($this->state_history) < 10) {
            $this->phase_coherence = 1.0;
            return;
        }
        
        // Analyze last 10 states
        $recent_states = array_slice($this->state_history, -10);
        $phase_diffs = [];
        
        for ($i = 1; $i < count($recent_states); $i++) {
            $prev_state = $recent_states[$i-1]['state'];
            $curr_state = $recent_states[$i]['state'];
            
            $diff = abs($curr_state->w1_projection - $prev_state->w1_projection) +
                   abs($curr_state->w2_energy - $prev_state->w2_energy) +
                   abs($curr_state->w3_spin - $prev_state->w3_spin) +
                   abs($curr_state->w4_mass - $prev_state->w4_mass);
            
            $phase_diffs[] = $diff;
        }
        
        $avg_diff = array_sum($phase_diffs) / count($phase_diffs);
        $this->phase_coherence = max(0.0, min(1.0, 1.0 - $avg_diff / 4.0));
    }
    
    private function storeStateHistory(): void {
        $this->state_history[] = [
            'time' => $this->current_time,
            'state' => clone $this->current_state
        ];
        
        // Maintain history size limit
        if (count($this->state_history) > $this->max_history) {
            $this->state_history = array_slice($this->state_history, -$this->max_history);
        }
    }
    
    public function getOscillationData(): array {
        return [
            'particle_id' => $this->particle_id,
            'timestamp' => $this->current_time,
            'state' => $this->current_state->toArray(),
            'derived_properties' => [
                'stability_factor' => $this->stability_factor,
                'energy_total' => $this->energy_total,
                'phase_coherence' => $this->phase_coherence,
                'state_magnitude' => $this->current_state->magnitude()
            ],
            'parameters' => $this->params->toArray()
        ];
    }
    
    public function getHistoryData(int $last_n = 100): array {
        $history_slice = $last_n ? array_slice($this->state_history, -$last_n) : $this->state_history;
        
        $result = [];
        foreach ($history_slice as $entry) {
            $result[] = [
                'time' => $entry['time'],
                'state' => $entry['state']->toArray(),
                'magnitude' => $entry['state']->magnitude()
            ];
        }
        
        return $result;
    }
}

class ParticleOscillationSimulation {
    public array $oscillators;
    public float $simulation_time;
    public bool $is_running;
    public int $update_rate;
    public float $dt;
    public float $global_coupling;
    public float $environmental_noise;
    public int $update_count;
    public float $last_fps_time;
    public float $current_fps;
    
    public function __construct() {
        $this->oscillators = [];
        $this->simulation_time = 0.0;
        $this->is_running = false;
        $this->update_rate = 60;
        $this->dt = 1.0 / $this->update_rate;
        $this->global_coupling = 0.05;
        $this->environmental_noise = 0.01;
        $this->update_count = 0;
        $this->last_fps_time = microtime(true);
        $this->current_fps = 0.0;
    }
    
    public function createOscillator(string $particle_id, ?OscillationParameters $params = null): string {
        if ($params === null) {
            // Create random parameters
            $params = new OscillationParameters(
                base_frequency: mt_rand(50, 200) / 100.0,
                amplitude_w1: mt_rand(80, 120) / 100.0,
                amplitude_w2: mt_rand(100, 180) / 100.0,
                amplitude_w3: mt_rand(60, 100) / 100.0,
                amplitude_w4: mt_rand(100, 140) / 100.0,
                phase_w1: mt_rand(0, 628) / 100.0,
                phase_w2: mt_rand(0, 628) / 100.0,
                phase_w3: mt_rand(0, 628) / 100.0,
                phase_w4: mt_rand(0, 628) / 100.0,
                coupling_strength: mt_rand(5, 15) / 100.0
            );
        }
        
        $oscillator = new TetrahedronOscillator($particle_id, $params);
        $this->oscillators[$particle_id] = $oscillator;
        
        return $particle_id;
    }
    
    public function removeOscillator(string $particle_id): bool {
        if (isset($this->oscillators[$particle_id])) {
            unset($this->oscillators[$particle_id]);
            return true;
        }
        return false;
    }
    
    public function updateSimulation(): void {
        if (!$this->is_running) {
            return;
        }
        
        $this->simulation_time += $this->dt;
        
        // Apply global coupling
        $this->applyGlobalCoupling();
        
        // Update each oscillator
        foreach ($this->oscillators as $oscillator) {
            // Add environmental noise
            $noise_factor = 1.0 + (mt_rand(-100, 100) / 10000.0) * $this->environmental_noise;
            $modified_dt = $this->dt * $noise_factor;
            
            $oscillator->updateOscillations($modified_dt);
        }
        
        // Update performance metrics
        $this->updatePerformanceMetrics();
    }
    
    private function applyGlobalCoupling(): void {
        if (count($this->oscillators) < 2) {
            return;
        }
        
        $oscillator_list = array_values($this->oscillators);
        
        for ($i = 0; $i < count($oscillator_list); $i++) {
            for ($j = $i + 1; $j < count($oscillator_list); $j++) {
                $osc1 = $oscillator_list[$i];
                $osc2 = $oscillator_list[$j];
                
                // Calculate coupling influence
                $coupling_w2 = $this->global_coupling * (
                    $osc2->current_state->w2_energy - $osc1->current_state->w2_energy
                ) * 0.1;
                
                $coupling_w3 = $this->global_coupling * (
                    $osc2->current_state->w3_spin - $osc1->current_state->w3_spin
                ) * 0.05;
                
                // Apply bidirectional coupling
                $osc1->current_state->w2_energy += $coupling_w2;
                $osc1->current_state->w3_spin += $coupling_w3;
                
                $osc2->current_state->w2_energy -= $coupling_w2;
                $osc2->current_state->w3_spin -= $coupling_w3;
            }
        }
    }
    
    private function updatePerformanceMetrics(): void {
        $this->update_count++;
        
        $current_time = microtime(true);
        if ($current_time - $this->last_fps_time >= 1.0) {
            $this->current_fps = $this->update_count / ($current_time - $this->last_fps_time);
            $this->update_count = 0;
            $this->last_fps_time = $current_time;
        }
    }
    
    public function startSimulation(): void {
        $this->is_running = true;
    }
    
    public function stopSimulation(): void {
        $this->is_running = false;
    }
    
    public function resetSimulation(): void {
        $this->simulation_time = 0.0;
        $this->is_running = false;
        $this->oscillators = [];
    }
    
    public function getSimulationState(): array {
        $oscillator_data = [];
        $total_energy = 0.0;
        $avg_stability = 0.0;
        
        foreach ($this->oscillators as $osc_id => $oscillator) {
            $osc_data = $oscillator->getOscillationData();
            $oscillator_data[$osc_id] = $osc_data;
            $total_energy += $osc_data['derived_properties']['energy_total'];
            $avg_stability += $osc_data['derived_properties']['stability_factor'];
        }
        
        if (count($this->oscillators) > 0) {
            $avg_stability /= count($this->oscillators);
        }
        
        return [
            'simulation_time' => $this->simulation_time,
            'is_running' => $this->is_running,
            'oscillator_count' => count($this->oscillators),
            'oscillators' => $oscillator_data,
            'global_metrics' => [
                'total_energy' => $total_energy,
                'average_stability' => $avg_stability,
                'current_fps' => $this->current_fps,
                'global_coupling' => $this->global_coupling,
                'environmental_noise' => $this->environmental_noise
            ]
        ];
    }
    
    public function getVisualizationData(): array {
        $viz_data = [
            'timestamp' => $this->simulation_time,
            'particles' => []
        ];
        
        foreach ($this->oscillators as $osc_id => $oscillator) {
            $state = $oscillator->current_state;
            $particle_viz = [
                'id' => $osc_id,
                'position' => [
                    'x' => $state->w1_projection,
                    'y' => $state->w2_energy,
                    'z' => $state->w3_spin
                ],
                'mass' => $state->w4_mass,
                'stability' => $oscillator->stability_factor,
                'energy' => $oscillator->energy_total,
                'coherence' => $oscillator->phase_coherence,
                'magnitude' => $state->magnitude(),
                'color_intensity' => min(1.0, abs($state->w2_energy) / 2.0)
            ];
            $viz_data['particles'][] = $particle_viz;
        }
        
        return $viz_data;
    }
}

?>