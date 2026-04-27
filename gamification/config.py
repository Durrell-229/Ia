"""
Configuration complète pour déploiement haute échelle
Optimisations: Redis, Database Indexing, Caching, CDN, Load Balancing
"""

# ===========================================================================
# DATABASE OPTIMIZATIONS (PostgreSQL/MySQL)
# ===========================================================================

DATABASE_OPTIMIZATIONS = {
    # Indexes à créer sur tables principales
    'indexes': [
        # Gamification models
        ('gamification_globalleaderboard', ['user_id', 'periode', 'score_total']),
        ('gamification_userbadges', ['user_id', 'badge_id']),
        ('gamification_xpaction', ['user_id', 'created_at']),
        
        # Composition models  
        ('compositions_compositionsession', ['eleve_id', 'exam_id']),
        ('compositions_resultat', ['session_id', 'note']),
        
        # Bulletin models
        ('bulletins_bulletin', ['eleve_id', 'periode', 'annee_scolaire']),
    ],
    
    # Partitions pour historical data (très utile pour grandes communautés)
    'partitions': [
        {
            'table': 'xpaction',
            'partition_by': 'created_at',
            'interval': 'MONTHLY',
        },
        {
            'table': 'compositionsession', 
            'partition_by': 'created_at',
            'interval': 'MONTHLY',
        }
    ],
    
    # Connection pool settings (gunicorn/workers)
    'pool_size': 20,
    'max_overflow': 10,
    'pool_timeout': 30,
    'pool_recycle': 1800,
}


# ===========================================================================
# CACHING STRATEGY (Redis)
# ===========================================================================

CACHING_CONFIG = {
    'backend': 'django_redis.cache.RedisCache',
    'location': 'redis://localhost:6379/1',
    'options': {
        'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        'MAX_ENTRIES': 10000,  # Max entries before eviction
        'CULL_FREQUENCY': 1/3,  # Remove 1/3 when max reached
    },
    
    'cache_targets': {
        # Leaderboards - cache très agressif (1h)
        'leaderboard_global_all_time': {
            'timeout': 3600,  # 1 hour
            'key_prefix': 'lb:global:all_time',
        },
        'leaderboard_weekly': {
            'timeout': 1800,  # 30 minutes
            'key_prefix': 'lb:weekly',
        },
        
        # User stats - cache court terme (15min)
        'user_stats': {
            'timeout': 900,  # 15 minutes
            'key_prefix': 'stats:user:',
        },
        
        # Badges user owns - cache moyen terme (30min)
        'user_badges': {
            'timeout': 1800,
            'key_prefix': 'badges:user:',
        },
        
        # XP actions recent - very short cache (5min)
        'recent_xp_actions': {
            'timeout': 300,  # 5 minutes
            'key_prefix': 'xp:recent:',
        },
    },
    
    # Cache warming strategy
    'warming_jobs': [
        {
            'task': 'load_top_100_leaderboard',
            'schedule': 'every hour at minute 0',
        },
        {
            'task': 'precompute_daily_ranks',
            'schedule': 'daily at 00:00',
        },
    ]
}


# ===========================================================================
# CELERY CONFIGURATION FOR HIGH LOAD
# ===========================================================================

