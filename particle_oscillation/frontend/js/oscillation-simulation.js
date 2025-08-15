/**
 * Particle Oscillation Simulation - Frontend JavaScript
 * Real-time 4D tetrahedron oscillation visualization
 */

class ParticleOscillationApp {
    constructor() {
        this.backend = 'python'; // default backend
        this.apiUrl = 'http://localhost:8002/api'; // Python FastAPI
        
        this.isRunning = false;
        this.particles = new Map();
        this.selectedParticle = null;
        this.updateInterval = null;
        this.connectionStatus = false;
        
        // Charts
        this.dimensionalChart = null;
        this.performanceChart = null;
        
        // Performance tracking
        this.performanceData = {
            timestamps: [],
            fps: [],
            energy: [],
            stability: []
        };
        
        this.initializeUI();
        this.setupEventListeners();
        this.initializeCharts();
        this.checkConnection();
    }
    
    initializeUI() {
        // Backend selector
        const backendSelector = document.getElementById('backendSelector');
        backendSelector.addEventListener('change', (e) => {
            this.switchBackend(e.target.value);
        });
        
        // Configuration sliders
        this.setupConfigurationSliders();
    }
    
    setupConfigurationSliders() {
        const sliders = [
            { id: 'globalCoupling', valueId: 'globalCouplingValue' },
            { id: 'environmentalNoise', valueId: 'environmentalNoiseValue' },
            { id: 'updateRate', valueId: 'updateRateValue' }
        ];
        
        sliders.forEach(slider => {
            const element = document.getElementById(slider.id);
            const valueElement = document.getElementById(slider.valueId);
            
            element.addEventListener('input', (e) => {
                valueElement.textContent = e.target.value;
                this.updateConfiguration();
            });
        });
    }
    
    setupEventListeners() {
        // Control buttons
        document.getElementById('startBtn').addEventListener('click', () => this.startSimulation());
        document.getElementById('stopBtn').addEventListener('click', () => this.stopSimulation());
        document.getElementById('resetBtn').addEventListener('click', () => this.resetSimulation());
        document.getElementById('createParticleBtn').addEventListener('click', () => this.createParticle());
    }
    
    switchBackend(backend) {
        this.backend = backend;
        
        if (backend === 'python') {
            this.apiUrl = 'http://localhost:8002/api';
        } else if (backend === 'php') {
            this.apiUrl = 'http://localhost/particle_oscillation/backend_php/api.php';
        }
        
        this.stopUpdateLoop();
        this.checkConnection();
    }
    
    async checkConnection() {
        try {
            const response = await fetch(`${this.apiUrl}/status`);
            const data = await response.json();
            
            this.connectionStatus = true;
            this.updateConnectionStatus(true, `Connected to ${this.backend.toUpperCase()}`);
            
            // Get initial state
            await this.fetchSimulationState();
            
        } catch (error) {
            this.connectionStatus = false;
            this.updateConnectionStatus(false, 'Connection Failed');
            console.error('Connection error:', error);
        }
    }
    
    updateConnectionStatus(connected, message) {
        const statusElement = document.getElementById('connectionStatus');
        const dot = statusElement.querySelector('div');
        const text = statusElement.querySelector('span');
        
        if (connected) {
            dot.className = 'w-3 h-3 bg-green-500 rounded-full';
            text.textContent = message;
            text.className = 'text-sm text-green-600';
        } else {
            dot.className = 'w-3 h-3 bg-red-500 rounded-full animate-pulse';
            text.textContent = message;
            text.className = 'text-sm text-red-600';
        }
    }
    
    async startSimulation() {
        if (!this.connectionStatus) {
            alert('No connection to backend server');
            return;
        }
        
        try {
            await fetch(`${this.apiUrl}/simulation/start`, { method: 'POST' });
            this.isRunning = true;
            this.startUpdateLoop();
            
            // Update UI
            document.getElementById('startBtn').disabled = true;
            document.getElementById('stopBtn').disabled = false;
            
        } catch (error) {
            console.error('Start simulation error:', error);
        }
    }
    
    async stopSimulation() {
        try {
            await fetch(`${this.apiUrl}/simulation/stop`, { method: 'POST' });
            this.isRunning = false;
            this.stopUpdateLoop();
            
            // Update UI
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
        } catch (error) {
            console.error('Stop simulation error:', error);
        }
    }
    
