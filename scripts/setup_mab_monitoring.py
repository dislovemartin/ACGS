#!/usr/bin/env python3
"""
Setup MAB Performance Monitoring

Sets up comprehensive monitoring for the Multi-Armed Bandit system including:
1. Prometheus metrics integration
2. Grafana dashboard configuration
3. Alert rules for performance degradation
4. Automated reporting setup

Usage:
    python scripts/setup_mab_monitoring.py
"""

import asyncio
import sys
import os
import json
import yaml
from datetime import datetime, timezone
from pathlib import Path

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src', 'backend'))

# Set environment variables
os.environ['DATABASE_URL'] = 'postgresql+asyncpg://acgs_user:acgs_password@localhost:5434/acgs_pgp_db'
os.environ['PYTHONPATH'] = '/home/dislove/ACGS-master/src/backend:/home/dislove/ACGS-master/src/backend/shared'


def create_prometheus_config():
    """Create Prometheus configuration for MAB monitoring."""
    print("📊 Creating Prometheus configuration...")
    
    prometheus_config = {
        'global': {
            'scrape_interval': '15s',
            'evaluation_interval': '15s'
        },
        'rule_files': [
            'mab_alert_rules.yml'
        ],
        'scrape_configs': [
            {
                'job_name': 'acgs-auth-service',
                'static_configs': [{'targets': ['localhost:8000']}],
                'metrics_path': '/metrics',
                'scrape_interval': '10s'
            },
            {
                'job_name': 'acgs-ac-service',
                'static_configs': [{'targets': ['localhost:8001']}],
                'metrics_path': '/metrics',
                'scrape_interval': '10s'
            },
            {
                'job_name': 'acgs-integrity-service',
                'static_configs': [{'targets': ['localhost:8002']}],
                'metrics_path': '/metrics',
                'scrape_interval': '10s'
            },
            {
                'job_name': 'acgs-fv-service',
                'static_configs': [{'targets': ['localhost:8003']}],
                'metrics_path': '/metrics',
                'scrape_interval': '10s'
            },
            {
                'job_name': 'acgs-gs-service-mab',
                'static_configs': [{'targets': ['localhost:8004']}],
                'metrics_path': '/api/v1/mab/metrics',
                'scrape_interval': '5s'  # More frequent for MAB metrics
            },
            {
                'job_name': 'acgs-pgc-service',
                'static_configs': [{'targets': ['localhost:8005']}],
                'metrics_path': '/metrics',
                'scrape_interval': '10s'
            }
        ],
        'alerting': {
            'alertmanagers': [
                {
                    'static_configs': [{'targets': ['localhost:9093']}]
                }
            ]
        }
    }
    
    # Create monitoring directory
    monitoring_dir = Path('monitoring')
    monitoring_dir.mkdir(exist_ok=True)
    
    # Write Prometheus config
    with open(monitoring_dir / 'prometheus.yml', 'w') as f:
        yaml.dump(prometheus_config, f, default_flow_style=False)
    
    print("✅ Prometheus configuration created")
    return True


def create_mab_alert_rules():
    """Create alert rules for MAB performance monitoring."""
    print("🚨 Creating MAB alert rules...")
    
    alert_rules = {
        'groups': [
            {
                'name': 'mab_performance_alerts',
                'rules': [
                    {
                        'alert': 'MABSuccessRateLow',
                        'expr': 'mab_overall_success_rate < 0.95',
                        'for': '2m',
                        'labels': {
                            'severity': 'warning',
                            'service': 'gs-service'
                        },
                        'annotations': {
                            'summary': 'MAB success rate below 95%',
                            'description': 'MAB overall success rate is {{ $value }} which is below the 95% threshold'
                        }
                    },
                    {
                        'alert': 'MABTemplateSelectionSlow',
                        'expr': 'mab_template_selection_duration_seconds > 0.2',
                        'for': '1m',
                        'labels': {
                            'severity': 'warning',
                            'service': 'gs-service'
                        },
                        'annotations': {
                            'summary': 'MAB template selection taking too long',
                            'description': 'MAB template selection duration is {{ $value }}s which exceeds 200ms threshold'
                        }
                    },
                    {
                        'alert': 'MABRewardThresholdLow',
                        'expr': 'mab_average_reward < 0.8',
                        'for': '5m',
                        'labels': {
                            'severity': 'critical',
                            'service': 'gs-service'
                        },
                        'annotations': {
                            'summary': 'MAB average reward below threshold',
                            'description': 'MAB average reward is {{ $value }} which is below the 0.8 threshold for 5 minutes'
                        }
                    },
                    {
                        'alert': 'MABOptimizationStalled',
                        'expr': 'increase(mab_total_optimizations[10m]) == 0',
                        'for': '10m',
                        'labels': {
                            'severity': 'warning',
                            'service': 'gs-service'
                        },
                        'annotations': {
                            'summary': 'MAB optimization has stalled',
                            'description': 'No MAB optimizations have occurred in the last 10 minutes'
                        }
                    }
                ]
            }
        ]
    }
    
    monitoring_dir = Path('monitoring')
    with open(monitoring_dir / 'mab_alert_rules.yml', 'w') as f:
        yaml.dump(alert_rules, f, default_flow_style=False)
    
    print("✅ MAB alert rules created")
    return True