CELERY_HIGH_SCALE = {
    # Worker configuration
    'worker_hws': {
        'concurrency': 8,  # Workers par instance
        'prefetch_multiplier': 4,  # Tasks pré-fetch
        'max_tasks_per_child': 1000,  # Reset worker après 1000 tasks
        'without_gossip': True,
        'without_mingle': True,
    },
    
    # Beat schedule - periodic tasks
    'beat_schedule': {
        # Leaderboard updates
        'update-leaderboard-every-hour': {
            'task': 'gamification.tasks.calculate_leaderboard_positions',
            'schedule': 3600,  # Every hour
            'options': {'queue': 'high_priority'},
        },
        
        # Badge checking
        'check-badges-every-30-minutes': {
            'task': 'gamification.tasks.check_badge_conditions_periodically',
            'schedule': 1800,  # Every 30 min
            'options': {'queue': 'background'},
        },
        
        # Weekly summary
        'weekly-leaderboard-summary': {
            'task': 'gamification.tasks.generate_weekly_leaderboard_summary',
            'schedule': 604800,  # Every week (Monday)
            'options': {'queue': 'low_priority'},
        },
        
        # Clean old stale data
        'cleanup-stale-data-daily': {
            'task': 'gamification.tasks.cleanup_stale_records',
            'schedule': 86400,  # Daily at midnight
            'options': {'queue': 'maintenance'},
        },
    },
    
    # Task routing & queues
    'task_routes': {
        'gamification.tasks.award_xp_points': {'queue': 'fast'},
        'gamification.tasks.claim_daily_reward': {'queue': 'fast'},
        'gamification.tasks.calculate_leaderboard_positions': {'queue': 'high_priority'},
        'gamification.tasks.check_badge_conditions_periodically': {'queue': 'background'},
        'gamification.tasks.generate_weekly_leaderboard_summary': {'queue': 'low_priority'},
    },
    
    # Queue priorities (for load balancing)
    'queues_config': {
        'fast': {
            'consumers': 3,  # High priority workers
            'priority': 'P1',
        },
        'high_priority': {
            'consumers': 5,
            'priority': 'P2',
        },
        'background': {
            'consumers': 2,
            'priority': 'P3',
        },
        'low_priority': {
            'consumers': 1,
            'priority': 'P4',
        },
    },
}


# ===========================================================================
# PERFORMANCE MONITORING & METRICS
# ===========================================================================

MONITORING_CONFIG = {
    # Metrics to track
    'metrics': [
        {
            'name': 'leaderboard_query_latency',
            'type': 'histogram',
            'labels': ['period'],
            'threshold_warn_ms': 100,
            'threshold_error_ms': 500,
        },
        {
            'name': 'badge_award_rate',
            'type': 'counter',
            'labels': ['badge_type'],
            'alert_threshold_increase': 100,  # Per minute
        },
        {
            'name': 'xp_awarded_total',
            'type': 'counter',
            'labels': ['action_type'],
        },
        {
            'name': 'active_users_count',
            'type': 'gauge',
            'refresh_interval_seconds': 60,
        },
    ],
    
    # Health check endpoints
    'health_checks': [
        {
            'endpoint': '/health/gamification/',
            'checks': [
                'database_connection',
                'redis_connection',
                'celery_worker_availability',
            ],
        },
    ],
    
    # Alerting thresholds
    'alerts': {
        'leaderboard_slow_queries': {
            'condition': 'avg_latency > 200ms for 5m',
            'notify': ['devops@academie.bj'],
        },
        'badge_award_spikes': {
            'condition': 'rate(badge_award[1m]) > 50',
            'notify': ['security@academie.bj'],
        },
        'celery_queue_backlog': {
            'condition': 'celery_queue_depth > 1000 for 10m',
            'notify': ['infra@academie.bj'],
        },
    },
}


# ===========================================================================
# SECURITY & RATE LIMITING
# ===========================================================================

SECURITY_CONFIG = {
    # Rate limiting per user IP
    'rate_limits': {
        'xp_claim_per_minute': 10,  # Max 10 requests/min
        'badge_check_per_hour': 100,  # Max 100 checks/hour
        'leaderboard_access_per_minute': 60,  # Standard access
    },
    
    # Anti-cheat measures
    'anti_cheat': {
        'suspicious_xp_gains_detection': True,
        'unusual_leading_score_alert': True,
        'streak_manipulation_detection': True,
        'max_xp_per_hour': 1000,  # Hard limit
    },
    
    # Data integrity
    'data_validation': {
        'require_timestamp_consistency': True,
        'audit_all_xp_transactions': True,
        'log_all_league_changes': True,
    },
}


# ===========================================================================
# SCALING RECOMMENDATIONS
# ===========================================================================

