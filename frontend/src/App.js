import React, { useState, useEffect } from 'react';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Badge } from './components/ui/badge';
import { Progress } from './components/ui/progress';
import { Separator } from './components/ui/separator';
import { Alert, AlertDescription } from './components/ui/alert';
import { 
  Play, 
  Pause, 
  RotateCcw, 
  Plus, 
  Trash2, 
  Atom, 
  Zap, 
  Activity,
  Settings,
  Info
} from 'lucide-react';
import './App.css';

const BACKEND_URL = process.env.REACT_APP_BACKEND_URL;

function App() {
  const [simulationState, setSimulationState] = useState({
    oscillators: {},
    oscillator_count: 0,
    simulation_time: 0,
    is_running: false,
    global_metrics: {
      total_energy: 0,
      average_stability: 0,
      current_fps: 0
    }
  });
  const [isConnected, setIsConnected] = useState(false);
  const [selectedParticle, setSelectedParticle] = useState(null);

  // Check connection and fetch initial state
  useEffect(() => {
    checkConnection();
    const interval = setInterval(() => {
      if (simulationState.is_running) {
        fetchSimulationState();
      }
    }, 1000);
    
    return () => clearInterval(interval);
  }, [simulationState.is_running]);

  const checkConnection = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/status`);
      const data = await response.json();
      setIsConnected(true);
      fetchSimulationState();
    } catch (error) {
      setIsConnected(false);
      console.error('Connection error:', error);
    }
  };

  const fetchSimulationState = async () => {
    try {
      const response = await fetch(`${BACKEND_URL}/api/simulation/state`);
      const data = await response.json();
      setSimulationState(data);
    } catch (error) {
      console.error('Fetch error:', error);
    }
  };

  const startSimulation = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/simulation/start`, { method: 'POST' });
      fetchSimulationState();
    } catch (error) {
      console.error('Start error:', error);
    }
  };

  const stopSimulation = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/simulation/stop`, { method: 'POST' });
      fetchSimulationState();
    } catch (error) {
      console.error('Stop error:', error);
    }
  };

  const resetSimulation = async () => {
    try {
      await fetch(`${BACKEND_URL}/api/simulation/reset`, { method: 'POST' });
      setSelectedParticle(null);
      fetchSimulationState();
    } catch (error) {
      console.error('Reset error:', error);
    }
  };

  const createParticle = async () => {
    try {
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
      
      await fetch(`${BACKEND_URL}/api/oscillators/create`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ parameters: randomParams })
      });
      
      fetchSimulationState();
    } catch (error) {
      console.error('Create particle error:', error);
    }
  };

  const deleteParticle = async (particleId) => {
    try {
      await fetch(`${BACKEND_URL}/api/oscillators/${particleId}`, { method: 'DELETE' });
      if (selectedParticle === particleId) {
        setSelectedParticle(null);
      }
      fetchSimulationState();
    } catch (error) {
      console.error('Delete particle error:', error);
    }
  };

  const ParticleVisualization = ({ particleId, particle }) => {
    const state = particle.state;
    const props = particle.derived_properties;
    
    const w1_norm = Math.max(0, Math.min(1, (state.w1_projection + 2) / 4));
    const w2_norm = Math.max(0, Math.min(1, (state.w2_energy + 2) / 4));
    const w3_norm = Math.max(0, Math.min(1, (state.w3_spin + 2) / 4));
    const w4_norm = Math.max(0, Math.min(1, (state.w4_mass + 2) / 4));
    
    const stabilityColor = props.stability_factor > 0.8 ? 'green' : 
                          props.stability_factor > 0.5 ? 'yellow' : 'red';
    
    const isSelected = selectedParticle === particleId;
    
    return (
      <div 
        className={`relative p-4 rounded-lg border-2 transition-all duration-300 cursor-pointer hover:shadow-lg ${
          isSelected ? 'border-blue-500 shadow-blue-500/20' : 'border-gray-300 hover:border-gray-400'
        }`}
        onClick={() => setSelectedParticle(particleId)}
      >
        <div className="flex justify-between items-center mb-3">
          <div className="text-xs font-mono text-gray-500">{particleId.substring(0, 12)}...</div>
          <div className="flex items-center space-x-1">
            <div className={`w-2 h-2 bg-${stabilityColor}-500 rounded-full`}></div>
            <span className={`text-xs text-${stabilityColor}-600`}>
              {(props.stability_factor * 100).toFixed(0)}%
            </span>
          </div>
        </div>
        
        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">w₁ (Projection)</span>
            <span className="text-xs font-mono">{state.w1_projection.toFixed(2)}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-blue-500 transition-all duration-200" 
                 style={{width: `${w1_norm * 100}%`}}></div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">w₂ (Energy)</span>
            <span className="text-xs font-mono">{state.w2_energy.toFixed(2)}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-red-500 transition-all duration-200" 
                 style={{width: `${w2_norm * 100}%`}}></div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">w₃ (Spin)</span>
            <span className="text-xs font-mono">{state.w3_spin.toFixed(2)}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-green-500 transition-all duration-200" 
                 style={{width: `${w3_norm * 100}%`}}></div>
          </div>
          
          <div className="flex items-center justify-between">
            <span className="text-xs text-gray-600">w₄ (Mass)</span>
            <span className="text-xs font-mono">{state.w4_mass.toFixed(2)}</span>
          </div>
          <div className="h-2 bg-gray-200 rounded-full overflow-hidden">
            <div className="h-full bg-purple-500 transition-all duration-200" 
                 style={{width: `${w4_norm * 100}%`}}></div>
          </div>
        </div>
        
        <div className="flex justify-between items-center mt-3 pt-2 border-t border-gray-100">
          <div className="text-center">
            <div className="text-xs font-semibold text-gray-700">{props.energy_total.toFixed(2)}</div>
            <div className="text-xs text-gray-500">Energy</div>
          </div>
          <div className="text-center">
            <div className="text-xs font-semibold text-gray-700">{(props.phase_coherence * 100).toFixed(0)}%</div>
            <div className="text-xs text-gray-500">Coherence</div>
          </div>
        </div>
        
        <Button
          variant="destructive"
          size="sm"
          className="absolute top-1 right-1 w-6 h-6 p-0 opacity-0 hover:opacity-100 transition-opacity"
          onClick={(e) => {
            e.stopPropagation();
            deleteParticle(particleId);
          }}
        >
          <Trash2 className="w-3 h-3" />
        </Button>
      </div>
    );
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-slate-50 to-blue-50">
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center py-4">
            <div className="flex items-center space-x-3">
              <div className="w-12 h-12 bg-gradient-to-r from-blue-600 via-purple-600 to-green-600 rounded-xl flex items-center justify-center">
                <Atom className="w-7 h-7 text-white" />
              </div>
              <div>
                <h1 className="text-2xl font-bold text-gray-900">Particle Oscillation Simulation</h1>
                <p className="text-sm text-gray-600">4D Tetrahedron Dynamics - MMU Theory</p>
              </div>
            </div>
            
            <div className="flex items-center space-x-2">
              <Badge variant={isConnected ? "default" : "destructive"}>
                {isConnected ? "Connected" : "Disconnected"}
              </Badge>
            </div>
          </div>
        </div>
      </header>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <Card className="mb-8">
          <CardHeader>
            <div className="flex justify-between items-center">
              <CardTitle className="flex items-center space-x-2">
                <Settings className="w-5 h-5" />
                <span>Simulation Controls</span>
              </CardTitle>
              <div className="flex space-x-2">
                <Button
                  onClick={simulationState.is_running ? stopSimulation : startSimulation}
                  variant={simulationState.is_running ? "destructive" : "default"}
                  size="sm"
                >
                  {simulationState.is_running ? (
                    <>
                      <Pause className="w-4 h-4 mr-2" />
                      Stop
                    </>
                  ) : (
                    <>
                      <Play className="w-4 h-4 mr-2" />
                      Start
                    </>
                  )}
                </Button>
                <Button onClick={resetSimulation} variant="outline" size="sm">
                  <RotateCcw className="w-4 h-4 mr-2" />
                  Reset
                </Button>
                <Button onClick={createParticle} variant="outline" size="sm">
                  <Plus className="w-4 h-4 mr-2" />
                  Create Particle
                </Button>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div className="text-center">
                <div className="text-2xl font-bold text-blue-600">{simulationState.oscillator_count}</div>
                <div className="text-sm text-gray-600">Active Particles</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-red-600">
                  {simulationState.global_metrics.total_energy.toFixed(2)}
                </div>
                <div className="text-sm text-gray-600">Total Energy</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-green-600">
                  {(simulationState.global_metrics.average_stability * 100).toFixed(1)}%
                </div>
                <div className="text-sm text-gray-600">Avg Stability</div>
              </div>
              <div className="text-center">
                <div className="text-2xl font-bold text-purple-600">
                  {simulationState.simulation_time.toFixed(1)}s
                </div>
                <div className="text-sm text-gray-600">Simulation Time</div>
              </div>
            </div>
          </CardContent>
        </Card>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Activity className="w-5 h-5" />
                  <span>4D Particle Oscillations</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {simulationState.oscillator_count === 0 ? (
                  <Alert>
                    <Info className="h-4 w-4" />
                    <AlertDescription>
                      No particles created yet. Click "Create Particle" to start the simulation.
                    </AlertDescription>
                  </Alert>
                ) : (
                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                    {Object.entries(simulationState.oscillators).map(([id, particle]) => (
                      <ParticleVisualization
                        key={id}
                        particleId={id}
                        particle={particle}
                      />
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>

          <div>
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center space-x-2">
                  <Zap className="w-5 h-5" />
                  <span>Particle Analysis</span>
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedParticle && simulationState.oscillators[selectedParticle] ? (
                  <div className="space-y-4">
                    {(() => {
                      const particle = simulationState.oscillators[selectedParticle];
                      const state = particle.state;
                      const props = particle.derived_properties;
                      const params = particle.parameters;
                      
                      return (
                        <>
                          <div>
                            <h3 className="font-semibold text-lg mb-2">
                              Particle {selectedParticle.substring(0, 8)}
                            </h3>
                            <Badge className={
                              props.stability_factor > 0.8 ? "bg-green-500" :
                              props.stability_factor > 0.5 ? "bg-yellow-500" : "bg-red-500"
                            }>
                              Stability: {(props.stability_factor * 100).toFixed(1)}%
                            </Badge>
                          </div>
                          
                          <Separator />
                          
                          <div className="grid grid-cols-2 gap-3">
                            <div className="bg-blue-50 p-3 rounded-lg">
                              <div className="text-sm font-medium text-blue-700">w₁ Projection</div>
                              <div className="text-lg font-bold text-blue-900">{state.w1_projection.toFixed(3)}</div>
                            </div>
                            <div className="bg-red-50 p-3 rounded-lg">
                              <div className="text-sm font-medium text-red-700">w₂ Energy</div>
                              <div className="text-lg font-bold text-red-900">{state.w2_energy.toFixed(3)}</div>
                            </div>
                            <div className="bg-green-50 p-3 rounded-lg">
                              <div className="text-sm font-medium text-green-700">w₃ Spin</div>
                              <div className="text-lg font-bold text-green-900">{state.w3_spin.toFixed(3)}</div>
                            </div>
                            <div className="bg-purple-50 p-3 rounded-lg">
                              <div className="text-sm font-medium text-purple-700">w₄ Mass</div>
                              <div className="text-lg font-bold text-purple-900">{state.w4_mass.toFixed(3)}</div>
                            </div>
                          </div>
                          
                          <Separator />
                          
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Derived Properties</h5>
                            <div className="space-y-2 text-sm">
                              <div className="flex justify-between">
                                <span>State Magnitude:</span>
                                <span className="font-mono">{props.state_magnitude.toFixed(3)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Total Energy:</span>
                                <span className="font-mono">{props.energy_total.toFixed(3)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Phase Coherence:</span>
                                <span className="font-mono">{(props.phase_coherence * 100).toFixed(1)}%</span>
                              </div>
                            </div>
                          </div>
                          
                          <Separator />
                          
                          <div>
                            <h5 className="font-medium text-gray-700 mb-2">Parameters</h5>
                            <div className="space-y-1 text-xs">
                              <div className="flex justify-between">
                                <span>Base Frequency:</span>
                                <span className="font-mono">{params.base_frequency.toFixed(2)} Hz</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Coupling Strength:</span>
                                <span className="font-mono">{params.coupling_strength.toFixed(3)}</span>
                              </div>
                              <div className="flex justify-between">
                                <span>Damping Factor:</span>
                                <span className="font-mono">{params.damping_factor.toFixed(3)}</span>
                              </div>
                            </div>
                          </div>
                        </>
                      );
                    })()}
                  </div>
                ) : (
                  <div className="text-center text-gray-500 py-8">
                    <Activity className="w-12 h-12 mx-auto mb-3 opacity-30" />
                    <p>Select a particle to view detailed analysis</p>
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </div>
    </div>
  );
}

export default App;