def create_grafana_dashboard():
    """Create Grafana dashboard for MAB monitoring."""
    print("📈 Creating Grafana dashboard...")
    
    dashboard = {
        "dashboard": {
            "id": None,
            "title": "ACGS-PGP MAB Performance Dashboard",
            "tags": ["acgs", "mab", "performance"],
            "timezone": "browser",
            "refresh": "30s",
            "time": {
                "from": "now-1h",
                "to": "now"
            },
            "panels": [
                {
                    "id": 1,
                    "title": "MAB Success Rate",
                    "type": "stat",
                    "targets": [
                        {
                            "expr": "mab_overall_success_rate",
                            "legendFormat": "Success Rate"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "percentunit",
                            "min": 0,
                            "max": 1,
                            "thresholds": {
                                "steps": [
                                    {"color": "red", "value": 0},
                                    {"color": "yellow", "value": 0.95},
                                    {"color": "green", "value": 0.99}
                                ]
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 6, "x": 0, "y": 0}
                },
                {
                    "id": 2,
                    "title": "Template Selection Performance",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "mab_template_selection_duration_seconds",
                            "legendFormat": "Selection Time (s)"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "s",
                            "custom": {
                                "drawStyle": "line",
                                "lineInterpolation": "linear"
                            }
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 6, "y": 0}
                },
                {
                    "id": 3,
                    "title": "Template Usage Distribution",
                    "type": "piechart",
                    "targets": [
                        {
                            "expr": "mab_template_uses_total",
                            "legendFormat": "{{ template_name }}"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 6, "x": 18, "y": 0}
                },
                {
                    "id": 4,
                    "title": "Average Reward by Template",
                    "type": "bargauge",
                    "targets": [
                        {
                            "expr": "mab_template_average_reward",
                            "legendFormat": "{{ template_name }}"
                        }
                    ],
                    "fieldConfig": {
                        "defaults": {
                            "unit": "short",
                            "min": 0,
                            "max": 1
                        }
                    },
                    "gridPos": {"h": 8, "w": 12, "x": 0, "y": 8}
                },
                {
                    "id": 5,
                    "title": "Optimization Rate",
                    "type": "timeseries",
                    "targets": [
                        {
                            "expr": "rate(mab_total_optimizations[5m])",
                            "legendFormat": "Optimizations/sec"
                        }
                    ],
                    "gridPos": {"h": 8, "w": 12, "x": 12, "y": 8}
                }
            ]
        },
        "overwrite": True
    }
    
    monitoring_dir = Path('monitoring')
    with open(monitoring_dir / 'mab_dashboard.json', 'w') as f:
        json.dump(dashboard, f, indent=2)
    
    print("✅ Grafana dashboard configuration created")
    return True


def create_docker_monitoring_stack():
    """Create Docker Compose for monitoring stack."""
    print("🐳 Creating Docker monitoring stack...")
    
    docker_compose = {
        'version': '3.8',
        'services': {
            'prometheus': {
                'image': 'prom/prometheus:latest',
                'container_name': 'acgs-prometheus',
                'ports': ['9090:9090'],
                'volumes': [
                    './monitoring/prometheus.yml:/etc/prometheus/prometheus.yml',
                    './monitoring/mab_alert_rules.yml:/etc/prometheus/mab_alert_rules.yml'
                ],
                'command': [
                    '--config.file=/etc/prometheus/prometheus.yml',
                    '--storage.tsdb.path=/prometheus',
                    '--web.console.libraries=/etc/prometheus/console_libraries',
                    '--web.console.templates=/etc/prometheus/consoles',
                    '--storage.tsdb.retention.time=200h',
                    '--web.enable-lifecycle'
                ],
                'networks': ['acgs-monitoring']
            },
            'grafana': {
                'image': 'grafana/grafana:latest',
                'container_name': 'acgs-grafana',
                'ports': ['3001:3000'],  # Use 3001 to avoid conflicts
                'environment': [
                    'GF_SECURITY_ADMIN_PASSWORD=acgs_admin'
                ],
                'volumes': [
                    'grafana-storage:/var/lib/grafana',
                    './monitoring/mab_dashboard.json:/var/lib/grafana/dashboards/mab_dashboard.json'
                ],
                'networks': ['acgs-monitoring']
            },
            'alertmanager': {
                'image': 'prom/alertmanager:latest',
                'container_name': 'acgs-alertmanager',
                'ports': ['9093:9093'],
                'volumes': [
                    './monitoring/alertmanager.yml:/etc/alertmanager/alertmanager.yml'
                ],
                'networks': ['acgs-monitoring']
            }
        },
        'networks': {
            'acgs-monitoring': {
                'driver': 'bridge'
            }
        },
        'volumes': {
            'grafana-storage': {}
        }
    }
    
    with open('docker-compose-monitoring.yml', 'w') as f:
        yaml.dump(docker_compose, f, default_flow_style=False)
    
    print("✅ Docker monitoring stack configuration created")
    return True


def create_alertmanager_config():
    """Create AlertManager configuration."""
    print("🔔 Creating AlertManager configuration...")
    
    alertmanager_config = {
        'global': {
            'smtp_smarthost': 'localhost:587',
            'smtp_from': 'acgs-alerts@localhost'
        },
        'route': {
            'group_by': ['alertname'],
            'group_wait': '10s',
            'group_interval': '10s',
            'repeat_interval': '1h',
            'receiver': 'web.hook'
        },
        'receivers': [
            {
                'name': 'web.hook',
                'webhook_configs': [
                    {
                        'url': 'http://localhost:5001/alerts',
                        'send_resolved': True
                    }
                ]
            }
        ],
        'inhibit_rules': [
            {
                'source_match': {
                    'severity': 'critical'
                },
                'target_match': {
                    'severity': 'warning'
                },
                'equal': ['alertname', 'dev', 'instance']
            }
        ]
    }
    
    monitoring_dir = Path('monitoring')
    with open(monitoring_dir / 'alertmanager.yml', 'w') as f:
        yaml.dump(alertmanager_config, f, default_flow_style=False)
    
    print("✅ AlertManager configuration created")
    return True


async def test_mab_metrics_endpoint():
    """Test MAB metrics endpoint availability."""
    print("🧪 Testing MAB metrics endpoint...")
    
    try:
        import aiohttp
        
        async with aiohttp.ClientSession() as session:
            try:
                async with session.get('http://localhost:8004/api/v1/mab/metrics', timeout=5) as response:
                    if response.status == 200:
                        metrics_data = await response.json()
                        print(f"✅ MAB metrics endpoint responding: {len(metrics_data)} metrics available")
                        return True
                    else:
                        print(f"⚠️  MAB metrics endpoint returned status {response.status}")
                        return False
            except aiohttp.ClientConnectorError:
                print("⚠️  MAB metrics endpoint not available (GS service may not be running)")
                return False
                
    except ImportError:
        print("⚠️  aiohttp not available, skipping endpoint test")
        return True


async def main():
    """Setup MAB performance monitoring."""
    print("🚀 Setting up MAB Performance Monitoring...")
    print("=" * 70)
    
    setup_tasks = [
        ("Prometheus Configuration", create_prometheus_config),
        ("MAB Alert Rules", create_mab_alert_rules),
        ("Grafana Dashboard", create_grafana_dashboard),
        ("Docker Monitoring Stack", create_docker_monitoring_stack),
        ("AlertManager Configuration", create_alertmanager_config),
        ("MAB Metrics Endpoint Test", test_mab_metrics_endpoint),
    ]
    
    results = []
    for task_name, task_func in setup_tasks:
        print(f"\n📋 {task_name}...")
        try:
            if asyncio.iscoroutinefunction(task_func):
                result = await task_func()
            else:
                result = task_func()
            results.append((task_name, result))
            if result:
                print(f"✅ {task_name}: COMPLETED")
            else:
                print(f"⚠️  {task_name}: COMPLETED WITH WARNINGS")
        except Exception as e:
            print(f"❌ {task_name}: FAILED - {e}")
            results.append((task_name, False))
        
        print("-" * 50)
    
    # Summary
    print("\n📊 MAB Monitoring Setup Results:")
    print("=" * 70)
    
    completed = sum(1 for _, result in results if result)
    total = len(results)
    
    for task_name, result in results:
        status = "✅ COMPLETED" if result else "❌ FAILED"
        print(f"{task_name:.<40} {status}")
    
    print("-" * 70)
    print(f"Overall: {completed}/{total} tasks completed ({completed/total*100:.1f}%)")
    
    if completed == total:
        print("\n🎉 MAB Performance Monitoring setup completed successfully!")
        print("\n📋 Next Steps:")
        print("1. Start monitoring stack: docker-compose -f docker-compose-monitoring.yml up -d")
        print("2. Access Grafana dashboard: http://localhost:3001 (admin/acgs_admin)")
        print("3. Access Prometheus: http://localhost:9090")
        print("4. Access AlertManager: http://localhost:9093")
        print("5. Monitor MAB metrics at: http://localhost:8004/api/v1/mab/metrics")
        print("\n✅ Phase 3 Complete: Performance monitoring setup ready")
        return True
    else:
        print(f"\n⚠️  {total - completed} task(s) failed. Please review and fix issues.")
        return False


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