    async resetSimulation() {
        try {
            await fetch(`${this.apiUrl}/simulation/reset`, { method: 'POST' });
            this.isRunning = false;
            this.particles.clear();
            this.selectedParticle = null;
            this.stopUpdateLoop();
            
            // Clear UI
            this.renderParticles();
            this.updateSystemMetrics(null);
            this.clearParticleDetails();
            
            // Update buttons
            document.getElementById('startBtn').disabled = false;
            document.getElementById('stopBtn').disabled = true;
            
        } catch (error) {
            console.error('Reset simulation error:', error);
        }
    }
    
    async createParticle() {
        if (!this.connectionStatus) {
            alert('No connection to backend server');
            return;
        }
        
        try {
            // Create random parameters for variety
            const randomParams = {
                base_frequency: 0.5 + Math.random() * 1.5,
                amplitude_w1: 0.8 + Math.random() * 0.4,
                amplitude_w2: 1.0 + Math.random() * 0.8,
                amplitude_w3: 0.6 + Math.random() * 0.4,
                amplitude_w4: 1.0 + Math.random() * 0.4,
                phase_w1: Math.random() * 2 * Math.PI,
                phase_w2: Math.random() * 2 * Math.PI,
                phase_w3: Math.random() * 2 * Math.PI,
                phase_w4: Math.random() * 2 * Math.PI,
                coupling_strength: 0.05 + Math.random() * 0.1
            };
            
            const response = await fetch(`${this.apiUrl}/oscillators/create`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    parameters: randomParams
                })
            });
            
            const data = await response.json();
            console.log('Particle created:', data);
            
            // Refresh state
            await this.fetchSimulationState();
            
        } catch (error) {
            console.error('Create particle error:', error);
        }
    }
    
    async updateConfiguration() {
        if (!this.connectionStatus) return;
        
        const config = {
            global_coupling: parseFloat(document.getElementById('globalCoupling').value),
            environmental_noise: parseFloat(document.getElementById('environmentalNoise').value),
            update_rate: parseInt(document.getElementById('updateRate').value)
        };
        
        try {
            await fetch(`${this.apiUrl}/simulation/config`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify(config)
            });
        } catch (error) {
            console.error('Update configuration error:', error);
        }
    }
    
    startUpdateLoop() {
        this.stopUpdateLoop();
        this.updateInterval = setInterval(() => {
            this.fetchSimulationState();
        }, 100); // 10 FPS updates
    }
    
    stopUpdateLoop() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
            this.updateInterval = null;
        }
    }
    
    async fetchSimulationState() {
        if (!this.connectionStatus) return;
        
        try {
            const response = await fetch(`${this.apiUrl}/simulation/state`);
            const data = await response.json();
            
            // Update particles data
            this.particles.clear();
            if (data.oscillators) {
                Object.entries(data.oscillators).forEach(([id, particleData]) => {
                    this.particles.set(id, particleData);
                });
            }
            
            // Update UI
            this.renderParticles();
            this.updateSystemMetrics(data);
            this.updatePerformanceData(data);
            
            // Update selected particle details
            if (this.selectedParticle && this.particles.has(this.selectedParticle)) {
                this.showParticleDetails(this.selectedParticle);
            }
            
        } catch (error) {
            console.error('Fetch simulation state error:', error);
            this.connectionStatus = false;
            this.updateConnectionStatus(false, 'Connection Lost');
        }
    }
    
    renderParticles() {
        const container = document.getElementById('particlesContainer');
        
        if (this.particles.size === 0) {
            container.innerHTML = `
                <div class="text-center text-gray-500">
                    <i data-lucide="plus-circle" class="w-12 h-12 mx-auto mb-2 opacity-50"></i>
                    <p>No particles created yet</p>
                    <p class="text-sm">Click "Create Particle" to start</p>
                </div>
            `;
            lucide.createIcons();
            return;
        }
        
        const particleElements = Array.from(this.particles.entries()).map(([id, particle]) => {
            const state = particle.state;
            const props = particle.derived_properties;
            
            // Calculate visual properties
            const w1_norm = Math.max(0, Math.min(1, (state.w1_projection + 2) / 4));
            const w2_norm = Math.max(0, Math.min(1, (state.w2_energy + 2) / 4));
            const w3_norm = Math.max(0, Math.min(1, (state.w3_spin + 2) / 4));
            const w4_norm = Math.max(0, Math.min(1, (state.w4_mass + 2) / 4));
            
            const stabilityColor = props.stability_factor > 0.8 ? 'green' : 
                                  props.stability_factor > 0.5 ? 'yellow' : 'red';
            
            const isSelected = this.selectedParticle === id;
            
            return `
                <div class="particle-oscillator p-4 bg-white rounded-lg border-2 cursor-pointer transition-all duration-300 hover:shadow-lg ${
                    isSelected ? 'border-blue-500 shadow-blue-500/20' : 'border-gray-200'
                }" data-particle-id="${id}">
                    
                    <!-- Particle Header -->
                    <div class="flex justify-between items-center mb-3">
                        <div class="text-xs font-mono text-gray-500">${id.substring(0, 12)}...</div>
                        <div class="flex items-center space-x-1">
                            <div class="w-2 h-2 bg-${stabilityColor}-500 rounded-full"></div>
                            <span class="text-xs text-${stabilityColor}-600">${(props.stability_factor * 100).toFixed(0)}%</span>
                        </div>
                    </div>
                    
                    <!-- 4D State Visualization -->
                    <div class="space-y-2">
                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-600">w₁ (Projection)</span>
                            <span class="text-xs font-mono">${state.w1_projection.toFixed(2)}</span>
                        </div>
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="dimension-bar h-full bg-blue-500 transition-all duration-200" 
                                 style="width: ${w1_norm * 100}%"></div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-600">w₂ (Energy)</span>
                            <span class="text-xs font-mono">${state.w2_energy.toFixed(2)}</span>
                        </div>
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="dimension-bar h-full bg-red-500 transition-all duration-200" 
                                 style="width: ${w2_norm * 100}%"></div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-600">w₃ (Spin)</span>
                            <span class="text-xs font-mono">${state.w3_spin.toFixed(2)}</span>
                        </div>
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="dimension-bar h-full bg-green-500 transition-all duration-200" 
                                 style="width: ${w3_norm * 100}%"></div>
                        </div>
                        
                        <div class="flex items-center justify-between">
                            <span class="text-xs text-gray-600">w₄ (Mass)</span>
                            <span class="text-xs font-mono">${state.w4_mass.toFixed(2)}</span>
                        </div>
                        <div class="h-2 bg-gray-200 rounded-full overflow-hidden">
                            <div class="dimension-bar h-full bg-purple-500 transition-all duration-200" 
                                 style="width: ${w4_norm * 100}%"></div>
                        </div>
                    </div>
                    
                    <!-- Energy & Coherence -->
                    <div class="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
                        <div class="text-center">
                            <div class="text-xs font-semibold text-gray-700">${props.energy_total.toFixed(2)}</div>
                            <div class="text-xs text-gray-500">Energy</div>
                        </div>
                        <div class="text-center">
                            <div class="text-xs font-semibold text-gray-700">${(props.phase_coherence * 100).toFixed(0)}%</div>
                            <div class="text-xs text-gray-500">Coherence</div>
                        </div>
                    </div>
                    
                    <!-- Delete Button -->
                    <button class="delete-particle absolute top-1 right-1 w-6 h-6 bg-red-500 hover:bg-red-600 text-white rounded-full text-xs opacity-0 group-hover:opacity-100 transition-opacity" 
                            data-particle-id="${id}">×</button>
                </div>
            `;
        }).join('');
        
        container.innerHTML = `
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 particle-grid w-full">
                ${particleElements}
            </div>
        `;
        
        // Add event listeners
        container.querySelectorAll('.particle-oscillator').forEach(element => {
            element.addEventListener('click', (e) => {
                const particleId = e.currentTarget.dataset.particleId;
                this.selectParticle(particleId);
            });
        });
        
        container.querySelectorAll('.delete-particle').forEach(button => {
            button.addEventListener('click', async (e) => {
                e.stopPropagation();
                const particleId = e.target.dataset.particleId;
                await this.deleteParticle(particleId);
            });
        });
        
        // Recreate icons
        lucide.createIcons();
    }
    
    async deleteParticle(particleId) {
        try {
            await fetch(`${this.apiUrl}/oscillators/${particleId}`, { method: 'DELETE' });
            
            if (this.selectedParticle === particleId) {
                this.selectedParticle = null;
                this.clearParticleDetails();
            }
            
            await this.fetchSimulationState();
            
        } catch (error) {
            console.error('Delete particle error:', error);
        }
    }
    
    selectParticle(particleId) {
        this.selectedParticle = particleId;
        this.showParticleDetails(particleId);
        this.renderParticles(); // Re-render to show selection
    }
    
    showParticleDetails(particleId) {
        const particle = this.particles.get(particleId);
        if (!particle) return;
        
        const state = particle.state;
        const props = particle.derived_properties;
        const params = particle.parameters;
        
        const detailsHtml = `
            <div class="space-y-4">
                <div class="flex justify-between items-center">
                    <h4 class="font-semibold text-gray-900">Particle ${particleId.substring(0, 8)}</h4>
                    <div class="text-sm text-gray-500">t = ${particle.timestamp.toFixed(2)}s</div>
                </div>
                
                <!-- 4D State Values -->
                <div class="grid grid-cols-2 gap-3">
                    <div class="bg-blue-50 p-3 rounded-lg">
                        <div class="text-sm font-medium text-blue-700">w₁ Projection</div>
                        <div class="text-lg font-bold text-blue-900">${state.w1_projection.toFixed(3)}</div>
                    </div>
                    <div class="bg-red-50 p-3 rounded-lg">
                        <div class="text-sm font-medium text-red-700">w₂ Energy</div>
                        <div class="text-lg font-bold text-red-900">${state.w2_energy.toFixed(3)}</div>
                    </div>
                    <div class="bg-green-50 p-3 rounded-lg">
                        <div class="text-sm font-medium text-green-700">w₃ Spin</div>
                        <div class="text-lg font-bold text-green-900">${state.w3_spin.toFixed(3)}</div>
                    </div>
                    <div class="bg-purple-50 p-3 rounded-lg">
                        <div class="text-sm font-medium text-purple-700">w₄ Mass</div>
                        <div class="text-lg font-bold text-purple-900">${state.w4_mass.toFixed(3)}</div>
                    </div>
                </div>
                
                <!-- Derived Properties -->
                <div class="border-t pt-4">
                    <h5 class="font-medium text-gray-700 mb-2">Derived Properties</h5>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between">
                            <span>State Magnitude:</span>
                            <span class="font-mono">${props.state_magnitude.toFixed(3)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Total Energy:</span>
                            <span class="font-mono">${props.energy_total.toFixed(3)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Stability Factor:</span>
                            <span class="font-mono">${(props.stability_factor * 100).toFixed(1)}%</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Phase Coherence:</span>
                            <span class="font-mono">${(props.phase_coherence * 100).toFixed(1)}%</span>
                        </div>
                    </div>
                </div>
                
                <!-- Oscillation Parameters -->
                <div class="border-t pt-4">
                    <h5 class="font-medium text-gray-700 mb-2">Parameters</h5>
                    <div class="space-y-1 text-xs">
                        <div class="flex justify-between">
                            <span>Base Frequency:</span>
                            <span class="font-mono">${params.base_frequency.toFixed(2)} Hz</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Coupling Strength:</span>
                            <span class="font-mono">${params.coupling_strength.toFixed(3)}</span>
                        </div>
                        <div class="flex justify-between">
                            <span>Damping Factor:</span>
                            <span class="font-mono">${params.damping_factor.toFixed(3)}</span>
                        </div>
                    </div>
                </div>
            </div>
        `;
        
        document.getElementById('particleDetails').innerHTML = detailsHtml;
        
        // Update dimensional chart
        this.updateDimensionalChart(particle);
    }
    
    clearParticleDetails() {
        document.getElementById('particleDetails').innerHTML = `
            <div class="text-center text-gray-500 py-8">
                <i data-lucide="mouse-pointer-click" class="w-8 h-8 mx-auto mb-2 opacity-50"></i>
                <p>Click on a particle to analyze</p>
            </div>
        `;
        lucide.createIcons();
    }
    
    updateSystemMetrics(data) {
        if (!data) {
            document.getElementById('particleCount').textContent = '0';
            document.getElementById('totalEnergy').textContent = '0.00';
            document.getElementById('avgStability').textContent = '0.0%';
            document.getElementById('simulationFPS').textContent = '0';
            document.getElementById('simulationTime').textContent = '0.0s';
            return;
        }
        
        const metrics = data.global_metrics;
        
        document.getElementById('particleCount').textContent = data.oscillator_count;
        document.getElementById('totalEnergy').textContent = metrics.total_energy.toFixed(2);
        document.getElementById('avgStability').textContent = (metrics.average_stability * 100).toFixed(1) + '%';
        document.getElementById('simulationFPS').textContent = metrics.current_fps.toFixed(0);
        document.getElementById('simulationTime').textContent = data.simulation_time.toFixed(1) + 's';
    }
    
    updatePerformanceData(data) {
        const now = Date.now();
        const metrics = data.global_metrics;
        
        this.performanceData.timestamps.push(now);
        this.performanceData.fps.push(metrics.current_fps);
        this.performanceData.energy.push(metrics.total_energy);
        this.performanceData.stability.push(metrics.average_stability * 100);
        
        // Keep only last 50 data points
        const maxPoints = 50;
        if (this.performanceData.timestamps.length > maxPoints) {
            Object.keys(this.performanceData).forEach(key => {
                this.performanceData[key] = this.performanceData[key].slice(-maxPoints);
            });
        }
        
        // Update performance chart
        this.updatePerformanceChart();
    }
    
    initializeCharts() {
        // Dimensional Chart
        const dimensionalCtx = document.getElementById('dimensionalChart').getContext('2d');
        this.dimensionalChart = new Chart(dimensionalCtx, {
            type: 'radar',
            data: {
                labels: ['w₁ Projection', 'w₂ Energy', 'w₃ Spin', 'w₄ Mass'],
                datasets: [{
                    label: 'Current State',
                    data: [0, 0, 0, 0],
                    backgroundColor: 'rgba(59, 130, 246, 0.2)',
                    borderColor: 'rgba(59, 130, 246, 1)',
                    borderWidth: 2,
                    pointBackgroundColor: 'rgba(59, 130, 246, 1)',
                    pointBorderColor: '#fff',
                    pointHoverBackgroundColor: '#fff',
                    pointHoverBorderColor: 'rgba(59, 130, 246, 1)'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                scales: {
                    r: {
                        beginAtZero: true,
                        max: 2,
                        min: -2
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
        
        // Performance Chart
        const performanceCtx = document.getElementById('performanceChart').getContext('2d');
        this.performanceChart = new Chart(performanceCtx, {
            type: 'line',
            data: {
                labels: [],
                datasets: [
                    {
                        label: 'FPS',
                        data: [],
                        borderColor: 'rgba(59, 130, 246, 1)',
                        backgroundColor: 'rgba(59, 130, 246, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y'
                    },
                    {
                        label: 'Total Energy',
                        data: [],
                        borderColor: 'rgba(239, 68, 68, 1)',
                        backgroundColor: 'rgba(239, 68, 68, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y1'
                    },
                    {
                        label: 'Avg Stability %',
                        data: [],
                        borderColor: 'rgba(16, 185, 129, 1)',
                        backgroundColor: 'rgba(16, 185, 129, 0.1)',
                        borderWidth: 2,
                        fill: false,
                        yAxisID: 'y2'
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    x: {
                        display: false
                    },
                    y: {
                        type: 'linear',
                        display: true,
                        position: 'left',
                        title: {
                            display: true,
                            text: 'FPS'
                        }
                    },
                    y1: {
                        type: 'linear',
                        display: false,
                        position: 'right'
                    },
                    y2: {
                        type: 'linear',
                        display: false,
                        position: 'right'
                    }
                }
            }
        });
    }
    
    updateDimensionalChart(particle) {
        if (!this.dimensionalChart || !particle) return;
        
        const state = particle.state;
        this.dimensionalChart.data.datasets[0].data = [
            state.w1_projection,
            state.w2_energy,
            state.w3_spin,
            state.w4_mass
        ];
        
        this.dimensionalChart.update('none');
    }
    
    updatePerformanceChart() {
        if (!this.performanceChart) return;
        
        const labels = this.performanceData.timestamps.map((_, i) => i);
        
        this.performanceChart.data.labels = labels;
        this.performanceChart.data.datasets[0].data = this.performanceData.fps;
        this.performanceChart.data.datasets[1].data = this.performanceData.energy;
        this.performanceChart.data.datasets[2].data = this.performanceData.stability;
        
        this.performanceChart.update('none');
    }
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    window.particleApp = new ParticleOscillationApp();
});