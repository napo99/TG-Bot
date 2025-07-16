#!/usr/bin/env python3
"""
Monitoring Dashboard - Real-time monitoring dashboard with ASCII display
Simple, practical dashboard for container monitoring and health status.
"""

import asyncio
import time
import json
import os
import curses
from typing import Dict, List, Optional, Any
from dataclasses import asdict
from datetime import datetime, timedelta

from docker_monitor import DockerMonitor
from container_health import ContainerHealthChecker

class MonitoringDashboard:
    """Simple real-time monitoring dashboard"""
    
    def __init__(self, log_dir: str = "/Users/screener-m3/projects/crypto-assistant/data/logs"):
        """Initialize monitoring dashboard"""
        self.log_dir = log_dir
        self.docker_monitor = DockerMonitor(log_dir)
        self.health_checker = ContainerHealthChecker(log_dir)
        
        # Dashboard state
        self.last_update = None
        self.update_interval = 30  # seconds
        self.auto_refresh = True
        
    def generate_ascii_dashboard(self) -> str:
        """Generate ASCII-based real-time dashboard"""
        try:
            # Get current time
            now = datetime.now()
            
            # Dashboard header
            lines = []
            lines.append("=" * 80)
            lines.append("🐳 DOCKER CONTAINER MONITORING DASHBOARD")
            lines.append("=" * 80)
            lines.append(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')} | Auto-refresh: {self.update_interval}s")
            lines.append("")
            
            # Quick system status
            try:
                import psutil
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=0.1)
                
                lines.append("🖥️  SYSTEM STATUS")
                lines.append(f"   Memory: {memory.percent:.1f}% used ({memory.used // 1024**2:,}MB / {memory.total // 1024**2:,}MB)")
                lines.append(f"   CPU: {cpu:.1f}%")
                lines.append("")
                
            except Exception as e:
                lines.append(f"🖥️  SYSTEM STATUS: Error getting metrics ({e})")
                lines.append("")
            
            # Container status (simplified for now)
            lines.append("📦 CONTAINER STATUS")
            lines.append("   Loading container metrics...")
            lines.append("")
            
            # Recent alerts placeholder
            lines.append("🚨 RECENT ALERTS")
            lines.append("   No active alerts")
            lines.append("")
            
            # Quick actions
            lines.append("⚡ QUICK ACTIONS")
            lines.append("   [R] Refresh Now  [Q] Quit  [H] Help")
            lines.append("")
            
            lines.append("=" * 80)
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error generating dashboard: {e}"

    async def get_live_metrics(self) -> Dict[str, Any]:
        """Get live metrics for dashboard"""
        try:
            # Get container metrics
            containers = await self.docker_monitor.monitor_all_containers()
            
            # Get system metrics
            system_metrics = {}
            try:
                import psutil
                memory = psutil.virtual_memory()
                cpu = psutil.cpu_percent(interval=0.1)
                disk = psutil.disk_usage('/')
                
                system_metrics = {
                    'memory_percent': memory.percent,
                    'memory_used_mb': memory.used // 1024**2,
                    'memory_total_mb': memory.total // 1024**2,
                    'cpu_percent': cpu,
                    'disk_percent': round((disk.used / disk.total) * 100, 1),
                    'disk_used_gb': round(disk.used / 1024**3, 1),
                    'disk_total_gb': round(disk.total / 1024**3, 1)
                }
            except:
                pass
            
            # Basic health check
            health_summary = {}
            try:
                # Quick health check without full analysis
                running_containers = [c for c in containers if c.status == 'running']
                healthy_containers = [c for c in containers if c.health_status == 'healthy']
                
                health_summary = {
                    'total_containers': len(containers),
                    'running_containers': len(running_containers),
                    'healthy_containers': len(healthy_containers),
                    'container_names': [c.name for c in containers]
                }
            except:
                pass
            
            return {
                'timestamp': datetime.now().isoformat(),
                'containers': [asdict(c) for c in containers],
                'system_metrics': system_metrics,
                'health_summary': health_summary
            }
            
        except Exception as e:
            return {'error': str(e), 'timestamp': datetime.now().isoformat()}

    def format_live_dashboard(self, metrics: Dict[str, Any]) -> str:
        """Format live metrics into dashboard display"""
        try:
            lines = []
            now = datetime.now()
            
            # Header
            lines.append("=" * 80)
            lines.append("🐳 DOCKER MONITORING DASHBOARD - LIVE")
            lines.append("=" * 80)
            lines.append(f"📅 {now.strftime('%Y-%m-%d %H:%M:%S')} | Next update: {self.update_interval}s")
            lines.append("")
            
            # System metrics
            system = metrics.get('system_metrics', {})
            if system:
                lines.append("🖥️  SYSTEM METRICS")
                
                # Memory bar
                memory_percent = system.get('memory_percent', 0)
                memory_bar = self._create_progress_bar(memory_percent, 50)
                lines.append(f"   Memory: {memory_bar} {memory_percent:.1f}%")
                lines.append(f"           {system.get('memory_used_mb', 0):,}MB / {system.get('memory_total_mb', 0):,}MB")
                
                # CPU
                cpu_percent = system.get('cpu_percent', 0)
                cpu_bar = self._create_progress_bar(cpu_percent, 50)
                lines.append(f"   CPU:    {cpu_bar} {cpu_percent:.1f}%")
                
                # Disk
                disk_percent = system.get('disk_percent', 0)
                disk_bar = self._create_progress_bar(disk_percent, 50)
                lines.append(f"   Disk:   {disk_bar} {disk_percent:.1f}%")
                lines.append(f"           {system.get('disk_used_gb', 0):.1f}GB / {system.get('disk_total_gb', 0):.1f}GB")
                
                lines.append("")
            
            # Container summary
            health = metrics.get('health_summary', {})
            if health:
                lines.append("📦 CONTAINER SUMMARY")
                total = health.get('total_containers', 0)
                running = health.get('running_containers', 0)
                healthy = health.get('healthy_containers', 0)
                
                lines.append(f"   Total: {total} | Running: {running} | Healthy: {healthy}")
                
                # Status indicators
                if running == total and healthy == total:
                    lines.append("   Status: ✅ ALL SYSTEMS HEALTHY")
                elif running == total:
                    lines.append("   Status: ⚠️  ALL RUNNING, SOME HEALTH ISSUES")
                else:
                    lines.append("   Status: 🚨 SOME CONTAINERS DOWN")
                
                lines.append("")
            
            # Container details
            containers = metrics.get('containers', [])
            if containers:
                lines.append("📋 CONTAINER DETAILS")
                
                for container in containers:
                    name = container.get('name', 'unknown')
                    status = container.get('status', 'unknown')
                    health = container.get('health_status', 'unknown')
                    memory_mb = container.get('memory_usage_mb', 0)
                    memory_percent = container.get('memory_percent', 0)
                    cpu_percent = container.get('cpu_percent', 0)
                    
                    # Status emoji
                    if status == 'running' and health == 'healthy':
                        status_emoji = "✅"
                    elif status == 'running':
                        status_emoji = "⚠️"
                    else:
                        status_emoji = "❌"
                    
                    lines.append(f"   {status_emoji} {name[:25]:<25}")
                    lines.append(f"      Status: {status} | Health: {health}")
                    lines.append(f"      Memory: {memory_mb:.1f}MB ({memory_percent:.1f}%) | CPU: {cpu_percent:.1f}%")
                    
                    # Memory bar for containers using significant memory
                    if memory_percent > 10:
                        memory_bar = self._create_progress_bar(memory_percent, 30)
                        lines.append(f"      Mem:    {memory_bar}")
                    
                    lines.append("")
            
            # Error handling
            if 'error' in metrics:
                lines.append("❌ ERROR")
                lines.append(f"   {metrics['error']}")
                lines.append("")
            
            # Footer
            lines.append("⚡ CONTROLS: [R]efresh | [Q]uit | [+/-] Update interval")
            lines.append("=" * 80)
            
            return "\n".join(lines)
            
        except Exception as e:
            return f"Error formatting dashboard: {e}"

    def _create_progress_bar(self, percentage: float, width: int = 40) -> str:
        """Create ASCII progress bar"""
        try:
            filled = int((percentage / 100) * width)
            bar = "█" * filled + "░" * (width - filled)
            
            # Color coding based on percentage
            if percentage > 90:
                return f"🔴{bar}"
            elif percentage > 75:
                return f"🟡{bar}"
            else:
                return f"🟢{bar}"
                
        except:
            return "░" * width

    def export_metrics_json(self, metrics: Dict[str, Any], filename: str = None) -> str:
        """Export metrics in JSON format"""
        try:
            if not filename:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                filename = f"metrics_export_{timestamp}.json"
            
            filepath = os.path.join(self.log_dir, filename)
            
            with open(filepath, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            return filepath
            
        except Exception as e:
            return f"Error exporting metrics: {e}"

    def create_html_report(self, metrics: Dict[str, Any]) -> str:
        """Create simple HTML dashboard for web viewing"""
        try:
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            html = f"""
<!DOCTYPE html>
<html>
<head>
    <title>Docker Monitoring Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
        .header {{ background: #2c3e50; color: white; padding: 20px; border-radius: 5px; }}
        .metrics {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 20px; margin: 20px 0; }}
        .card {{ background: white; padding: 20px; border-radius: 5px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .progress {{ background: #ecf0f1; height: 20px; border-radius: 10px; overflow: hidden; }}
        .progress-bar {{ height: 100%; transition: width 0.3s; }}
        .healthy {{ background: #27ae60; }}
        .warning {{ background: #f39c12; }}
        .critical {{ background: #e74c3c; }}
        .container-item {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-radius: 3px; }}
        .status-healthy {{ color: #27ae60; }}
        .status-warning {{ color: #f39c12; }}
        .status-error {{ color: #e74c3c; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🐳 Docker Monitoring Dashboard</h1>
        <p>Generated: {timestamp}</p>
    </div>
    
    <div class="metrics">
"""
            
            # System metrics
            system = metrics.get('system_metrics', {})
            if system:
                memory_percent = system.get('memory_percent', 0)
                cpu_percent = system.get('cpu_percent', 0)
                disk_percent = system.get('disk_percent', 0)
                
                memory_class = 'critical' if memory_percent > 85 else 'warning' if memory_percent > 70 else 'healthy'
                cpu_class = 'critical' if cpu_percent > 90 else 'warning' if cpu_percent > 70 else 'healthy'
                disk_class = 'critical' if disk_percent > 90 else 'warning' if disk_percent > 80 else 'healthy'
                
                html += f"""
        <div class="card">
            <h3>🖥️ System Metrics</h3>
            <div style="margin: 10px 0;">
                <strong>Memory Usage</strong>
                <div class="progress">
                    <div class="progress-bar {memory_class}" style="width: {memory_percent}%"></div>
                </div>
                <small>{system.get('memory_used_mb', 0):,}MB / {system.get('memory_total_mb', 0):,}MB ({memory_percent:.1f}%)</small>
            </div>
            <div style="margin: 10px 0;">
                <strong>CPU Usage</strong>
                <div class="progress">
                    <div class="progress-bar {cpu_class}" style="width: {cpu_percent}%"></div>
                </div>
                <small>{cpu_percent:.1f}%</small>
            </div>
            <div style="margin: 10px 0;">
                <strong>Disk Usage</strong>
                <div class="progress">
                    <div class="progress-bar {disk_class}" style="width: {disk_percent}%"></div>
                </div>
                <small>{system.get('disk_used_gb', 0):.1f}GB / {system.get('disk_total_gb', 0):.1f}GB ({disk_percent:.1f}%)</small>
            </div>
        </div>
"""
            
            # Container summary
            health = metrics.get('health_summary', {})
            if health:
                total = health.get('total_containers', 0)
                running = health.get('running_containers', 0)
                healthy = health.get('healthy_containers', 0)
                
                html += f"""
        <div class="card">
            <h3>📦 Container Summary</h3>
            <p><strong>Total Containers:</strong> {total}</p>
            <p><strong>Running:</strong> {running}</p>
            <p><strong>Healthy:</strong> {healthy}</p>
            {"<p class='status-healthy'>✅ All systems healthy</p>" if running == total and healthy == total else 
             "<p class='status-warning'>⚠️ Some issues detected</p>" if running == total else 
             "<p class='status-error'>🚨 Containers down</p>"}
        </div>
"""
            
            # Container details
            containers = metrics.get('containers', [])
            if containers:
                html += """
        <div class="card" style="grid-column: 1/-1;">
            <h3>📋 Container Details</h3>
"""
                
                for container in containers:
                    name = container.get('name', 'unknown')
                    status = container.get('status', 'unknown')
                    health = container.get('health_status', 'unknown')
                    memory_mb = container.get('memory_usage_mb', 0)
                    memory_percent = container.get('memory_percent', 0)
                    cpu_percent = container.get('cpu_percent', 0)
                    
                    status_class = 'status-healthy' if status == 'running' and health == 'healthy' else 'status-warning' if status == 'running' else 'status-error'
                    memory_class = 'critical' if memory_percent > 85 else 'warning' if memory_percent > 70 else 'healthy'
                    
                    html += f"""
            <div class="container-item">
                <h4 class="{status_class}">{name}</h4>
                <p><strong>Status:</strong> {status} | <strong>Health:</strong> {health}</p>
                <p><strong>Memory:</strong> {memory_mb:.1f}MB ({memory_percent:.1f}%) | <strong>CPU:</strong> {cpu_percent:.1f}%</p>
                <div class="progress" style="margin-top: 5px;">
                    <div class="progress-bar {memory_class}" style="width: {memory_percent}%"></div>
                </div>
            </div>
"""
                
                html += """
        </div>
"""
            
            html += """
    </div>
    
    <div class="card">
        <p><small>Dashboard auto-refreshes every 30 seconds. Last update: """ + timestamp + """</small></p>
    </div>
    
</body>
</html>"""
            
            # Save HTML file
            html_filename = os.path.join(self.log_dir, "dashboard.html")
            with open(html_filename, 'w') as f:
                f.write(html)
            
            return html_filename
            
        except Exception as e:
            return f"Error creating HTML report: {e}"

    async def run_dashboard_once(self):
        """Run dashboard once and display results"""
        try:
            print("Fetching metrics...")
            metrics = await self.get_live_metrics()
            
            print("\033[2J\033[H")  # Clear screen
            dashboard = self.format_live_dashboard(metrics)
            print(dashboard)
            
            # Also export data
            json_file = self.export_metrics_json(metrics)
            html_file = self.create_html_report(metrics)
            
            print(f"\n📁 Data exported:")
            print(f"   JSON: {json_file}")
            print(f"   HTML: {html_file}")
            
        except Exception as e:
            print(f"Error running dashboard: {e}")

    async def run_interactive_dashboard(self):
        """Run interactive dashboard with periodic updates"""
        try:
            print("Starting interactive dashboard...")
            print("Press Ctrl+C to exit")
            
            while True:
                try:
                    # Fetch metrics
                    metrics = await self.get_live_metrics()
                    
                    # Clear screen and display
                    print("\033[2J\033[H")  # Clear screen
                    dashboard = self.format_live_dashboard(metrics)
                    print(dashboard)
                    
                    # Update timestamp
                    self.last_update = datetime.now()
                    
                    # Wait for next update
                    await asyncio.sleep(self.update_interval)
                    
                except KeyboardInterrupt:
                    print("\nDashboard stopped by user")
                    break
                except Exception as e:
                    print(f"Error in dashboard loop: {e}")
                    await asyncio.sleep(5)  # Wait a bit before retrying
                    
        except Exception as e:
            print(f"Error starting dashboard: {e}")

# CLI interface
async def main():
    """Main CLI interface"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Monitoring Dashboard')
    parser.add_argument('--interactive', action='store_true',
                       help='Run interactive dashboard with auto-refresh')
    parser.add_argument('--once', action='store_true',
                       help='Run dashboard once and exit')
    parser.add_argument('--interval', type=int, default=30,
                       help='Update interval in seconds (default: 30)')
    parser.add_argument('--html', action='store_true',
                       help='Generate HTML report only')
    parser.add_argument('--json', action='store_true',
                       help='Generate JSON export only')
    
    args = parser.parse_args()
    
    dashboard = MonitoringDashboard()
    dashboard.update_interval = args.interval
    
    if args.interactive:
        await dashboard.run_interactive_dashboard()
    elif args.once:
        await dashboard.run_dashboard_once()
    elif args.html:
        metrics = await dashboard.get_live_metrics()
        html_file = dashboard.create_html_report(metrics)
        print(f"HTML report generated: {html_file}")
    elif args.json:
        metrics = await dashboard.get_live_metrics()
        json_file = dashboard.export_metrics_json(metrics)
        print(f"JSON export generated: {json_file}")
    else:
        # Default: run once
        await dashboard.run_dashboard_once()

if __name__ == "__main__":
    asyncio.run(main())