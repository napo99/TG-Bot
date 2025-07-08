#!/usr/bin/env python3
"""
🔍 CI/CD Evolution Detector
Automatically assess project maturity and recommend next evolution level
"""

import yaml
import os
import subprocess
import json
from datetime import datetime, timedelta
from pathlib import Path

class EvolutionDetector:
    def __init__(self, config_path="config/evolution.yml"):
        self.config_path = config_path
        self.config = self.load_config()
        self.project_root = Path(__file__).parent.parent
        
    def load_config(self):
        """Load evolution configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            print("❌ Evolution config not found. Run ./scripts/setup/init-level-1.sh first")
            return {}
    
    def collect_current_metrics(self):
        """Collect current project metrics"""
        metrics = {
            'deployment_frequency': self._detect_deployment_frequency(),
            'team_size': self._detect_team_size(),
            'production_traffic': self._detect_production_traffic(),
            'manual_errors': self._detect_manual_errors(),
            'test_coverage': self._detect_test_coverage(),
            'service_count': self._count_services(),
            'last_updated': datetime.now().strftime('%Y-%m-%d')
        }
        
        return metrics
    
    def _detect_deployment_frequency(self):
        """Detect how often deployments happen"""
        try:
            # Check git commits in last 30 days
            result = subprocess.run([
                'git', 'log', '--since="30 days ago"', '--oneline'
            ], capture_output=True, text=True)
            
            commit_count = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 0
            
            if commit_count > 20:
                return "daily"
            elif commit_count > 8:
                return "weekly"
            else:
                return "monthly"
                
        except Exception:
            return "unknown"
    
    def _detect_team_size(self):
        """Estimate team size from git contributors"""
        try:
            result = subprocess.run([
                'git', 'shortlog', '-sn', '--since="3 months ago"'
            ], capture_output=True, text=True)
            
            contributors = len(result.stdout.strip().split('\n')) if result.stdout.strip() else 1
            return max(1, contributors)  # At least 1 person
            
        except Exception:
            return 1
    
    def _detect_production_traffic(self):
        """Estimate production traffic (placeholder)"""
        # TODO: Integrate with actual monitoring systems
        # For now, check if production monitoring is set up
        
        monitoring_files = [
            'docker-compose.prod.yml',
            'config/production.env',
            'monitoring/prometheus.yml'
        ]
        
        has_production = any(
            os.path.exists(f) for f in monitoring_files
        )
        
        return 1000 if has_production else 0
    
    def _detect_manual_errors(self):
        """Detect manual deployment errors (placeholder)"""
        # TODO: Parse deployment logs or error reports
        # For now, estimate based on deployment complexity
        
        has_manual_deployment = not os.path.exists('.github/workflows/deploy.yml')
        return 2 if has_manual_deployment else 0
    
    def _detect_test_coverage(self):
        """Detect test coverage percentage"""
        try:
            if os.path.exists('tests/'):
                test_files = list(Path('tests').rglob('test_*.py'))
                source_files = list(Path('services').rglob('*.py'))
                
                if test_files and source_files:
                    coverage = (len(test_files) / len(source_files)) * 100
                    return min(100, coverage)  # Cap at 100%
                    
        except Exception:
            pass
            
        return 0
    
    def _count_services(self):
        """Count number of services"""
        services_dir = Path('services')
        if services_dir.exists():
            return len([d for d in services_dir.iterdir() if d.is_dir()])
        return 1
    
    def evaluate_level_readiness(self):
        """Evaluate readiness for next level"""
        current_level = self.config.get('current_level', 1)
        metrics = self.collect_current_metrics()
        
        recommendations = []
        
        # Level 2 readiness
        if current_level == 1:
            level_2_ready = self._check_level_2_readiness(metrics)
            if level_2_ready['ready']:
                recommendations.append({
                    'level': 2,
                    'title': 'Automated CI/CD',
                    'priority': 'HIGH',
                    'effort': '2-3 days',
                    'triggers': level_2_ready['triggers'],
                    'benefits': [
                        'Automated staging deployment',
                        'Reduced manual errors',
                        'Faster iteration cycles'
                    ]
                })
        
        # Level 3 readiness
        if current_level <= 2:
            level_3_ready = self._check_level_3_readiness(metrics)
            if level_3_ready['ready']:
                recommendations.append({
                    'level': 3,
                    'title': 'Professional Monitoring',
                    'priority': 'MEDIUM',
                    'effort': '1-2 weeks',
                    'triggers': level_3_ready['triggers'],
                    'benefits': [
                        'Production monitoring dashboards',
                        'Automated alerting',
                        'Performance tracking'
                    ]
                })
        
        return recommendations, metrics
    
    def _check_level_2_readiness(self, metrics):
        """Check if ready for Level 2"""
        triggers = []
        
        if metrics['deployment_frequency'] in ['daily', 'weekly']:
            triggers.append(f"High deployment frequency: {metrics['deployment_frequency']}")
        
        if metrics['team_size'] > 1:
            triggers.append(f"Team growth: {metrics['team_size']} contributors")
        
        if metrics['manual_errors'] > 0:
            triggers.append(f"Manual errors detected: {metrics['manual_errors']}/month")
        
        if metrics['service_count'] > 1:
            triggers.append(f"Multiple services: {metrics['service_count']} services")
        
        return {
            'ready': len(triggers) >= 1,  # Any trigger is enough
            'triggers': triggers
        }
    
    def _check_level_3_readiness(self, metrics):
        """Check if ready for Level 3"""
        triggers = []
        
        if metrics['production_traffic'] > 500:
            triggers.append(f"Production traffic: {metrics['production_traffic']} req/day")
        
        if metrics['deployment_frequency'] == 'daily':
            triggers.append("Daily deployment frequency")
        
        if metrics['team_size'] > 2:
            triggers.append(f"Large team: {metrics['team_size']} contributors")
        
        return {
            'ready': len(triggers) >= 2,  # Need multiple triggers
            'triggers': triggers
        }
    
    def generate_report(self):
        """Generate comprehensive evolution report"""
        recommendations, metrics = self.evaluate_level_readiness()
        current_level = self.config.get('current_level', 1)
        
        print("🔍 CI/CD Evolution Assessment")
        print("=" * 50)
        print()
        
        # Current status
        print(f"📊 Current Level: {current_level}")
        print(f"🎯 Target Level: {self.config.get('target_level', 2)}")
        print()
        
        # Metrics
        print("📈 Project Metrics:")
        print(f"  • Deployment Frequency: {metrics['deployment_frequency']}")
        print(f"  • Team Size: {metrics['team_size']} contributors")
        print(f"  • Production Traffic: {metrics['production_traffic']} requests/day")
        print(f"  • Test Coverage: {metrics['test_coverage']:.1f}%")
        print(f"  • Service Count: {metrics['service_count']}")
        print(f"  • Manual Errors: {metrics['manual_errors']}/month")
        print()
        
        # Recommendations
        if recommendations:
            print("🚀 Evolution Recommendations:")
            for rec in recommendations:
                print(f"  📋 Level {rec['level']}: {rec['title']}")
                print(f"     Priority: {rec['priority']} | Effort: {rec['effort']}")
                print(f"     Triggers: {', '.join(rec['triggers'])}")
                print(f"     Benefits: {', '.join(rec['benefits'])}")
                print()
                
            # Show upgrade command
            next_level = recommendations[0]['level']
            print(f"💡 Ready to upgrade to Level {next_level}!")
            print(f"   Run: ./scripts/setup/upgrade-to-level-{next_level}.sh")
            print()
        else:
            print("✅ Current level is appropriate for project maturity")
            print()
            
            # Show what would trigger next level
            if current_level == 1:
                print("🎯 To trigger Level 2 automation:")
                print("  • Increase deployment frequency (deploy more often)")
                print("  • Add team members (collaborative development)")
                print("  • Deploy to production (operational requirements)")
        
        # Level-specific advice
        if current_level == 1:
            print("📋 Level 1 Checklist:")
            print("  □ Add health endpoints to all services")
            print("  □ Create unit tests for critical functions")
            print("  □ Set up basic GitHub Actions")
            print("  □ Document API endpoints")
        
        return recommendations
    
    def update_config(self, metrics):
        """Update evolution config with current metrics"""
        if 'metrics' not in self.config:
            self.config['metrics'] = {}
            
        self.config['metrics'].update(metrics)
        
        try:
            with open(self.config_path, 'w') as f:
                yaml.dump(self.config, f, default_flow_style=False)
            print(f"✅ Updated metrics in {self.config_path}")
        except Exception as e:
            print(f"❌ Failed to update config: {e}")

def main():
    """Main entry point"""
    detector = EvolutionDetector()
    
    if not detector.config:
        return
    
    # Generate and display report
    recommendations = detector.generate_report()
    
    # Update metrics
    _, metrics = detector.evaluate_level_readiness()
    detector.update_config(metrics)
    
    # Exit with appropriate code
    if recommendations:
        exit(1)  # Upgrades available
    else:
        exit(0)  # Current level appropriate

if __name__ == "__main__":
    main()