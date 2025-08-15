<?php

/**
 * Particle Oscillation Simulation - PHP API Server
 * RESTful API for 4D tetrahedron oscillation simulation
 */

require_once 'oscillation_engine.php';

// Enable CORS
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type, Authorization');
header('Content-Type: application/json');

// Handle preflight OPTIONS request
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(200);
    exit();
}

// Initialize simulation (using session for persistence)
session_start();
if (!isset($_SESSION['simulation'])) {
    $_SESSION['simulation'] = new ParticleOscillationSimulation();
}

$simulation = $_SESSION['simulation'];

// Parse request
$request_method = $_SERVER['REQUEST_METHOD'];
$request_uri = $_SERVER['REQUEST_URI'];
$path_info = parse_url($request_uri, PHP_URL_PATH);
$path_parts = explode('/', trim($path_info, '/'));

// Remove 'api.php' from path if present
if ($path_parts[0] === 'api.php') {
    array_shift($path_parts);
}

// Get request body for POST/PUT requests
$input = file_get_contents('php://input');
$request_data = json_decode($input, true) ?? [];

// Response helper function
function sendResponse(int $status_code, array $data): void {
    http_response_code($status_code);
    echo json_encode($data, JSON_PRETTY_PRINT);
    exit();
}

// Error handler
function handleError(string $message, int $status_code = 500): void {
    sendResponse($status_code, [
        'error' => true,
        'message' => $message,
        'timestamp' => date('c')
    ]);
}

