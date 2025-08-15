from fastapi import FastAPI, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse, JSONResponse
from pydantic import BaseModel
from typing import List, Dict, Optional
import asyncio
import json
import time
import uvicorn
from datetime import datetime

from oscillation_engine import (
    ParticleOscillationSimulation, 
    OscillationParameters,
    FourDimensionalState
)

app = FastAPI(
    title="Particle Oscillation Simulation API",
    description="Real-time 4D tetrahedron oscillation simulation based on MMU theory",
    version="1.0.0"
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

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
        
        # Remove disconnected clients
        for conn in disconnected:
            self.disconnect(conn)

manager = ConnectionManager()

# Pydantic models for API
class OscillationParamsModel(BaseModel):
    base_frequency: float = 1.0
    amplitude_w1: float = 1.0
    amplitude_w2: float = 1.5
    amplitude_w3: float = 0.8
    amplitude_w4: float = 1.2
    phase_w1: float = 0.0
    phase_w2: float = 0.785  # π/4
    phase_w3: float = 1.571  # π/2
    phase_w4: float = 2.356  # 3π/4
    damping_factor: float = 0.98
    coupling_strength: float = 0.1

class CreateOscillatorRequest(BaseModel):
    particle_id: Optional[str] = None
    parameters: Optional[OscillationParamsModel] = None

class SimulationConfigRequest(BaseModel):
    global_coupling: Optional[float] = None
    environmental_noise: Optional[float] = None
    update_rate: Optional[int] = None

# Background task for continuous simulation updates
async def simulation_loop():
    """Background task to continuously update simulation"""
    while True:
        try:
            simulation.update_simulation()
            
            # Broadcast updates to connected clients
            if len(manager.active_connections) > 0:
                viz_data = simulation.get_visualization_data()
                await manager.broadcast(json.dumps({
                    'type': 'simulation_update',
                    'data': viz_data
                }))
            
            await asyncio.sleep(simulation.dt)
            
        except Exception as e:
            print(f"Simulation loop error: {e}")
            await asyncio.sleep(1)

# Start background simulation loop
@app.on_event("startup")
async def startup_event():
    asyncio.create_task(simulation_loop())

# API Endpoints

@app.get("/")
async def root():
    return {"message": "Particle Oscillation Simulation API", "version": "1.0.0"}

@app.get("/api/status")
async def get_api_status():
    """Get API and simulation status"""
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
    """Get complete simulation state"""
    return simulation.get_simulation_state()

@app.post("/api/simulation/start")
async def start_simulation():
    """Start the oscillation simulation"""
    simulation.start_simulation()
    return {"message": "Simulation started", "running": True}

@app.post("/api/simulation/stop") 
async def stop_simulation():
    """Stop the oscillation simulation"""
    simulation.stop_simulation()
    return {"message": "Simulation stopped", "running": False}

@app.post("/api/simulation/reset")
async def reset_simulation():
    """Reset simulation to initial state"""
    simulation.reset_simulation()
    return {"message": "Simulation reset"}

@app.post("/api/simulation/config")
async def update_simulation_config(config: SimulationConfigRequest):
    """Update global simulation configuration"""
    if config.global_coupling is not None:
        simulation.global_coupling = max(0.0, min(1.0, config.global_coupling))
    
    if config.environmental_noise is not None:
        simulation.environmental_noise = max(0.0, min(0.1, config.environmental_noise))
    
    if config.update_rate is not None:
        simulation.update_rate = max(10, min(120, config.update_rate))
        simulation.dt = 1.0 / simulation.update_rate
    
    return {"message": "Configuration updated", "config": {
        "global_coupling": simulation.global_coupling,
        "environmental_noise": simulation.environmental_noise,
        "update_rate": simulation.update_rate
    }}

@app.post("/api/oscillators/create")
async def create_oscillator(request: CreateOscillatorRequest):
    """Create new tetrahedron oscillator"""
    # Generate particle ID if not provided
    particle_id = request.particle_id or f"particle_{int(time.time()*1000)}"
    
    # Convert parameters if provided
    params = None
    if request.parameters:
        params = OscillationParameters(
            base_frequency=request.parameters.base_frequency,
            amplitude_w1=request.parameters.amplitude_w1,
            amplitude_w2=request.parameters.amplitude_w2,
            amplitude_w3=request.parameters.amplitude_w3,
            amplitude_w4=request.parameters.amplitude_w4,
            phase_w1=request.parameters.phase_w1,
            phase_w2=request.parameters.phase_w2,
            phase_w3=request.parameters.phase_w3,
            phase_w4=request.parameters.phase_w4,
            damping_factor=request.parameters.damping_factor,
            coupling_strength=request.parameters.coupling_strength
        )
    
    created_id = simulation.create_oscillator(particle_id, params)
    
    return {
        "message": "Oscillator created",
        "particle_id": created_id,
        "parameters": simulation.oscillators[created_id].get_oscillation_data()['parameters']
    }

@app.delete("/api/oscillators/{particle_id}")
async def remove_oscillator(particle_id: str):
    """Remove oscillator from simulation"""
    success = simulation.remove_oscillator(particle_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Oscillator not found")
    
    return {"message": "Oscillator removed", "particle_id": particle_id}

@app.get("/api/oscillators")
async def get_all_oscillators():
    """Get all oscillators in simulation"""
    state = simulation.get_simulation_state()
    return {
        "oscillator_count": state['oscillator_count'],
        "oscillators": state['oscillators']
    }

@app.get("/api/oscillators/{particle_id}")
async def get_oscillator(particle_id: str):
    """Get specific oscillator data"""
    if particle_id not in simulation.oscillators:
        raise HTTPException(status_code=404, detail="Oscillator not found")
    
    return simulation.oscillators[particle_id].get_oscillation_data()

@app.get("/api/oscillators/{particle_id}/history")
async def get_oscillator_history(particle_id: str, last_n: int = 100):
    """Get oscillator history data for analysis"""
    if particle_id not in simulation.oscillators:
        raise HTTPException(status_code=404, detail="Oscillator not found")
    
    history = simulation.oscillators[particle_id].get_history_data(last_n)
    
    return {
        "particle_id": particle_id,
        "history_length": len(history),
        "history": history
    }

@app.get("/api/visualization/data")
async def get_visualization_data():
    """Get data optimized for real-time visualization"""
    return simulation.get_visualization_data()

@app.get("/api/analytics/system")
async def get_system_analytics():
    """Get system-wide analytics and metrics"""
    state = simulation.get_simulation_state()
    
    # Calculate additional analytics
    oscillators = state['oscillators']
    
    if not oscillators:
        return {"message": "No oscillators in simulation"}
    
    # Dimensional analysis
    w1_values = [osc['state']['w1_projection'] for osc in oscillators.values()]
    w2_values = [osc['state']['w2_energy'] for osc in oscillators.values()]
    w3_values = [osc['state']['w3_spin'] for osc in oscillators.values()]
    w4_values = [osc['state']['w4_mass'] for osc in oscillators.values()]
    
    analytics = {
        "system_metrics": state['global_metrics'],
        "dimensional_statistics": {
            "w1_projection": {
                "mean": sum(w1_values) / len(w1_values),
                "min": min(w1_values),
                "max": max(w1_values),
                "range": max(w1_values) - min(w1_values)
            },
            "w2_energy": {
                "mean": sum(w2_values) / len(w2_values),
                "min": min(w2_values),
                "max": max(w2_values),
                "range": max(w2_values) - min(w2_values)
            },
            "w3_spin": {
                "mean": sum(w3_values) / len(w3_values),
                "min": min(w3_values),
                "max": max(w3_values),
                "range": max(w3_values) - min(w3_values)
            },
            "w4_mass": {
                "mean": sum(w4_values) / len(w4_values),
                "min": min(w4_values),
                "max": max(w4_values),
                "range": max(w4_values) - min(w4_values)
            }
        },
        "stability_distribution": {
            "high_stability": len([osc for osc in oscillators.values() 
                                 if osc['derived_properties']['stability_factor'] > 0.8]),
            "medium_stability": len([osc for osc in oscillators.values() 
                                   if 0.5 <= osc['derived_properties']['stability_factor'] <= 0.8]),
            "low_stability": len([osc for osc in oscillators.values() 
                                if osc['derived_properties']['stability_factor'] < 0.5])
        }
    }
    
    return analytics

# WebSocket endpoint for real-time updates
@app.websocket("/api/ws")
async def websocket_endpoint(websocket: WebSocket):
    await manager.connect(websocket)
    
    try:
        # Send initial state
        initial_state = simulation.get_simulation_state()
        await websocket.send_text(json.dumps({
            'type': 'initial_state',
            'data': initial_state
        }))
        
        # Keep connection alive and handle incoming messages
        while True:
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                # Handle client commands
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

# Health check endpoint
@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "simulation_active": simulation.is_running,
        "active_connections": len(manager.active_connections)
    }

if __name__ == "__main__":
    # Create some default oscillators for testing
    for i in range(3):
        simulation.create_oscillator(f"default_particle_{i}")
    
    print("🌌 Starting Particle Oscillation Simulation API Server")
    print("📊 Default particles created for testing")
    print("🌐 Server will be available at http://localhost:8002")
    print("📡 WebSocket endpoint: ws://localhost:8002/api/ws")
    print("📚 API documentation: http://localhost:8002/docs")
    
    uvicorn.run(
        "api_server:app",
        host="0.0.0.0",
        port=8002,
        reload=True,
        log_level="info"
    )