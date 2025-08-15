from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import math
import random
import uuid
import time
import numpy as np
import os
from datetime import datetime

# Environment variables
CORS_ORIGINS = os.getenv("CORS_ORIGINS", "*").split(",")

app = FastAPI(title="Particle Oscillation Simulation API", version="1.0.0")

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Import the oscillation engine classes
class FourDimensionalState(BaseModel):
    w1_projection: float = 0.0
    w2_energy: float = 1.0
    w3_spin: float = 0.0
    w4_mass: float = 1.0
    
    def magnitude(self) -> float:
        return math.sqrt(self.w1_projection**2 + self.w2_energy**2 + 
                        self.w3_spin**2 + self.w4_mass**2)

class OscillationParameters(BaseModel):
    base_frequency: float = 1.0
    amplitude_w1: float = 1.0
    amplitude_w2: float = 1.5
    amplitude_w3: float = 0.8
    amplitude_w4: float = 1.2
    phase_w1: float = 0.0
    phase_w2: float = math.pi/4
    phase_w3: float = math.pi/2
    phase_w4: float = 3*math.pi/4
    damping_factor: float = 0.98
    coupling_strength: float = 0.1

class TetrahedronOscillator:
    def __init__(self, particle_id: str, params: OscillationParameters):
        self.particle_id = particle_id
        self.params = params
        self.creation_time = time.time()
        self.current_time = 0.0
        self.dt = 0.016
        
        self.current_state = FourDimensionalState()
        self.state_history = []
        self.max_history = 1000
        
        self.stability_factor = 1.0
        self.energy_total = 0.0
        self.phase_coherence = 1.0
        
    def update_oscillations(self, dt: float) -> None:
        self.current_time += dt
        t = self.current_time
        
        # Calculate base oscillations
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
        
        # Apply coupling
        coupling = self.params.coupling_strength
        
        w1_coupled = w1_base + coupling * (self.current_state.w2_energy * 0.3 + 
                                          self.current_state.w4_mass * 0.2)
        
        w2_coupled = w2_base + coupling * (self.current_state.w3_spin * 0.4 +
                                          self.current_state.w1_projection * 0.1)
        
        w3_coupled = w3_base + coupling * (self.current_state.w2_energy * 0.5) + \
                    0.3 * math.sin(6 * math.pi * self.params.base_frequency * t)
        
        w4_coupled = w4_base + coupling * (self.current_state.w1_projection * 0.15)
        
        # Apply damping
        damping = self.params.damping_factor
        
        self.current_state.w1_projection = w1_coupled * damping
        self.current_state.w2_energy = w2_coupled * damping
        self.current_state.w3_spin = w3_coupled * damping
        self.current_state.w4_mass = w4_coupled * damping
        
        self._calculate_stability()
        self._calculate_total_energy()
        self._calculate_phase_coherence()
        self._store_state_history()
    
    def _calculate_stability(self) -> None:
        state_magnitude = self.current_state.magnitude()
        
        if state_magnitude == 0:
            self.stability_factor = 0.0
            return
            
        w1_ratio = abs(self.current_state.w1_projection) / state_magnitude
        w2_ratio = abs(self.current_state.w2_energy) / state_magnitude
        w3_ratio = abs(self.current_state.w3_spin) / state_magnitude
        w4_ratio = abs(self.current_state.w4_mass) / state_magnitude
        
        balance_factor = 1.0 - abs(0.25 - w1_ratio) - abs(0.25 - w2_ratio) - \
                        abs(0.25 - w3_ratio) - abs(0.25 - w4_ratio)
        
        self.stability_factor = max(0.0, min(1.0, balance_factor))
    
    def _calculate_total_energy(self) -> None:
        kinetic = 0.5 * (self.current_state.w1_projection**2 + 
                        self.current_state.w2_energy**2 +
                        self.current_state.w3_spin**2 + 
                        self.current_state.w4_mass**2)
        
        potential = 0.25 * self.params.coupling_strength * (
            self.current_state.w1_projection * self.current_state.w2_energy +
            self.current_state.w2_energy * self.current_state.w3_spin +
            self.current_state.w3_spin * self.current_state.w4_mass +
            self.current_state.w4_mass * self.current_state.w1_projection
        )
        
        self.energy_total = kinetic + potential
    
    def _calculate_phase_coherence(self) -> None:
        if len(self.state_history) < 10:
            self.phase_coherence = 1.0
            return
            
        recent_states = self.state_history[-10:]
        phase_diffs = []
        
        for i in range(1, len(recent_states)):
            prev_state = recent_states[i-1][1]
            curr_state = recent_states[i][1]
            
            diff = abs(curr_state.w1_projection - prev_state.w1_projection) + \
                   abs(curr_state.w2_energy - prev_state.w2_energy) + \
                   abs(curr_state.w3_spin - prev_state.w3_spin) + \
                   abs(curr_state.w4_mass - prev_state.w4_mass)
            
            phase_diffs.append(diff)
        
        avg_diff = sum(phase_diffs) / len(phase_diffs)
        self.phase_coherence = max(0.0, min(1.0, 1.0 - avg_diff / 4.0))
    
    def _store_state_history(self) -> None:
        self.state_history.append((self.current_time, 
                                  FourDimensionalState(**self.current_state.model_dump())))
        
        if len(self.state_history) > self.max_history:
            self.state_history = self.state_history[-self.max_history:]
    
    def get_oscillation_data(self) -> Dict:
        return {
            'particle_id': self.particle_id,
            'timestamp': self.current_time,
            'state': self.current_state.model_dump(),
            'derived_properties': {
                'stability_factor': self.stability_factor,
                'energy_total': self.energy_total,
                'phase_coherence': self.phase_coherence,
                'state_magnitude': self.current_state.magnitude()
            },
            'parameters': self.params.model_dump()
        }

