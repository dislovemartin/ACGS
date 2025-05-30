#!/usr/bin/env python3
"""
Monitoring and Alerting Setup for ACGS-PGP
Sets up comprehensive monitoring, metrics collection, and alerting
"""

import os
import json
import yaml
from datetime import datetime
from typing import Dict, List, Any

class MonitoringSetup:
    def __init__(self):
        self.services = [
            {"name": "ac_service", "port": 8001, "path": "/health"},
            {"name": "integrity_service", "port": 8002, "path": "/health"},
            {"name": "fv_service", "port": 8003, "path": "/health"},
            {"name": "gs_service", "port": 8004, "path": "/health"},
            {"name": "pgc_service", "port": 8005, "path": "/health"},
            {"name": "postgres_db", "port": 5433, "path": None}
        ]
    
    def create_prometheus_config(self):
        """Create Prometheus monitoring configuration"""
        print("📊 Creating Prometheus Configuration...")
        
        prometheus_config = {
            "global": {
                "scrape_interval": "15s",
                "evaluation_interval": "15s"
            },
            "rule_files": [
                "acgs_pgp_rules.yml"
            ],
            "alerting": {
                "alertmanagers": [
                    {
                        "static_configs": [
                            {"targets": ["alertmanager:9093"]}
                        ]
                    }
                ]
            },
            "scrape_configs": [
                {
                    "job_name": "acgs-pgp-services",
                    "static_configs": [
                        {
                            "targets": [
                                "ac_service:8001",
                                "integrity_service:8002", 
                                "fv_service:8003",
                                "gs_service:8004",
                                "pgc_service:8005"
                            ]
                        }
                    ],
                    "metrics_path": "/metrics",
                    "scrape_interval": "10s"
                },
                {
                    "job_name": "postgres",
                    "static_configs": [
                        {"targets": ["postgres_exporter:9187"]}
                    ]
                },
                {
                    "job_name": "node-exporter",
                    "static_configs": [
                        {"targets": ["node_exporter:9100"]}
                    ]
                }
            ]
        }
        
        with open("prometheus.yml", "w") as f:
            yaml.dump(prometheus_config, f, default_flow_style=False)
        
        print("  ✅ Prometheus config created: prometheus.yml")
    
    def create_alerting_rules(self):
        """Create Prometheus alerting rules"""
        print("\n🚨 Creating Alerting Rules...")
        
        alerting_rules = {
            "groups": [
                {
                    "name": "acgs_pgp_alerts",
                    "rules": [
                        {
                            "alert": "ServiceDown",
                            "expr": "up == 0",
                            "for": "1m",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "ACGS-PGP service {{ $labels.instance }} is down",
                                "description": "Service {{ $labels.instance }} has been down for more than 1 minute"
                            }
                        },
                        {
                            "alert": "HighResponseTime",
                            "expr": "http_request_duration_seconds{quantile=\"0.95\"} > 1",
                            "for": "5m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High response time on {{ $labels.instance }}",
                                "description": "95th percentile response time is {{ $value }}s"
                            }
                        },
                        {
                            "alert": "DatabaseConnectionsHigh",
                            "expr": "pg_stat_activity_count > 80",
                            "for": "2m",
                            "labels": {"severity": "warning"},
                            "annotations": {
                                "summary": "High database connections",
                                "description": "Database has {{ $value }} active connections"
                            }
                        },
                        {
                            "alert": "ConstitutionalViolation",
                            "expr": "acgs_constitutional_violations_total > 0",
                            "for": "0s",
                            "labels": {"severity": "critical"},
                            "annotations": {
                                "summary": "Constitutional violation detected",
                                "description": "{{ $value }} constitutional violations detected in the last 5 minutes"
                            }
                        }
                    ]
                }
            ]
        }
        
        with open("acgs_pgp_rules.yml", "w") as f:
            yaml.dump(alerting_rules, f, default_flow_style=False)
        
        print("  ✅ Alerting rules created: acgs_pgp_rules.yml")
    
    def create_grafana_dashboard(self):
        """Create Grafana dashboard configuration"""
        print("\n📈 Creating Grafana Dashboard...")
        
        dashboard = {
            "dashboard": {
                "id": None,
                "title": "ACGS-PGP System Overview",
                "tags": ["acgs-pgp"],
                "timezone": "browser",
                "panels": [
                    {
                        "id": 1,
                        "title": "Service Health",
                        "type": "stat",
                        "targets": [
                            {
                                "expr": "up",
                                "legendFormat": "{{ instance }}"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 0, "y": 0}
                    },
                    {
                        "id": 2,
                        "title": "Response Times",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "http_request_duration_seconds{quantile=\"0.95\"}",
                                "legendFormat": "95th percentile"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 12, "x": 12, "y": 0}
                    },
                    {
                        "id": 3,
                        "title": "Constitutional Compliance",
                        "type": "graph",
                        "targets": [
                            {
                                "expr": "acgs_constitutional_compliance_rate",
                                "legendFormat": "Compliance Rate"
                            }
                        ],
                        "gridPos": {"h": 8, "w": 24, "x": 0, "y": 8}
                    }
                ],
                "time": {"from": "now-1h", "to": "now"},
                "refresh": "5s"
            }
        }
        
        with open("acgs_pgp_dashboard.json", "w") as f:
            json.dump(dashboard, f, indent=2)
        
        print("  ✅ Grafana dashboard created: acgs_pgp_dashboard.json")
    
    def create_health_check_script(self):
        """Create comprehensive health check script"""
        print("\n🏥 Creating Health Check Script...")
        
        health_script = '''#!/bin/bash
# ACGS-PGP Comprehensive Health Check Script

echo "🏥 ACGS-PGP System Health Check"
echo "==============================="

# Service health checks
services=("ac_service:8001" "integrity_service:8002" "fv_service:8003" "gs_service:8004" "pgc_service:8005")
healthy_services=0
total_services=${#services[@]}

echo "1. Service Health Status:"
for service in "${services[@]}"; do
    IFS=':' read -r name port <<< "$service"
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:$port/health)
    
    if [ "$response" = "200" ]; then
        echo "  ✅ $name: Healthy"
        ((healthy_services++))
    else
        echo "  ❌ $name: Unhealthy (HTTP $response)"
    fi
done

echo -e "\\n2. Database Health:"
if pg_isready -h localhost -p 5433 -U acgs_user -d acgs_pgp_db; then
    echo "  ✅ PostgreSQL: Healthy"
    ((healthy_services++))
    ((total_services++))
else
    echo "  ❌ PostgreSQL: Unhealthy"
    ((total_services++))
fi

echo -e "\\n3. System Resources:"
echo "  CPU Usage: $(top -bn1 | grep "Cpu(s)" | awk '{print $2}' | cut -d'%' -f1)%"
echo "  Memory Usage: $(free | grep Mem | awk '{printf("%.1f%%", $3/$2 * 100.0)}')"
echo "  Disk Usage: $(df -h / | awk 'NR==2{printf "%s", $5}')"

echo -e "\\n4. Docker Container Status:"
docker-compose ps --format "table {{.Name}}\\t{{.State}}\\t{{.Status}}"

echo -e "\\n5. Recent Logs (last 10 lines):"
docker-compose logs --tail=10 ac_service | head -5
docker-compose logs --tail=10 gs_service | head -5

echo -e "\\n📊 Health Summary:"
echo "  Services: $healthy_services/$total_services healthy"
health_percentage=$((healthy_services * 100 / total_services))

if [ $health_percentage -eq 100 ]; then
    echo "  Status: ✅ All systems operational"
    exit 0
elif [ $health_percentage -ge 80 ]; then
    echo "  Status: ⚠️  Mostly operational ($health_percentage%)"
    exit 1
else
    echo "  Status: ❌ System degraded ($health_percentage%)"
    exit 2
fi
'''
        
        with open("health_check.sh", "w") as f:
            f.write(health_script)
        
        os.chmod("health_check.sh", 0o755)
        print("  ✅ Health check script created: health_check.sh")
    
    def create_monitoring_docker_compose(self):
        """Create Docker Compose for monitoring stack"""
        print("\n🐳 Creating Monitoring Docker Compose...")
        
        monitoring_compose = {
            "version": "3.8",
            "services": {
                "prometheus": {
                    "image": "prom/prometheus:latest",
                    "container_name": "acgs_prometheus",
                    "ports": ["9090:9090"],
                    "volumes": [
                        "./prometheus.yml:/etc/prometheus/prometheus.yml",
                        "./acgs_pgp_rules.yml:/etc/prometheus/acgs_pgp_rules.yml"
                    ],
                    "command": [
                        "--config.file=/etc/prometheus/prometheus.yml",
                        "--storage.tsdb.path=/prometheus",
                        "--web.console.libraries=/etc/prometheus/console_libraries",
                        "--web.console.templates=/etc/prometheus/consoles",
                        "--storage.tsdb.retention.time=200h",
                        "--web.enable-lifecycle"
                    ]
                },
                "grafana": {
                    "image": "grafana/grafana:latest",
                    "container_name": "acgs_grafana",
                    "ports": ["3001:3000"],
                    "environment": [
                        "GF_SECURITY_ADMIN_PASSWORD=admin123"
                    ],
                    "volumes": [
                        "grafana_data:/var/lib/grafana"
                    ]
                },
                "alertmanager": {
                    "image": "prom/alertmanager:latest",
                    "container_name": "acgs_alertmanager",
                    "ports": ["9093:9093"],
                    "volumes": [
                        "./alertmanager.yml:/etc/alertmanager/alertmanager.yml"
                    ]
                },
                "node_exporter": {
                    "image": "prom/node-exporter:latest",
                    "container_name": "acgs_node_exporter",
                    "ports": ["9100:9100"]
                }
            },
            "volumes": {
                "grafana_data": {}
            }
        }
        
        with open("docker-compose.monitoring.yml", "w") as f:
            yaml.dump(monitoring_compose, f, default_flow_style=False)
        
        print("  ✅ Monitoring Docker Compose created: docker-compose.monitoring.yml")
    
    def create_alertmanager_config(self):
        """Create Alertmanager configuration"""
        print("\n📧 Creating Alertmanager Configuration...")
        
        alertmanager_config = {
            "global": {
                "smtp_smarthost": "localhost:587",
                "smtp_from": "alerts@acgs-pgp.com"
            },
            "route": {
                "group_by": ["alertname"],
                "group_wait": "10s",
                "group_interval": "10s",
                "repeat_interval": "1h",
                "receiver": "web.hook"
            },
            "receivers": [
                {
                    "name": "web.hook",
                    "email_configs": [
                        {
                            "to": "admin@acgs-pgp.com",
                            "subject": "ACGS-PGP Alert: {{ .GroupLabels.alertname }}",
                            "body": "{{ range .Alerts }}{{ .Annotations.description }}{{ end }}"
                        }
                    ]
                }
            ]
        }
        
        with open("alertmanager.yml", "w") as f:
            yaml.dump(alertmanager_config, f, default_flow_style=False)
        
        print("  ✅ Alertmanager config created: alertmanager.yml")
    
    def setup_monitoring_and_alerting(self):
        """Main setup function"""
        print("🚀 Setting up Monitoring and Alerting for ACGS-PGP")
        print("=" * 60)
        
        self.create_prometheus_config()
        self.create_alerting_rules()
        self.create_grafana_dashboard()
        self.create_health_check_script()
        self.create_monitoring_docker_compose()
        self.create_alertmanager_config()
        
        # Create startup script
        startup_script = '''#!/bin/bash
# Start ACGS-PGP monitoring stack

echo "🚀 Starting ACGS-PGP Monitoring Stack..."

# Start monitoring services
docker-compose -f docker-compose.monitoring.yml up -d

echo "✅ Monitoring stack started!"
echo "📊 Prometheus: http://localhost:9090"
echo "📈 Grafana: http://localhost:3001 (admin/admin123)"
echo "🚨 Alertmanager: http://localhost:9093"

# Wait for services to start
sleep 10

# Run initial health check
./health_check.sh
'''
        
        with open("start_monitoring.sh", "w") as f:
            f.write(startup_script)
        
        os.chmod("start_monitoring.sh", 0o755)
        
        print("\n" + "=" * 60)
        print("✅ Monitoring and Alerting Setup Complete!")
        print("\nCreated files:")
        print("- prometheus.yml (Prometheus configuration)")
        print("- acgs_pgp_rules.yml (alerting rules)")
        print("- acgs_pgp_dashboard.json (Grafana dashboard)")
        print("- health_check.sh (health monitoring)")
        print("- docker-compose.monitoring.yml (monitoring stack)")
        print("- alertmanager.yml (alert configuration)")
        print("- start_monitoring.sh (startup script)")
        print("\nNext steps:")
        print("1. Start monitoring: ./start_monitoring.sh")
        print("2. Access Grafana: http://localhost:3001")
        print("3. Import dashboard: acgs_pgp_dashboard.json")
        print("4. Configure email alerts in alertmanager.yml")

def main():
    setup = MonitoringSetup()
    setup.setup_monitoring_and_alerting()

if __name__ == "__main__":
    main()
