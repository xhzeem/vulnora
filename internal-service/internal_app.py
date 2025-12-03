#!/usr/bin/env python3
"""
Internal Service - SSRF Target
This service is only accessible from localhost/internal network
Contains secrets, flags, and simulates cloud metadata services
"""

from flask import Flask, jsonify, request
import os

app = Flask(__name__)

# Secrets and flags from environment
SECRET_FLAG = os.getenv('SECRET_FLAG', 'FLAG{ss4f_1nt3rn4l_4cc3ss}')
AWS_ACCESS_KEY = os.getenv('AWS_ACCESS_KEY', 'AKIAIOSFODNN7EXAMPLE')
AWS_SECRET_KEY = os.getenv('AWS_SECRET_KEY', 'wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY')
INTERNAL_API_KEY = os.getenv('INTERNAL_API_KEY', 'INTERNAL-SECRET-KEY-XYZ-12345')

@app.route('/')
def home():
    return jsonify({
        'service': 'Internal Admin Service',
        'version': '1.0.0',
        'status': 'running',
        'warning': 'This service should only be accessible from localhost'
    })

@app.route('/health')
def health():
    return jsonify({
        'status': 'healthy',
        'uptime': '99.9%',
        'services': {
            'database': 'online',
            'cache': 'online',
            'queue': 'online'
        }
    })

@app.route('/admin/secrets')
def admin_secrets():
    """
    SSRF Target - Contains sensitive information
    Only accessible via SSRF vulnerability
    """
    return jsonify({
        'flag': SECRET_FLAG,
        'internal_api_key': INTERNAL_API_KEY,
        'database_password': 'postgres',
        'admin_credentials': {
            'username': 'sysadmin',
            'password': 'SuperSecret123!'
        },
        'encryption_key': 'AES256-KEY-EXAMPLE-12345',
        'jwt_secret': 'jwt-secret-key-do-not-share',
        'stripe_api_key': 'sk_test_51Example',
        'aws_access_key_id': AWS_ACCESS_KEY,
        'aws_secret_access_key': AWS_SECRET_KEY
    })

@app.route('/admin/users')
def admin_users():
    """Internal user database with sensitive info"""
    return jsonify({
        'users': [
            {
                'id': 1,
                'username': 'admin',
                'email': 'admin@internal.local',
                'role': 'superadmin',
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...',
                'api_token': 'admin-token-12345'
            },
            {
                'id': 2,
                'username': 'developer',
                'email': 'dev@internal.local',
                'role': 'developer',
                'ssh_key': 'ssh-rsa AAAAB3NzaC1yc2EAAAADAQABAAABAQ...',
                'api_token': 'dev-token-67890'
            }
        ],
        'total_users': 247,
        'internal_flag': 'FLAG{int3rn4l_us3r_d4t4b4s3}'
    })

@app.route('/aws/latest/meta-data/')
@app.route('/aws/latest/meta-data/<path:path>')
def aws_metadata(path=''):
    """
    Simulates AWS EC2 Metadata Service
    Used to demonstrate cloud metadata SSRF
    """
    metadata = {
        '': 'ami-id\nami-launch-index\ninstance-id\ninstance-type\nlocal-hostname\nlocal-ipv4\npublic-hostname\npublic-ipv4\nsecurity-groups',
        'ami-id': 'ami-0abcdef1234567890',
        'instance-id': 'i-1234567890abcdef0',
        'instance-type': 't2.micro',
        'local-ipv4': '172.31.0.10',
        'public-ipv4': '54.123.45.67',
        'security-groups': 'default\nvulnerableshop-sg',
        'iam/security-credentials/': 'vulnerableshop-role',
        'iam/security-credentials/vulnerableshop-role': jsonify({
            'Code': 'Success',
            'LastUpdated': '2024-01-01T00:00:00Z',
            'Type': 'AWS-HMAC',
            'AccessKeyId': AWS_ACCESS_KEY,
            'SecretAccessKey': AWS_SECRET_KEY,
            'Token': 'IQoJb3JpZ2luX2VjEHYaCXVzLWVhc3QtMSJHMEUCIQCx...',
            'Expiration': '2024-12-31T23:59:59Z'
        }).get_data(as_text=True)
    }
    
    return metadata.get(path, f'Available endpoints:\n{metadata[""]}')

@app.route('/admin/database/dump')
def database_dump():
    """Simulates database dump endpoint"""
    return jsonify({
        'database': 'production_db',
        'tables': 127,
        'records': 1584092,
        'dump_url': 'file:///var/backups/db_dump_20240101.sql',
        'flag': 'FLAG{d4t4b4s3_dump_3xp0s3d}',
        'sensitive_data': {
            'credit_cards': 45823,
            'ssn_numbers': 12456,
            'passwords_plain': 8934
        }
    })

@app.route('/admin/logs')
def admin_logs():
    """Access logs with sensitive information"""
    return jsonify({
        'recent_logins': [
            {'ip': '192.168.1.100', 'user': 'admin', 'password_attempt': 'admin123', 'success': True},
            {'ip': '10.0.0.50', 'user': 'root', 'password_attempt': 'toor', 'success': False},
            {'ip': '172.16.0.10', 'user': 'sysadmin', 'password_attempt': 'SuperSecret123!', 'success': True}
        ],
        'api_calls': [
            {'endpoint': '/api/users', 'api_key': 'sk_live_12345', 'data': 'exported 500 users'},
            {'endpoint': '/api/payments', 'api_key': 'pk_test_67890', 'data': 'processed $15,000'}
        ],
        'flag': 'FLAG{l0g_f1l3s_l34k_s3cr3ts}'
    })

@app.route('/admin/config')
def admin_config():
    """System configuration with secrets"""
    return jsonify({
        'database': {
            'host': 'db.internal.local',
            'user': 'dbadmin',
            'password': 'DbAdminPass2024!',
            'port': 5432
        },
        'redis': {
            'host': 'redis.internal.local',
            'password': 'RedisSecretPass',
            'port': 6379
        },
        'email': {
            'smtp_host': 'smtp.gmail.com',
            'username': 'vulnerableshop@gmail.com',
            'password': 'EmailAppPassword123'
        },
        's3': {
            'bucket': 'vulnerableshop-uploads',
            'access_key': AWS_ACCESS_KEY,
            'secret_key': AWS_SECRET_KEY
        },
        'flag': 'FLAG{c0nf1g_f1l3s_3xp0s3d}'
    })

if __name__ == '__main__':
    print("=" * 60)
    print("Internal Service - SSRF Target")
    print("=" * 60)
    print("Running on http://0.0.0.0:8888")
    print("⚠️  This service simulates internal-only resources")
    print("=" * 60)
    app.run(host='0.0.0.0', port=8888, debug=True)