class ParticleOscillationSimulation:
    def __init__(self):
        self.oscillators = {}
        self.simulation_time = 0.0
        self.is_running = False
        self.update_rate = 60
        self.dt = 1.0 / self.update_rate
        self.global_coupling = 0.05
        self.environmental_noise = 0.01
        self.update_count = 0
        self.last_fps_time = time.time()
        self.current_fps = 0.0
    
    def create_oscillator(self, particle_id: str, params: Optional[OscillationParameters] = None) -> str:
        if params is None:
            params = OscillationParameters(
                base_frequency=random.uniform(0.5, 2.0),
                amplitude_w1=random.uniform(0.8, 1.2),
                amplitude_w2=random.uniform(1.0, 1.8),
                amplitude_w3=random.uniform(0.6, 1.0),
                amplitude_w4=random.uniform(1.0, 1.4),
                phase_w1=random.uniform(0, 2*math.pi),
                phase_w2=random.uniform(0, 2*math.pi),
                phase_w3=random.uniform(0, 2*math.pi),
                phase_w4=random.uniform(0, 2*math.pi),
                coupling_strength=random.uniform(0.05, 0.15)
            )
        
        oscillator = TetrahedronOscillator(particle_id, params)
        self.oscillators[particle_id] = oscillator
        return particle_id
    
    def remove_oscillator(self, particle_id: str) -> bool:
        if particle_id in self.oscillators:
            del self.oscillators[particle_id]
            return True
        return False
    
    def update_simulation(self) -> None:
        if not self.is_running:
            return
            
        self.simulation_time += self.dt
        
        for oscillator in self.oscillators.values():
            noise_factor = 1.0 + random.gauss(0, self.environmental_noise)
            modified_dt = self.dt * noise_factor
            oscillator.update_oscillations(modified_dt)
        
        self._update_performance_metrics()
    
    def _update_performance_metrics(self) -> None:
        self.update_count += 1
        current_time = time.time()
        if current_time - self.last_fps_time >= 1.0:
            self.current_fps = self.update_count / (current_time - self.last_fps_time)
            self.update_count = 0
            self.last_fps_time = current_time
    
    def start_simulation(self) -> None:
        self.is_running = True
    
    def stop_simulation(self) -> None:
        self.is_running = False
    
    def reset_simulation(self) -> None:
        self.simulation_time = 0.0
        self.is_running = False
        self.oscillators.clear()
    
    def get_simulation_state(self) -> Dict:
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

