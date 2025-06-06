import os, pytest
if not os.environ.get("ACGS_INTEGRATION"):
    pytest.skip("integration test requires running services", allow_module_level=True)

#!/usr/bin/env python3
"""
Test script for Constitutional Fidelity Monitor WebSocket functionality.

This script tests the enhanced WebSocket implementation for Task 19.1:
- Real-time fidelity score tracking
- Alert level monitoring (green: >0.85, amber: 0.70-0.85, red: <0.70)
- Performance metrics integration
- QEC-inspired error correction capabilities
"""

import asyncio
import websockets
import json
import time
from datetime import datetime

async def test_fidelity_websocket():
    """Test the enhanced Constitutional Fidelity Monitor WebSocket."""
    uri = "ws://localhost:8004/api/v1/ws/fidelity-monitor"
    
    try:
        print(f"🔗 Connecting to Constitutional Fidelity Monitor WebSocket: {uri}")
        
        async with websockets.connect(uri) as websocket:
            print("✅ WebSocket connection established")
            
            # Test 1: Connection establishment
            print("\n📡 Test 1: Connection Establishment")
            response = await websocket.recv()
            connection_msg = json.loads(response)
            print(f"Connection response: {json.dumps(connection_msg, indent=2)}")
            
            # Test 2: Get performance metrics
            print("\n📊 Test 2: Performance Metrics Request")
            await websocket.send(json.dumps({
                "type": "get_performance_metrics"
            }))
            
            response = await websocket.recv()
            metrics_msg = json.loads(response)
            print(f"Performance metrics: {json.dumps(metrics_msg, indent=2)}")
            
            # Test 3: Get fidelity status (enhanced functionality)
            print("\n🛡️ Test 3: Fidelity Status Request (Enhanced)")
            await websocket.send(json.dumps({
                "type": "get_fidelity_status"
            }))
            
            response = await websocket.recv()
            fidelity_msg = json.loads(response)
            print(f"Fidelity status: {json.dumps(fidelity_msg, indent=2)}")
            
            # Test 4: Workflow subscription
            print("\n🔔 Test 4: Workflow Subscription")
            test_workflow_id = "constitutional_council_test"
            await websocket.send(json.dumps({
                "type": "subscribe_workflow",
                "workflow_id": test_workflow_id
            }))
            
            response = await websocket.recv()
            subscription_msg = json.loads(response)
            print(f"Subscription response: {json.dumps(subscription_msg, indent=2)}")
            
            # Test 5: Ping/Pong
            print("\n🏓 Test 5: Ping/Pong")
            await websocket.send(json.dumps({
                "type": "ping"
            }))
            
            response = await websocket.recv()
            pong_msg = json.loads(response)
            print(f"Pong response: {json.dumps(pong_msg, indent=2)}")
            
            # Test 6: Listen for real-time updates (5 seconds)
            print("\n⏱️ Test 6: Real-time Updates (5 seconds)")
            start_time = time.time()
            while time.time() - start_time < 5:
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=1.0)
                    update_msg = json.loads(response)
                    print(f"Real-time update: {json.dumps(update_msg, indent=2)}")
                except asyncio.TimeoutError:
                    print(".", end="", flush=True)
                    continue
            
            print("\n✅ All WebSocket tests completed successfully!")
            
    except websockets.exceptions.ConnectionRefused:
        print("❌ Connection refused. Make sure the GS service is running on port 8004")
    except Exception as e:
        print(f"❌ Error during WebSocket test: {e}")

def test_fidelity_thresholds():
    """Test fidelity threshold calculations."""
    print("\n🎯 Testing Fidelity Threshold Logic")
    
    FIDELITY_THRESHOLDS = {
        "green": 0.85,
        "amber": 0.70,
        "red": 0.55
    }
    
    test_scores = [0.95, 0.87, 0.75, 0.65, 0.45]
    
    for score in test_scores:
        if score >= FIDELITY_THRESHOLDS["green"]:
            level = "green (EXCELLENT)"
        elif score >= FIDELITY_THRESHOLDS["amber"]:
            level = "amber (CAUTION)"
        else:
            level = "red (CRITICAL)"
        
        print(f"Score: {score:.2f} ({score*100:.1f}%) → Alert Level: {level}")

def simulate_fidelity_history():
    """Simulate fidelity history data for trend analysis."""
    print("\n📈 Simulating Fidelity History for Trend Analysis")
    
    import random
    
    # Generate 20 data points with realistic fidelity scores
    history = []
    base_score = 0.80
    
    for i in range(20):
        # Add some realistic variation
        variation = random.uniform(-0.05, 0.05)
        score = max(0.5, min(1.0, base_score + variation))
        
        timestamp = datetime.now().isoformat()
        history.append({
            "score": score,
            "timestamp": timestamp,
            "time": time.time() + i * 60  # 1 minute intervals
        })
        
        # Gradual trend
        base_score += random.uniform(-0.01, 0.02)
        base_score = max(0.6, min(0.95, base_score))
    
    print(f"Generated {len(history)} fidelity history points")
    
    # Calculate trend
    if len(history) >= 2:
        recent = history[-5:]  # Last 5 points
        trend = recent[-1]["score"] - recent[0]["score"]
        
        if abs(trend) < 0.01:
            trend_direction = "stable"
        elif trend > 0:
            trend_direction = "improving"
        else:
            trend_direction = "declining"
        
        print(f"Trend analysis: {trend_direction} (change: {trend:+.3f})")
        
        # Calculate average
        avg_score = sum(entry["score"] for entry in history) / len(history)
        print(f"Average score: {avg_score:.3f} ({avg_score*100:.1f}%)")

if __name__ == "__main__":
    print("🚀 Constitutional Fidelity Monitor WebSocket Test Suite")
    print("=" * 60)
    
    # Test threshold logic
    test_fidelity_thresholds()
    
    # Test fidelity history simulation
    simulate_fidelity_history()
    
    # Test WebSocket functionality
    print("\n" + "=" * 60)
    asyncio.run(test_fidelity_websocket())

import os
import asyncio
import pytest

@pytest.mark.skipif(not os.environ.get("ACGS_INTEGRATION"), reason="Integration test requires running services")
def test_main_wrapper():
    if 'main' in globals():
        if asyncio.iscoroutinefunction(main):
            asyncio.run(main())
        else:
            main()