// Route handler
try {
    // Root endpoint
    if (empty($path_parts) || $path_parts[0] === '') {
        sendResponse(200, [
            'message' => 'Particle Oscillation Simulation PHP API',
            'version' => '1.0.0',
            'endpoints' => [
                'GET /status' => 'API status',
                'GET /simulation/state' => 'Get simulation state',
                'POST /simulation/start' => 'Start simulation',
                'POST /simulation/stop' => 'Stop simulation',
                'POST /simulation/reset' => 'Reset simulation',
                'POST /oscillators/create' => 'Create oscillator',
                'GET /oscillators' => 'Get all oscillators',
                'GET /oscillators/{id}' => 'Get specific oscillator',
                'DELETE /oscillators/{id}' => 'Remove oscillator',
                'GET /visualization/data' => 'Get visualization data'
            ]
        ]);
    }
    
    // Status endpoint
    if ($path_parts[0] === 'status' && $request_method === 'GET') {
        $state = $simulation->getSimulationState();
        sendResponse(200, [
            'api_status' => 'running',
            'simulation_running' => $state['is_running'],
            'particle_count' => $state['oscillator_count'],
            'simulation_time' => $state['simulation_time'],
            'fps' => $state['global_metrics']['current_fps'],
            'php_version' => PHP_VERSION,
            'memory_usage' => memory_get_usage(true),
            'session_id' => session_id()
        ]);
    }
    
    // Simulation endpoints
    if ($path_parts[0] === 'simulation') {
        if (!isset($path_parts[1])) {
            handleError('Simulation endpoint requires action', 400);
        }
        
        switch ($path_parts[1]) {
            case 'state':
                if ($request_method === 'GET') {
                    // Update simulation before returning state
                    if ($simulation->is_running) {
                        $simulation->updateSimulation();
                    }
                    sendResponse(200, $simulation->getSimulationState());
                }
                break;
                
            case 'start':
                if ($request_method === 'POST') {
                    $simulation->startSimulation();
                    sendResponse(200, [
                        'message' => 'Simulation started',
                        'running' => true,
                        'timestamp' => date('c')
                    ]);
                }
                break;
                
            case 'stop':
                if ($request_method === 'POST') {
                    $simulation->stopSimulation();
                    sendResponse(200, [
                        'message' => 'Simulation stopped', 
                        'running' => false,
                        'timestamp' => date('c')
                    ]);
                }
                break;
                
            case 'reset':
                if ($request_method === 'POST') {
                    $simulation->resetSimulation();
                    sendResponse(200, [
                        'message' => 'Simulation reset',
                        'timestamp' => date('c')
                    ]);
                }
                break;
                
            case 'config':
                if ($request_method === 'POST') {
                    // Update simulation configuration
                    if (isset($request_data['global_coupling'])) {
                        $simulation->global_coupling = max(0.0, min(1.0, (float)$request_data['global_coupling']));
                    }
                    
                    if (isset($request_data['environmental_noise'])) {
                        $simulation->environmental_noise = max(0.0, min(0.1, (float)$request_data['environmental_noise']));
                    }
                    
                    if (isset($request_data['update_rate'])) {
                        $simulation->update_rate = max(10, min(120, (int)$request_data['update_rate']));
                        $simulation->dt = 1.0 / $simulation->update_rate;
                    }
                    
                    sendResponse(200, [
                        'message' => 'Configuration updated',
                        'config' => [
                            'global_coupling' => $simulation->global_coupling,
                            'environmental_noise' => $simulation->environmental_noise,
                            'update_rate' => $simulation->update_rate
                        ]
                    ]);
                }
                break;
                
            default:
                handleError('Unknown simulation action', 404);
        }
    }
    
    // Oscillator endpoints
    if ($path_parts[0] === 'oscillators') {
        switch ($request_method) {
            case 'GET':
                if (!isset($path_parts[1])) {
                    // Get all oscillators
                    $state = $simulation->getSimulationState();
                    sendResponse(200, [
                        'oscillator_count' => $state['oscillator_count'],
                        'oscillators' => $state['oscillators']
                    ]);
                } else {
                    // Get specific oscillator
                    $particle_id = $path_parts[1];
                    if (!isset($simulation->oscillators[$particle_id])) {
                        handleError('Oscillator not found', 404);
                    }
                    
                    // Check for history request
                    if (isset($path_parts[2]) && $path_parts[2] === 'history') {
                        $last_n = isset($_GET['last_n']) ? (int)$_GET['last_n'] : 100;
                        $history = $simulation->oscillators[$particle_id]->getHistoryData($last_n);
                        
                        sendResponse(200, [
                            'particle_id' => $particle_id,
                            'history_length' => count($history),
                            'history' => $history
                        ]);
                    } else {
                        sendResponse(200, $simulation->oscillators[$particle_id]->getOscillationData());
                    }
                }
                break;
                
            case 'POST':
                if (isset($path_parts[1]) && $path_parts[1] === 'create') {
                    // Create new oscillator
                    $particle_id = $request_data['particle_id'] ?? 'particle_' . time() . '_' . mt_rand(1000, 9999);
                    
                    $params = null;
                    if (isset($request_data['parameters'])) {
                        $p = $request_data['parameters'];
                        $params = new OscillationParameters(
                            base_frequency: $p['base_frequency'] ?? 1.0,
                            amplitude_w1: $p['amplitude_w1'] ?? 1.0,
                            amplitude_w2: $p['amplitude_w2'] ?? 1.5,
                            amplitude_w3: $p['amplitude_w3'] ?? 0.8,
                            amplitude_w4: $p['amplitude_w4'] ?? 1.2,
                            phase_w1: $p['phase_w1'] ?? 0.0,
                            phase_w2: $p['phase_w2'] ?? M_PI/4,
                            phase_w3: $p['phase_w3'] ?? M_PI/2,
                            phase_w4: $p['phase_w4'] ?? 3*M_PI/4,
                            damping_factor: $p['damping_factor'] ?? 0.98,
                            coupling_strength: $p['coupling_strength'] ?? 0.1
                        );
                    }
                    
                    $created_id = $simulation->createOscillator($particle_id, $params);
                    
                    sendResponse(201, [
                        'message' => 'Oscillator created',
                        'particle_id' => $created_id,
                        'parameters' => $simulation->oscillators[$created_id]->getOscillationData()['parameters']
                    ]);
                } else {
                    handleError('Invalid oscillator endpoint', 400);
                }
                break;
                
            case 'DELETE':
                if (!isset($path_parts[1])) {
                    handleError('Particle ID required for deletion', 400);
                }
                
                $particle_id = $path_parts[1];
                $success = $simulation->removeOscillator($particle_id);
                
                if (!$success) {
                    handleError('Oscillator not found', 404);
                }
                
                sendResponse(200, [
                    'message' => 'Oscillator removed',
                    'particle_id' => $particle_id
                ]);
                break;
                
            default:
                handleError('Method not allowed for oscillators endpoint', 405);
        }
    }
    
    // Visualization endpoint
    if ($path_parts[0] === 'visualization' && isset($path_parts[1]) && $path_parts[1] === 'data') {
        if ($request_method === 'GET') {
            // Update simulation before getting visualization data
            if ($simulation->is_running) {
                $simulation->updateSimulation();
            }
            sendResponse(200, $simulation->getVisualizationData());
        }
    }
    
    // Analytics endpoint
    if ($path_parts[0] === 'analytics' && isset($path_parts[1]) && $path_parts[1] === 'system') {
        if ($request_method === 'GET') {
            $state = $simulation->getSimulationState();
            $oscillators = $state['oscillators'];
            
            if (empty($oscillators)) {
                sendResponse(200, ['message' => 'No oscillators in simulation']);
            }
            
            // Calculate dimensional statistics
            $w1_values = array_column(array_column($oscillators, 'state'), 'w1_projection');
            $w2_values = array_column(array_column($oscillators, 'state'), 'w2_energy');
            $w3_values = array_column(array_column($oscillators, 'state'), 'w3_spin');
            $w4_values = array_column(array_column($oscillators, 'state'), 'w4_mass');
            
            $analytics = [
                'system_metrics' => $state['global_metrics'],
                'dimensional_statistics' => [
                    'w1_projection' => [
                        'mean' => array_sum($w1_values) / count($w1_values),
                        'min' => min($w1_values),
                        'max' => max($w1_values),
                        'range' => max($w1_values) - min($w1_values)
                    ],
                    'w2_energy' => [
                        'mean' => array_sum($w2_values) / count($w2_values),
                        'min' => min($w2_values),
                        'max' => max($w2_values),
                        'range' => max($w2_values) - min($w2_values)
                    ],
                    'w3_spin' => [
                        'mean' => array_sum($w3_values) / count($w3_values),
                        'min' => min($w3_values),
                        'max' => max($w3_values),
                        'range' => max($w3_values) - min($w3_values)
                    ],
                    'w4_mass' => [
                        'mean' => array_sum($w4_values) / count($w4_values),
                        'min' => min($w4_values),
                        'max' => max($w4_values),
                        'range' => max($w4_values) - min($w4_values)
                    ]
                ],
                'stability_distribution' => [
                    'high_stability' => count(array_filter($oscillators, function($osc) {
                        return $osc['derived_properties']['stability_factor'] > 0.8;
                    })),
                    'medium_stability' => count(array_filter($oscillators, function($osc) {
                        return $osc['derived_properties']['stability_factor'] >= 0.5 && 
                               $osc['derived_properties']['stability_factor'] <= 0.8;
                    })),
                    'low_stability' => count(array_filter($oscillators, function($osc) {
                        return $osc['derived_properties']['stability_factor'] < 0.5;
                    }))
                ]
            ];
            
            sendResponse(200, $analytics);
        }
    }
    
    // Health check endpoint
    if ($path_parts[0] === 'health') {
        if ($request_method === 'GET') {
            sendResponse(200, [
                'status' => 'healthy',
                'timestamp' => date('c'),
                'simulation_active' => $simulation->is_running,
                'php_version' => PHP_VERSION,
                'memory_usage' => [
                    'current' => memory_get_usage(true),
                    'peak' => memory_get_peak_usage(true)
                ],
                'session_active' => session_status() === PHP_SESSION_ACTIVE
            ]);
        }
    }
    
    // If no route matches
    handleError('Endpoint not found', 404);
    
} catch (Exception $e) {
    handleError('Internal server error: ' . $e->getMessage(), 500);
}

?>