# Global simulation instance
simulation = ParticleOscillationSimulation()

# WebSocket connection manager
class ConnectionManager:
    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        if websocket in self.active_connections:
            self.active_connections.remove(websocket)

    async def broadcast(self, message: str):
        disconnected = []
        for connection in self.active_connections:
            try:
                await connection.send_text(message)
            except:
                disconnected.append(connection)
        
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Background simulation loop
async def simulation_loop():
    while True:
        try:
            simulation.update_simulation()
            
            if len(manager.active_connections) > 0:
                viz_data = simulation.get_simulation_state()
                await manager.broadcast(json.dumps({
                    'type': 'simulation_update',
                    'data': viz_data
                }))
            
            await asyncio.sleep(simulation.dt)
            
        except Exception as e:
            print(f"Simulation loop error: {e}")
            await asyncio.sleep(1)

@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

# API Endpoints
@app.get("/")
async def root():
    return {"message": "Particle Oscillation Simulation API", "version": "1.0.0"}

@app.get("/api/status")
async def get_api_status():
    state = simulation.get_simulation_state()
    return {
        "api_status": "running",
        "simulation_running": state['is_running'],
        "particle_count": state['oscillator_count'],
        "simulation_time": state['simulation_time'],
        "fps": state['global_metrics']['current_fps']
    }

@app.get("/api/simulation/state")
async def get_simulation_state():
    return simulation.get_simulation_state()

@app.post("/api/simulation/start")
async def start_simulation():
    simulation.start_simulation()
    return {"message": "Simulation started", "running": True}

@app.post("/api/simulation/stop") 
async def stop_simulation():
    simulation.stop_simulation()
    return {"message": "Simulation stopped", "running": False}

@app.post("/api/simulation/reset")
async def reset_simulation():
    simulation.reset_simulation()
    return {"message": "Simulation reset"}

@app.post("/api/oscillators/create")
async def create_oscillator(request: Optional[dict] = None):
    particle_id = f"particle_{int(time.time()*1000)}"
    
    params = None
    if request and 'parameters' in request:
        p = request['parameters']
        params = OscillationParameters(**p)
    
    created_id = simulation.create_oscillator(particle_id, params)
    
    return {
        "message": "Oscillator created",
        "particle_id": created_id,
        "parameters": simulation.oscillators[created_id].get_oscillation_data()['parameters']
    }

@app.delete("/api/oscillators/{particle_id}")
async def remove_oscillator(particle_id: str):
    success = simulation.remove_oscillator(particle_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Oscillator not found")
    
    return {"message": "Oscillator removed", "particle_id": particle_id}

@app.get("/api/oscillators")
async def get_all_oscillators():
    state = simulation.get_simulation_state()
    return {
        "oscillator_count": state['oscillator_count'],
        "oscillators": state['oscillators']
    }

@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        initial_state = simulation.get_simulation_state()
        await websocket.send_text(json.dumps({
            'type': 'initial_state',
            'data': initial_state
        }))
        
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message.get('type') == 'ping':
                    await websocket.send_text(json.dumps({
                        'type': 'pong',
                        'timestamp': time.time()
                    }))
                
            except WebSocketDisconnect:
                break
            except Exception as e:
                print(f"WebSocket error: {e}")
                break
                
    except WebSocketDisconnect:
        manager.disconnect(websocket)

if __name__ == "__main__":
    import uvicorn
    
    # Create some default oscillators
    for i in range(3):
        simulation.create_oscillator(f"default_particle_{i}")
    
    print("🌌 Starting Particle Oscillation Simulation API Server")
    print("🌐 Server available at http://localhost:8001")
    
    uvicorn.run(app, host="0.0.0.0", port=8001)