SCALING_GUIDE = {
    # Small scale (< 10K users)
    'small_scale': {
        'database': {
            'type': 'Single PostgreSQL instance',
            'ram': '8GB',
            'cpu': '4 cores',
            'storage': '100GB SSD',
        },
        'redis': {
            'type': 'Single instance',
            'ram': '2GB',
        },
        'celery_workers': 2,
        'web_servers': 1,
        'monthly_cost_usd': '~$50-100',
    },
    
    # Medium scale (10K-100K users)
    'medium_scale': {
        'database': {
            'type': 'PostgreSQL with Read Replicas',
            'ram': '16GB',
            'cpu': '8 cores',
            'storage': '500GB SSD',
            'read_replicas': 2,
        },
        'redis': {
            'type': 'Redis Cluster (3 master + 3 slave)',
            'ram': '8GB total',
        },
        'celery_workers': 4,
        'web_servers': 2,
        'load_balancer': True,
        'cdn': True,
        'monthly_cost_usd': '~$300-500',
    },
    
    # Large scale (100K+ users)
    'large_scale': {
        'database': {
            'type': 'PostgreSQL sharding + TimescaleDB',
            'ram': '64GB',
            'cpu': '16 cores',
            'storage': '2TB NVMe',
            'sharding_key': 'user_id',
            'read_replicas': 4,
        },
        'redis': {
            'type': 'Redis Cluster (6 master + 6 slave)',
            'ram': '32GB total',
            'cluster_mode': 'enabled',
        },
        'celery_workers': 8,
        'web_servers': 4,
        'load_balancer': 'AWS ALB / Nginx',
        'cdn': 'CloudFront / Cloudflare',
        'monitoring': 'Prometheus + Grafana + Sentry',
        'backup': 'Daily incremental, weekly full',
        'monthly_cost_usd': '~$1000-2000',
    },
}


# ===========================================================================
# DEPLOYMENT CHECKLIST
# ===========================================================================

DEPLOYMENT_CHECKLIST = [
    # Pre-deployment
    'Run database migrations',
    'Create necessary indexes',
    'Setup Redis cluster',
    'Configure Celery workers',
    'Setup monitoring stack (Prometheus/Grafana)',
    'Configure CDN for static files',
    
    # During deployment
    'Enable read-only mode for DB if needed',
    'Apply migrations incrementally',
    'Update DNS records slowly (TTL reduction first)',
    'Start new pods/instances gradually',
    'Health check each instance before adding to LB',
    
    # Post-deployment
    'Verify all services healthy',
    'Run smoke tests',
    'Check Celery task processing',
    'Monitor error rates (should be < 0.1%)',
    'Verify leaderboard calculations accurate',
    'Test badge awarding flow end-to-end',
    'Monitor cache hit ratios (> 80% target)',
]


# ===========================================================================
# BACKUP & DISASTER RECOVERY
# ===========================================================================

BACKUP_STRATEGY = {
    'database': {
        'frequency': 'Daily at 02:00 UTC',
        'retention': {
            'daily': 7,      # Keep 7 days
            'weekly': 4,     # Keep 4 weeks
            'monthly': 12,   # Keep 12 months
        },
        'storage': 'S3 Glacier Deep Archive',
        'encryption': 'AES-256',
    },
    
    'redis': {
        'rdb_snapshots': 'Every 6 hours',
        'aof_logging': 'Every second',
        'backup_to': 'S3 Standard',
    },
    
    'recovery_objectives': {
        'RPO': '15 minutes',  # Recovery Point Objective
        'RTO': '1 hour',      # Recovery Time Objective
    },
}


# ===========================================================================
# API RATE LIMITING (Django Ninja)
# ===========================================================================

API_RATE_LIMITS = {
    'default': '100/minute',
    'authenticated': '500/minute',
    'leaderboard_endpoints': '30/minute',
    'badge_claim': '10/minute',
    'xp_operations': '60/minute',
}
