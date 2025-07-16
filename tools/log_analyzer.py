"""
Log Analysis Tool for Crypto Assistant
Provides comprehensive log analysis and reporting capabilities
"""

import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
import re
from collections import defaultdict, Counter
import matplotlib.pyplot as plt
import seaborn as sns

class LogAnalyzer:
    """Comprehensive log analysis tool"""
    
    def __init__(self, log_directory: str = "/app/logs"):
        self.log_directory = Path(log_directory)
        self.df_cache = {}
        
    def load_logs(self, service: str = None, date_range: Tuple[str, str] = None) -> pd.DataFrame:
        """Load logs into pandas DataFrame"""
        cache_key = f"{service}_{date_range}"
        if cache_key in self.df_cache:
            return self.df_cache[cache_key]
        
        log_files = []
        if service:
            log_files.extend(self.log_directory.glob(f"{service}*.log"))
        else:
            log_files.extend(self.log_directory.glob("*.log"))
        
        all_logs = []
        for log_file in log_files:
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            log_entry = json.loads(line.strip())
                            all_logs.append(log_entry)
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                print(f"Error reading {log_file}: {e}")
                continue
        
        if not all_logs:
            return pd.DataFrame()
        
        df = pd.DataFrame(all_logs)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter by date range if specified
        if date_range:
            start_date, end_date = date_range
            df = df[(df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)]
        
        self.df_cache[cache_key] = df
        return df
    
    def analyze_error_patterns(self, service: str = None, hours: int = 24) -> Dict[str, Any]:
        """Analyze error patterns and trends"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(service, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        # Filter error logs
        error_df = df[df['level'].isin(['ERROR', 'CRITICAL', 'FATAL'])]
        
        if error_df.empty:
            return {
                "total_errors": 0,
                "error_rate": 0,
                "message": "No errors found in the specified time period"
            }
        
        analysis = {
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "total_logs": len(df),
            "total_errors": len(error_df),
            "error_rate": len(error_df) / len(df) * 100,
            "errors_by_service": error_df['service'].value_counts().to_dict(),
            "errors_by_module": error_df['module'].value_counts().to_dict(),
            "errors_by_level": error_df['level'].value_counts().to_dict(),
            "top_error_messages": self._extract_top_errors(error_df),
            "error_timeline": self._create_error_timeline(error_df),
            "error_frequency": self._analyze_error_frequency(error_df),
            "critical_errors": self._identify_critical_errors(error_df)
        }
        
        return analysis
    
    def analyze_performance_metrics(self, service: str = None, hours: int = 24) -> Dict[str, Any]:
        """Analyze performance metrics and trends"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(service, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        # Extract performance data
        perf_logs = df[df['event_type'] == 'performance_metric']
        api_logs = df[df['event_type'].isin(['api_request', 'api_response'])]
        
        analysis = {
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "response_time_analysis": self._analyze_response_times(df),
            "memory_usage_analysis": self._analyze_memory_usage(perf_logs),
            "api_performance": self._analyze_api_performance(api_logs),
            "throughput_analysis": self._analyze_throughput(df),
            "resource_utilization": self._analyze_resource_utilization(perf_logs),
            "performance_alerts": self._identify_performance_alerts(df)
        }
        
        return analysis
    
    def track_user_journey(self, user_id: str, hours: int = 24) -> Dict[str, Any]:
        """Track complete user interaction journey"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(None, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        # Filter user-related logs
        user_logs = df[
            (df['user_data'].notna() & (df['user_data'].astype(str).str.contains(str(user_id)))) |
            (df['context'].notna() & (df['context'].astype(str).str.contains(str(user_id))))
        ]
        
        if user_logs.empty:
            return {"message": f"No activity found for user {user_id}"}
        
        journey = {
            "user_id": user_id,
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "total_interactions": len(user_logs),
            "commands_used": self._extract_user_commands(user_logs),
            "session_timeline": self._create_user_timeline(user_logs),
            "response_times": self._analyze_user_response_times(user_logs),
            "errors_encountered": self._extract_user_errors(user_logs),
            "most_used_features": self._analyze_user_feature_usage(user_logs),
            "session_duration": self._calculate_session_duration(user_logs)
        }
        
        return journey
    
    def generate_system_health_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive system health report"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(None, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        health_report = {
            "report_timestamp": datetime.now().isoformat(),
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "overall_health_score": self._calculate_health_score(df),
            "service_status": self._analyze_service_status(df),
            "error_summary": self.analyze_error_patterns(None, hours),
            "performance_summary": self.analyze_performance_metrics(None, hours),
            "exchange_health": self._analyze_exchange_health(df),
            "system_alerts": self._generate_system_alerts(df),
            "recommendations": self._generate_recommendations(df)
        }
        
        return health_report
    
    def analyze_exchange_performance(self, hours: int = 24) -> Dict[str, Any]:
        """Analyze exchange API performance"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(None, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        # Filter exchange-related logs
        exchange_logs = df[df['event_type'] == 'exchange_api_call']
        
        analysis = {
            "time_range": f"{start_time.isoformat()} to {end_time.isoformat()}",
            "exchange_summary": self._summarize_exchange_performance(exchange_logs),
            "response_time_comparison": self._compare_exchange_response_times(exchange_logs),
            "success_rate_comparison": self._compare_exchange_success_rates(exchange_logs),
            "rate_limit_analysis": self._analyze_rate_limits(exchange_logs),
            "data_quality_scores": self._analyze_exchange_data_quality(exchange_logs),
            "reliability_ranking": self._rank_exchange_reliability(exchange_logs)
        }
        
        return analysis
    
    def create_performance_dashboard_data(self, hours: int = 24) -> Dict[str, Any]:
        """Create data for performance dashboard"""
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours)
        
        df = self.load_logs(None, (start_time.isoformat(), end_time.isoformat()))
        
        if df.empty:
            return {"error": "No logs found"}
        
        dashboard_data = {
            "timestamp": datetime.now().isoformat(),
            "time_series_data": {
                "error_rate": self._create_error_rate_timeseries(df),
                "response_times": self._create_response_time_timeseries(df),
                "memory_usage": self._create_memory_usage_timeseries(df),
                "api_throughput": self._create_throughput_timeseries(df)
            },
            "current_metrics": {
                "total_requests": len(df[df['event_type'] == 'api_request']),
                "error_count": len(df[df['level'] == 'ERROR']),
                "avg_response_time": self._calculate_avg_response_time(df),
                "active_users": self._count_active_users(df),
                "system_uptime": self._calculate_uptime(df)
            },
            "alerts": self._get_current_alerts(df),
            "top_endpoints": self._get_top_endpoints(df),
            "service_health": self._get_service_health_indicators(df)
        }
        
        return dashboard_data
    
    def _extract_top_errors(self, error_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Extract top error messages"""
        if error_df.empty:
            return []
        
        # Extract error messages from different possible locations
        error_messages = []
        for _, row in error_df.iterrows():
            message = row.get('message', '')
            if 'exception' in row and isinstance(row['exception'], dict):
                message = row['exception'].get('message', message)
            error_messages.append(message)
        
        error_counter = Counter(error_messages)
        return [{"message": msg, "count": count} for msg, count in error_counter.most_common(10)]
    
    def _create_error_timeline(self, error_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Create error timeline"""
        if error_df.empty:
            return []
        
        # Group by hour
        error_df['hour'] = error_df['timestamp'].dt.floor('H')
        timeline = error_df.groupby('hour').size().reset_index(name='error_count')
        
        return [{"timestamp": row['hour'].isoformat(), "count": row['error_count']} 
                for _, row in timeline.iterrows()]
    
    def _analyze_error_frequency(self, error_df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze error frequency patterns"""
        if error_df.empty:
            return {}
        
        error_df['hour'] = error_df['timestamp'].dt.hour
        error_df['day_of_week'] = error_df['timestamp'].dt.day_name()
        
        return {
            "errors_by_hour": error_df['hour'].value_counts().to_dict(),
            "errors_by_day": error_df['day_of_week'].value_counts().to_dict(),
            "peak_error_hour": error_df['hour'].mode().iloc[0] if not error_df['hour'].mode().empty else None,
            "peak_error_day": error_df['day_of_week'].mode().iloc[0] if not error_df['day_of_week'].mode().empty else None
        }
    
    def _identify_critical_errors(self, error_df: pd.DataFrame) -> List[Dict[str, Any]]:
        """Identify critical errors requiring immediate attention"""
        if error_df.empty:
            return []
        
        critical_errors = []
        
        # Find recent critical/fatal errors
        recent_critical = error_df[
            (error_df['level'].isin(['CRITICAL', 'FATAL'])) &
            (error_df['timestamp'] > datetime.now() - timedelta(hours=1))
        ]
        
        for _, row in recent_critical.iterrows():
            critical_errors.append({
                "timestamp": row['timestamp'].isoformat(),
                "service": row.get('service', 'unknown'),
                "module": row.get('module', 'unknown'),
                "message": row.get('message', ''),
                "level": row.get('level', ''),
                "severity": "critical"
            })
        
        # Find high-frequency errors
        error_counts = error_df['message'].value_counts()
        high_freq_errors = error_counts[error_counts > 10]
        
        for message, count in high_freq_errors.items():
            if len(critical_errors) < 20:  # Limit to prevent overflow
                critical_errors.append({
                    "message": message,
                    "count": count,
                    "severity": "high_frequency",
                    "recommendation": "Investigate recurring issue"
                })
        
        return critical_errors
    
    def _analyze_response_times(self, df: pd.DataFrame) -> Dict[str, Any]:
        """Analyze response time metrics"""
        # Extract response times from various sources
        response_times = []
        
        # From API response logs
        api_responses = df[df['event_type'] == 'api_response']
        if not api_responses.empty and 'api' in api_responses.columns:
            for _, row in api_responses.iterrows():
                if isinstance(row['api'], dict) and 'response_time_ms' in row['api']:
                    response_times.append(row['api']['response_time_ms'])
        
        # From user interaction logs
        user_interactions = df[df['event_type'] == 'telegram_interaction']
        if not user_interactions.empty and 'user' in user_interactions.columns:
            for _, row in user_interactions.iterrows():
                if isinstance(row['user'], dict) and 'response_time_ms' in row['user']:
                    response_times.append(row['user']['response_time_ms'])
        
        if not response_times:
            return {"message": "No response time data found"}
        
        response_times = np.array(response_times)
        
        return {
            "count": len(response_times),
            "mean": float(np.mean(response_times)),
            "median": float(np.median(response_times)),
            "p95": float(np.percentile(response_times, 95)),
            "p99": float(np.percentile(response_times, 99)),
            "min": float(np.min(response_times)),
            "max": float(np.max(response_times)),
            "std": float(np.std(response_times))
        }
    
    def _calculate_health_score(self, df: pd.DataFrame) -> float:
        """Calculate overall system health score (0-100)"""
        if df.empty:
            return 0
        
        # Error rate component (40% weight)
        error_logs = df[df['level'].isin(['ERROR', 'CRITICAL', 'FATAL'])]
        error_rate = len(error_logs) / len(df) if len(df) > 0 else 0
        error_score = max(0, 100 - (error_rate * 1000))  # Penalize errors heavily
        
        # Response time component (30% weight)
        response_time_analysis = self._analyze_response_times(df)
        if 'mean' in response_time_analysis:
            avg_response_time = response_time_analysis['mean']
            # Good response time is < 1000ms
            response_score = max(0, 100 - (avg_response_time / 50))  # Scale appropriately
        else:
            response_score = 100
        
        # Availability component (30% weight)
        # Assume high availability if logs are being generated consistently
        time_span = (df['timestamp'].max() - df['timestamp'].min()).total_seconds()
        expected_logs = max(1, time_span / 60)  # Expect at least 1 log per minute
        availability_score = min(100, (len(df) / expected_logs) * 100)
        
        # Weighted average
        health_score = (error_score * 0.4 + response_score * 0.3 + availability_score * 0.3)
        
        return round(min(100, max(0, health_score)), 2)
    
    def export_analysis_report(self, analysis_type: str = "full", output_format: str = "json") -> str:
        """Export analysis report to file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if analysis_type == "full":
            report = self.generate_system_health_report()
        elif analysis_type == "errors":
            report = self.analyze_error_patterns()
        elif analysis_type == "performance":
            report = self.analyze_performance_metrics()
        elif analysis_type == "exchanges":
            report = self.analyze_exchange_performance()
        else:
            report = {"error": f"Unknown analysis type: {analysis_type}"}
        
        filename = f"log_analysis_{analysis_type}_{timestamp}"
        
        if output_format == "json":
            filepath = self.log_directory / f"{filename}.json"
            with open(filepath, 'w') as f:
                json.dump(report, f, indent=2, default=str)
        elif output_format == "csv":
            # Convert to DataFrame if possible
            filepath = self.log_directory / f"{filename}.csv"
            try:
                df = pd.json_normalize(report)
                df.to_csv(filepath, index=False)
            except Exception as e:
                return f"Error exporting to CSV: {e}"
        
        return str(filepath)

if __name__ == "__main__":
    # Example usage
    analyzer = LogAnalyzer()
    
    # Generate system health report
    health_report = analyzer.generate_system_health_report(hours=24)
    print(json.dumps(health_report, indent=2, default=str))
    
    # Analyze error patterns
    error_analysis = analyzer.analyze_error_patterns(hours=24)
    print(json.dumps(error_analysis, indent=2, default=str))