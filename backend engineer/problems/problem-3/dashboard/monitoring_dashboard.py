"""
Real-time monitoring dashboard for performance metrics.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse
import logging

from core.monitoring import PerformanceMonitor
from services.cache_service import CacheService
from core.config import settings

logger = logging.getLogger(__name__)


class MonitoringDashboard:
    """Real-time monitoring dashboard."""
    
    def __init__(self, performance_monitor: PerformanceMonitor, cache_service: CacheService):
        self.performance_monitor = performance_monitor
        self.cache_service = cache_service
        self.connected_clients: List[WebSocket] = []
        self.dashboard_data = {
            "last_update": None,
            "metrics": {},
            "alerts": [],
            "system_status": "healthy"
        }
    
    async def add_client(self, websocket: WebSocket):
        """Add a new client to the dashboard."""
        await websocket.accept()
        self.connected_clients.append(websocket)
        logger.info(f"Client connected. Total clients: {len(self.connected_clients)}")
    
    async def remove_client(self, websocket: WebSocket):
        """Remove a client from the dashboard."""
        if websocket in self.connected_clients:
            self.connected_clients.remove(websocket)
        logger.info(f"Client disconnected. Total clients: {len(self.connected_clients)}")
    
    async def broadcast_update(self, data: Dict[str, Any]):
        """Broadcast data to all connected clients."""
        if not self.connected_clients:
            return
        
        message = json.dumps(data, default=str)
        disconnected_clients = []
        
        for client in self.connected_clients:
            try:
                await client.send_text(message)
            except Exception as e:
                logger.error(f"Error sending to client: {e}")
                disconnected_clients.append(client)
        
        # Remove disconnected clients
        for client in disconnected_clients:
            await self.remove_client(client)
    
    async def update_dashboard_data(self):
        """Update dashboard data with latest metrics."""
        try:
            # Get performance metrics
            performance_metrics = await self.performance_monitor.get_metrics()
            
            # Get cache statistics
            cache_stats = self.cache_service.get_stats()
            
            # Get system metrics
            system_metrics = await self._get_system_metrics()
            
            # Check for alerts
            alerts = await self._check_alerts(performance_metrics, cache_stats, system_metrics)
            
            # Update dashboard data
            self.dashboard_data.update({
                "last_update": datetime.utcnow().isoformat(),
                "metrics": {
                    "performance": performance_metrics,
                    "cache": cache_stats,
                    "system": system_metrics
                },
                "alerts": alerts,
                "system_status": self._determine_system_status(performance_metrics, alerts)
            })
            
            # Broadcast update to all clients
            await self.broadcast_update(self.dashboard_data)
            
        except Exception as e:
            logger.error(f"Error updating dashboard data: {e}")
    
    async def _get_system_metrics(self) -> Dict[str, Any]:
        """Get system-level metrics."""
        try:
            import psutil
            
            # CPU metrics
            cpu_percent = psutil.cpu_percent(interval=1)
            cpu_count = psutil.cpu_count()
            
            # Memory metrics
            memory = psutil.virtual_memory()
            memory_used_gb = memory.used / (1024**3)
            memory_total_gb = memory.total / (1024**3)
            memory_percent = memory.percent
            
            # Disk metrics
            disk = psutil.disk_usage('/')
            disk_used_gb = disk.used / (1024**3)
            disk_total_gb = disk.total / (1024**3)
            disk_percent = (disk.used / disk.total) * 100
            
            # Network metrics
            network = psutil.net_io_counters()
            
            return {
                "cpu": {
                    "percent": cpu_percent,
                    "count": cpu_count,
                    "load_average": psutil.getloadavg() if hasattr(psutil, 'getloadavg') else [0, 0, 0]
                },
                "memory": {
                    "used_gb": round(memory_used_gb, 2),
                    "total_gb": round(memory_total_gb, 2),
                    "percent": memory_percent,
                    "available_gb": round(memory.available / (1024**3), 2)
                },
                "disk": {
                    "used_gb": round(disk_used_gb, 2),
                    "total_gb": round(disk_total_gb, 2),
                    "percent": round(disk_percent, 2)
                },
                "network": {
                    "bytes_sent": network.bytes_sent,
                    "bytes_recv": network.bytes_recv,
                    "packets_sent": network.packets_sent,
                    "packets_recv": network.packets_recv
                }
            }
            
        except Exception as e:
            logger.error(f"Error getting system metrics: {e}")
            return {}
    
    async def _check_alerts(self, performance_metrics: Dict, cache_stats: Dict, system_metrics: Dict) -> List[Dict[str, Any]]:
        """Check for performance alerts."""
        alerts = []
        current_time = datetime.utcnow()
        
        try:
            # Check response time alerts
            response_times = performance_metrics.get("response_times", {})
            if response_times.get("p95", 0) > 1.0:  # P95 > 1 second
                alerts.append({
                    "type": "warning",
                    "message": f"High response time detected: P95 = {response_times.get('p95', 0):.3f}s",
                    "timestamp": current_time.isoformat(),
                    "severity": "medium"
                })
            
            # Check error rate alerts
            error_rates = performance_metrics.get("error_rates", {})
            for endpoint, rate in error_rates.items():
                if rate > 5.0:  # Error rate > 5%
                    alerts.append({
                        "type": "error",
                        "message": f"High error rate for {endpoint}: {rate:.1f}%",
                        "timestamp": current_time.isoformat(),
                        "severity": "high"
                    })
            
            # Check cache hit rate alerts
            cache_hit_rates = performance_metrics.get("cache_hit_rates", {})
            for cache_type, rate in cache_hit_rates.items():
                if rate < 50.0:  # Cache hit rate < 50%
                    alerts.append({
                        "type": "warning",
                        "message": f"Low cache hit rate for {cache_type}: {rate:.1f}%",
                        "timestamp": current_time.isoformat(),
                        "severity": "low"
                    })
            
            # Check memory usage alerts
            memory_percent = system_metrics.get("memory", {}).get("percent", 0)
            if memory_percent > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"High memory usage: {memory_percent:.1f}%",
                    "timestamp": current_time.isoformat(),
                    "severity": "critical"
                })
            elif memory_percent > 80:
                alerts.append({
                    "type": "warning",
                    "message": f"Elevated memory usage: {memory_percent:.1f}%",
                    "timestamp": current_time.isoformat(),
                    "severity": "medium"
                })
            
            # Check CPU usage alerts
            cpu_percent = system_metrics.get("cpu", {}).get("percent", 0)
            if cpu_percent > 90:
                alerts.append({
                    "type": "critical",
                    "message": f"High CPU usage: {cpu_percent:.1f}%",
                    "timestamp": current_time.isoformat(),
                    "severity": "critical"
                })
            elif cpu_percent > 80:
                alerts.append({
                    "type": "warning",
                    "message": f"Elevated CPU usage: {cpu_percent:.1f}%",
                    "timestamp": current_time.isoformat(),
                    "severity": "medium"
                })
            
            # Check database performance alerts
            db_performance = performance_metrics.get("database_performance", {})
            slow_query_rate = db_performance.get("slow_query_rate", 0)
            if slow_query_rate > 10:  # Slow query rate > 10%
                alerts.append({
                    "type": "warning",
                    "message": f"High slow query rate: {slow_query_rate:.1f}%",
                    "timestamp": current_time.isoformat(),
                    "severity": "medium"
                })
            
        except Exception as e:
            logger.error(f"Error checking alerts: {e}")
        
        return alerts
    
    def _determine_system_status(self, performance_metrics: Dict, alerts: List[Dict]) -> str:
        """Determine overall system status."""
        critical_alerts = [a for a in alerts if a.get("severity") == "critical"]
        high_alerts = [a for a in alerts if a.get("severity") == "high"]
        
        if critical_alerts:
            return "critical"
        elif high_alerts:
            return "degraded"
        else:
            return "healthy"
    
    async def start_monitoring_loop(self):
        """Start the monitoring loop."""
        while True:
            try:
                await self.update_dashboard_data()
                await asyncio.sleep(5)  # Update every 5 seconds
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                await asyncio.sleep(10)  # Wait longer on error


def create_dashboard_html() -> str:
    """Create HTML dashboard."""
    return """
    <!DOCTYPE html>
    <html>
    <head>
        <title>Performance Monitoring Dashboard</title>
        <meta charset="utf-8">
        <meta name="viewport" content="width=device-width, initial-scale=1">
        <style>
            body {
                font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
                margin: 0;
                padding: 20px;
                background-color: #f5f5f5;
            }
            .header {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                margin-bottom: 20px;
                text-align: center;
            }
            .status-indicator {
                display: inline-block;
                width: 12px;
                height: 12px;
                border-radius: 50%;
                margin-right: 8px;
            }
            .status-healthy { background-color: #4CAF50; }
            .status-degraded { background-color: #FF9800; }
            .status-critical { background-color: #F44336; }
            .metrics-grid {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
                gap: 20px;
                margin-bottom: 20px;
            }
            .metric-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .metric-title {
                font-size: 18px;
                font-weight: bold;
                margin-bottom: 10px;
                color: #333;
            }
            .metric-value {
                font-size: 24px;
                font-weight: bold;
                color: #667eea;
            }
            .metric-subtitle {
                font-size: 14px;
                color: #666;
                margin-top: 5px;
            }
            .alerts-section {
                background: white;
                padding: 20px;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }
            .alert {
                padding: 10px;
                margin: 10px 0;
                border-radius: 5px;
                border-left: 4px solid;
            }
            .alert-critical { background-color: #ffebee; border-left-color: #f44336; }
            .alert-high { background-color: #fff3e0; border-left-color: #ff9800; }
            .alert-warning { background-color: #fff8e1; border-left-color: #ffc107; }
            .chart-container {
                height: 200px;
                background: #f8f9fa;
                border-radius: 5px;
                display: flex;
                align-items: center;
                justify-content: center;
                color: #666;
            }
            .connection-status {
                position: fixed;
                top: 20px;
                right: 20px;
                padding: 10px 15px;
                border-radius: 20px;
                color: white;
                font-size: 12px;
            }
            .connected { background-color: #4CAF50; }
            .disconnected { background-color: #F44336; }
        </style>
    </head>
    <body>
        <div class="connection-status" id="connectionStatus">Connecting...</div>
        
        <div class="header">
            <h1>Performance Monitoring Dashboard</h1>
            <p>Real-time system performance metrics and alerts</p>
            <div>
                <span class="status-indicator" id="systemStatus"></span>
                <span id="systemStatusText">Loading...</span>
            </div>
        </div>
        
        <div class="metrics-grid" id="metricsGrid">
            <!-- Metrics will be populated by JavaScript -->
        </div>
        
        <div class="alerts-section">
            <h2>Alerts</h2>
            <div id="alertsContainer">
                <p>Loading alerts...</p>
            </div>
        </div>
        
        <script>
            let ws = null;
            let reconnectInterval = null;
            
            function connect() {
                const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
                const wsUrl = `${protocol}//${window.location.host}/ws/dashboard`;
                
                ws = new WebSocket(wsUrl);
                
                ws.onopen = function() {
                    console.log('Connected to dashboard');
                    document.getElementById('connectionStatus').textContent = 'Connected';
                    document.getElementById('connectionStatus').className = 'connection-status connected';
                    clearInterval(reconnectInterval);
                };
                
                ws.onmessage = function(event) {
                    const data = JSON.parse(event.data);
                    updateDashboard(data);
                };
                
                ws.onclose = function() {
                    console.log('Disconnected from dashboard');
                    document.getElementById('connectionStatus').textContent = 'Disconnected';
                    document.getElementById('connectionStatus').className = 'connection-status disconnected';
                    
                    // Reconnect after 5 seconds
                    reconnectInterval = setInterval(connect, 5000);
                };
                
                ws.onerror = function(error) {
                    console.error('WebSocket error:', error);
                };
            }
            
            function updateDashboard(data) {
                // Update system status
                const statusElement = document.getElementById('systemStatus');
                const statusTextElement = document.getElementById('systemStatusText');
                const systemStatus = data.system_status || 'unknown';
                
                statusElement.className = `status-indicator status-${systemStatus}`;
                statusTextElement.textContent = systemStatus.toUpperCase();
                
                // Update metrics
                updateMetrics(data.metrics);
                
                // Update alerts
                updateAlerts(data.alerts || []);
            }
            
            function updateMetrics(metrics) {
                const metricsGrid = document.getElementById('metricsGrid');
                
                if (!metrics) {
                    metricsGrid.innerHTML = '<p>No metrics available</p>';
                    return;
                }
                
                const performance = metrics.performance || {};
                const cache = metrics.cache || {};
                const system = metrics.system || {};
                
                let html = '';
                
                // Response times
                const responseTimes = performance.response_times || {};
                html += `
                    <div class="metric-card">
                        <div class="metric-title">Response Times</div>
                        <div class="metric-value">${(responseTimes.avg || 0).toFixed(3)}s</div>
                        <div class="metric-subtitle">P95: ${(responseTimes.p95 || 0).toFixed(3)}s | P99: ${(responseTimes.p99 || 0).toFixed(3)}s</div>
                    </div>
                `;
                
                // Cache hit rate
                const cacheHitRates = performance.cache_hit_rates || {};
                const avgCacheHitRate = Object.values(cacheHitRates).reduce((a, b) => a + b, 0) / Object.keys(cacheHitRates).length || 0;
                html += `
                    <div class="metric-card">
                        <div class="metric-title">Cache Hit Rate</div>
                        <div class="metric-value">${avgCacheHitRate.toFixed(1)}%</div>
                        <div class="metric-subtitle">Total hits: ${cache.hits || 0} | Misses: ${cache.misses || 0}</div>
                    </div>
                `;
                
                // Memory usage
                const memory = system.memory || {};
                html += `
                    <div class="metric-card">
                        <div class="metric-title">Memory Usage</div>
                        <div class="metric-value">${(memory.percent || 0).toFixed(1)}%</div>
                        <div class="metric-subtitle">${(memory.used_gb || 0).toFixed(1)}GB / ${(memory.total_gb || 0).toFixed(1)}GB</div>
                    </div>
                `;
                
                // CPU usage
                const cpu = system.cpu || {};
                html += `
                    <div class="metric-card">
                        <div class="metric-title">CPU Usage</div>
                        <div class="metric-value">${(cpu.percent || 0).toFixed(1)}%</div>
                        <div class="metric-subtitle">Load: ${(cpu.load_average || [0, 0, 0]).map(l => l.toFixed(2)).join(', ')}</div>
                    </div>
                `;
                
                // Database performance
                const dbPerformance = performance.database_performance || {};
                html += `
                    <div class="metric-card">
                        <div class="metric-title">Database Performance</div>
                        <div class="metric-value">${(dbPerformance.average_time || 0).toFixed(3)}s</div>
                        <div class="metric-subtitle">Queries: ${dbPerformance.total_queries || 0} | Slow: ${dbPerformance.slow_queries || 0}</div>
                    </div>
                `;
                
                // Throughput
                const throughput = performance.throughput || {};
                const totalThroughput = Object.values(throughput).reduce((a, b) => a + b, 0);
                html += `
                    <div class="metric-card">
                        <div class="metric-title">Throughput</div>
                        <div class="metric-value">${totalThroughput.toFixed(1)}</div>
                        <div class="metric-subtitle">Requests per second</div>
                    </div>
                `;
                
                metricsGrid.innerHTML = html;
            }
            
            function updateAlerts(alerts) {
                const alertsContainer = document.getElementById('alertsContainer');
                
                if (alerts.length === 0) {
                    alertsContainer.innerHTML = '<p style="color: #4CAF50;">No active alerts</p>';
                    return;
                }
                
                let html = '';
                alerts.forEach(alert => {
                    const severity = alert.severity || 'warning';
                    const timestamp = new Date(alert.timestamp).toLocaleString();
                    html += `
                        <div class="alert alert-${severity}">
                            <strong>${alert.type.toUpperCase()}</strong>: ${alert.message}
                            <br><small>${timestamp}</small>
                        </div>
                    `;
                });
                
                alertsContainer.innerHTML = html;
            }
            
            // Connect when page loads
            connect();
        </script>
    </body>
    </html>
    """
