#!/usr/bin/env python3
"""
Deployment and automation script for Altium to KiCAD Migration Tool.

This script provides functionality for:
- Building Python packages
- Creating Docker images
- Generating standalone executables
- Creating release packages
- Running CI/CD operations
- Setting up monitoring
- Running performance benchmarks
"""

import os
import sys
import subprocess
import shutil
import json
import yaml
import time
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
import argparse
import tempfile
import zipfile
import requests
from datetime import datetime

class DeploymentManager:
    """Manage deployment and distribution of the migration tool"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.version = self._get_version()
        self.logger = self._setup_logging()
        
    def _get_version(self) -> str:
        """Get current version from package"""
        try:
            version_file = self.project_root / "migration_tool" / "_version.py"
            if version_file.exists():
                exec(version_file.read_text())
                return locals().get('__version__', '1.0.0')
        except Exception:
            pass
        return '1.0.0'
    
    def _setup_logging(self) -> logging.Logger:
        """Setup logging for deployment operations"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        return logging.getLogger(__name__)
    
    def build_package(self) -> Dict[str, str]:
        """Build Python package for distribution"""
        self.logger.info("Building Python package...")
        
        # Clean previous builds
        build_dirs = ['build', 'dist', '*.egg-info']
        for pattern in build_dirs:
            for path in self.project_root.glob(pattern):
                if path.is_dir():
                    shutil.rmtree(path)
                else:
                    path.unlink()
        
        # Run build
        result = subprocess.run([
            sys.executable, 'setup.py', 'sdist', 'bdist_wheel'
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Package build failed: {result.stderr}")
        
        # Find built files
        dist_dir = self.project_root / "dist"
        wheel_files = list(dist_dir.glob("*.whl"))
        tar_files = list(dist_dir.glob("*.tar.gz"))
        
        return {
            'wheel': str(wheel_files[0]) if wheel_files else None,
            'source': str(tar_files[0]) if tar_files else None,
            'version': self.version
        }
    
    def build_docker_image(self, tag: Optional[str] = None) -> str:
        """Build Docker image"""
        if not tag:
            tag = f"altium-kicad-migration:{self.version}"
        
        self.logger.info(f"Building Docker image: {tag}")
        
        # Build image
        result = subprocess.run([
            'docker', 'build', '-t', tag, '.'
        ], cwd=self.project_root, capture_output=True, text=True)
        
        if result.returncode != 0:
            raise RuntimeError(f"Docker build failed: {result.stderr}")
        
        self.logger.info(f"Docker image built successfully: {tag}")
        return tag
    
    def create_standalone_executable(self, platform: str = "auto") -> Dict[str, str]:
        """Create standalone executable using PyInstaller"""
        try:
            import PyInstaller
        except ImportError:
            subprocess.run([sys.executable, '-m', 'pip', 'install', 'pyinstaller'])
        
        self.logger.info(f"Creating standalone executable for {platform}...")
        
        # Platform-specific settings
        if platform == "auto":
            platform = sys.platform
        
        output_dir = self.project_root / "dist" / f"standalone-{platform}"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Create CLI executable
        cli_result = subprocess.run([
            'pyinstaller',
            '--onefile',
            '--name', f'altium-kicad-migrate-{self.version}',
            '--distpath', str(output_dir),
            'migration_tool/cli.py'
        ], cwd=self.project_root, capture_output=True, text=True)
        
        # Create GUI executable
        gui_result = subprocess.run([
            'pyinstaller',
            '--onefile',
            '--windowed',
            '--name', f'migration-gui-{self.version}',
            '--distpath', str(output_dir),
            'migration_tool/gui.py'
        ], cwd=self.project_root, capture_output=True, text=True)
        
        executables = {}
        if cli_result.returncode == 0:
            cli_exe = output_dir / f'altium-kicad-migrate-{self.version}'
            if platform == "win32":
                cli_exe = cli_exe.with_suffix('.exe')
            executables['cli'] = str(cli_exe)
        
        if gui_result.returncode == 0:
            gui_exe = output_dir / f'migration-gui-{self.version}'
            if platform == "win32":
                gui_exe = gui_exe.with_suffix('.exe')
            executables['gui'] = str(gui_exe)
        
        return executables
    
    def create_release_package(self) -> str:
        """Create complete release package with all artifacts"""
        self.logger.info("Creating release package...")
        
        release_dir = self.project_root / "release" / f"v{self.version}"
        release_dir.mkdir(parents=True, exist_ok=True)
        
        # Build Python package
        python_package = self.build_package()
        
        # Copy Python artifacts
        if python_package['wheel']:
            shutil.copy2(python_package['wheel'], release_dir)
        if python_package['source']:
            shutil.copy2(python_package['source'], release_dir)
        
        # Build Docker image
        docker_tag = self.build_docker_image()
        
        # Create executables for multiple platforms
        platforms = ['win32', 'darwin', 'linux']
        for platform in platforms:
            try:
                executables = self.create_standalone_executable(platform)
                if executables:
                    platform_dir = release_dir / platform
                    platform_dir.mkdir(exist_ok=True)
                    for exe_type, exe_path in executables.items():
                        if Path(exe_path).exists():
                            shutil.copy2(exe_path, platform_dir)
            except Exception as e:
                self.logger.warning(f"Failed to create {platform} executable: {e}")
        
        # Create documentation package
        self._create_documentation_package(release_dir)
        
        # Create release manifest
        manifest = {
            'version': self.version,
            'build_date': datetime.now().isoformat(),
            'artifacts': {
                'python_wheel': python_package.get('wheel'),
                'python_source': python_package.get('source'),
                'docker_image': docker_tag,
                'executables': list((release_dir).rglob('*altium-kicad-migrate*')),
                'documentation': str(release_dir / 'docs.zip')
            }
        }
        
        manifest_path = release_dir / 'release_manifest.json'
        with open(manifest_path, 'w') as f:
            json.dump(manifest, f, indent=2, default=str)
        
        # Create release archive
        release_archive = self.project_root / f"altium-kicad-migration-v{self.version}.zip"
        with zipfile.ZipFile(release_archive, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in release_dir.rglob('*'):
                if file_path.is_file():
                    arcname = file_path.relative_to(release_dir)
                    zf.write(file_path, arcname)
        
        self.logger.info(f"Release package created: {release_archive}")
        return str(release_archive)
    
    def _create_documentation_package(self, output_dir: Path):
        """Create documentation package"""
        docs_dir = self.project_root / "docs"
        if not docs_dir.exists():
            return
        
        # Build Sphinx documentation if available
        try:
            subprocess.run(['make', 'html'], cwd=docs_dir, check=True)
            built_docs = docs_dir / "_build" / "html"
            if built_docs.exists():
                # Create documentation archive
                docs_archive = output_dir / "docs.zip"
                with zipfile.ZipFile(docs_archive, 'w', zipfile.ZIP_DEFLATED) as zf:
                    for file_path in built_docs.rglob('*'):
                        if file_path.is_file():
                            arcname = file_path.relative_to(built_docs)
                            zf.write(file_path, arcname)
        except Exception as e:
            self.logger.warning(f"Failed to build documentation: {e}")


class ContinuousIntegration:
    """Continuous Integration automation tools"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
    
    def run_quality_checks(self) -> Dict[str, bool]:
        """Run all code quality checks"""
        checks = {
            'formatting': self._check_formatting(),
            'linting': self._check_linting(),
            'type_checking': self._check_types(),
            'security': self._check_security(),
            'dependencies': self._check_dependencies()
        }
        
        self.logger.info("Quality check results:")
        for check, passed in checks.items():
            status = "✅ PASSED" if passed else "❌ FAILED"
            self.logger.info(f"  {check}: {status}")
        
        return checks
    
    def _check_formatting(self) -> bool:
        """Check code formatting with Black"""
        try:
            result = subprocess.run([
                'black', '--check', 'migration_tool/', 'tests/'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("Black not installed, skipping formatting check")
            return True
    
    def _check_linting(self) -> bool:
        """Check code with flake8"""
        try:
            result = subprocess.run([
                'flake8', 'migration_tool/', 'tests/'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("flake8 not installed, skipping lint check")
            return True
    
    def _check_types(self) -> bool:
        """Check types with mypy"""
        try:
            result = subprocess.run([
                'mypy', 'migration_tool/'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("mypy not installed, skipping type check")
            return True
    
    def _check_security(self) -> bool:
        """Check security with bandit"""
        try:
            result = subprocess.run([
                'bandit', '-r', 'migration_tool/'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("bandit not installed, skipping security check")
            return True
    
    def _check_dependencies(self) -> bool:
        """Check dependencies for vulnerabilities"""
        try:
            result = subprocess.run([
                'safety', 'check'
            ], capture_output=True, text=True)
            return result.returncode == 0
        except FileNotFoundError:
            self.logger.warning("safety not installed, skipping dependency check")
            return True
    
    def run_tests(self) -> Dict[str, Any]:
        """Run complete test suite"""
        test_results = {}
        
        # Unit tests
        result = subprocess.run([
            'pytest', 'tests/unit/', '-v', '--cov=migration_tool', '--cov-report=json'
        ], capture_output=True, text=True)
        
        test_results['unit_tests'] = {
            'passed': result.returncode == 0,
            'output': result.stdout,
            'coverage': self._parse_coverage_report()
        }
        
        # Integration tests
        result = subprocess.run([
            'pytest', 'tests/integration/', '-v'
        ], capture_output=True, text=True)
        
        test_results['integration_tests'] = {
            'passed': result.returncode == 0,
            'output': result.stdout
        }
        
        # Performance tests
        result = subprocess.run([
            'pytest', 'tests/performance/', '-v', '--benchmark-only'
        ], capture_output=True, text=True)
        
        test_results['performance_tests'] = {
            'passed': result.returncode == 0,
            'output': result.stdout
        }
        
        return test_results
    
    def _parse_coverage_report(self) -> Dict[str, Any]:
        """Parse coverage report from JSON"""
        try:
            coverage_file = self.project_root / "coverage.json"
            if coverage_file.exists():
                with open(coverage_file) as f:
                    coverage_data = json.load(f)
                return {
                    'percentage': coverage_data.get('totals', {}).get('percent_covered', 0),
                    'missing_lines': coverage_data.get('totals', {}).get('missing_lines', 0)
                }
        except Exception:
            pass
        return {'percentage': 0, 'missing_lines': 0}


class MonitoringSetup:
    """Setup monitoring and logging for production deployment"""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.logger = logging.getLogger(__name__)
    
    def create_prometheus_config(self) -> str:
        """Create Prometheus monitoring configuration"""
        config = {
            'global': {
                'scrape_interval': '15s',
                'evaluation_interval': '15s'
            },
            'scrape_configs': [
                {
                    'job_name': 'altium-kicad-migration',
                    'static_configs': [
                        {'targets': ['localhost:8080']}
                    ],
                    'metrics_path': '/metrics',
                    'scrape_interval': '30s'
                }
            ],
            'alerting': {
                'alertmanagers': [
                    {
                        'static_configs': [
                            {'targets': ['localhost:9093']}
                        ]
                    }
                ]
            }
        }
        
        config_path = self.project_root / "monitoring" / "prometheus.yml"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return str(config_path)
    
    def create_grafana_dashboard(self) -> str:
        """Create Grafana dashboard configuration"""
        dashboard = {
            'dashboard': {
                'id': None,
                'title': 'Altium to KiCAD Migration Tool',
                'tags': ['migration', 'kicad', 'altium'],
                'timezone': 'browser',
                'panels': [
                    {
                        'id': 1,
                        'title': 'Migration Success Rate',
                        'type': 'stat',
                        'targets': [
                            {
                                'expr': 'migration_success_total / migration_total * 100',
                                'legendFormat': 'Success Rate %'
                            }
                        ]
                    },
                    {
                        'id': 2,
                        'title': 'Migration Duration',
                        'type': 'graph',
                        'targets': [
                            {
                                'expr': 'migration_duration_seconds',
                                'legendFormat': 'Duration (seconds)'
                            }
                        ]
                    },
                    {
                        'id': 3,
                        'title': 'Components Processed',
                        'type': 'graph',
                        'targets': [
                            {
                                'expr': 'components_processed_total',
                                'legendFormat': 'Components'
                            }
                        ]
                    },
                    {
                        'id': 4,
                        'title': 'Error Rate',
                        'type': 'graph',
                        'targets': [
                            {
                                'expr': 'migration_errors_total',
                                'legendFormat': 'Errors'
                            }
                        ]
                    }
                ],
                'time': {
                    'from': 'now-1h',
                    'to': 'now'
                },
                'refresh': '30s'
            }
        }
        
        dashboard_path = self.project_root / "monitoring" / "grafana_dashboard.json"
        dashboard_path.parent.mkdir(exist_ok=True)
        
        with open(dashboard_path, 'w') as f:
            json.dump(dashboard, f, indent=2)
        
        return str(dashboard_path)
    
    def create_logging_config(self) -> str:
        """Create production logging configuration"""
        config = {
            'version': 1,
            'disable_existing_loggers': False,
            'formatters': {
                'standard': {
                    'format': '%(asctime)s [%(levelname)s] %(name)s: %(message)s'
                },
                'json': {
                    'format': '{"timestamp": "%(asctime)s", "level": "%(levelname)s", "logger": "%(name)s", "message": "%(message)s"}'
                }
            },
            'handlers': {
                'default': {
                    'level': 'INFO',
                    'formatter': 'standard',
                    'class': 'logging.StreamHandler',
                    'stream': 'ext://sys.stdout'
                },
                'file': {
                    'level': 'DEBUG',
                    'formatter': 'json',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': '/var/log/migration_tool/app.log',
                    'maxBytes': 10485760,
                    'backupCount': 5
                },
                'error_file': {
                    'level': 'ERROR',
                    'formatter': 'json',
                    'class': 'logging.handlers.RotatingFileHandler',
                    'filename': '/var/log/migration_tool/error.log',
                    'maxBytes': 10485760,
                    'backupCount': 5
                }
            },
            'loggers': {
                '': {
                    'handlers': ['default', 'file', 'error_file'],
                    'level': 'DEBUG',
                    'propagate': False
                }
            }
        }
        
        config_path = self.project_root / "config" / "logging_production.yaml"
        config_path.parent.mkdir(exist_ok=True)
        
        with open(config_path, 'w') as f:
            yaml.dump(config, f, default_flow_style=False)
        
        return str(config_path)


def main():
    """Main entry point for automation scripts"""
    parser = argparse.ArgumentParser(description="Altium to KiCAD Migration Tool - Automation Scripts")
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Deployment commands
    deploy_parser = subparsers.add_parser('deploy', help='Deployment operations')
    deploy_parser.add_argument('--build-package', action='store_true', help='Build Python package')
    deploy_parser.add_argument('--build-docker', action='store_true', help='Build Docker image')
    deploy_parser.add_argument('--build-executable', action='store_true', help='Build standalone executable')
    deploy_parser.add_argument('--create-release', action='store_true', help='Create complete release package')
    
    # CI commands
    ci_parser = subparsers.add_parser('ci', help='Continuous integration operations')
    ci_parser.add_argument('--quality-checks', action='store_true', help='Run quality checks')
    ci_parser.add_argument('--run-tests', action='store_true', help='Run test suite')
    ci_parser.add_argument('--full-ci', action='store_true', help='Run complete CI pipeline')
    
    # Monitoring commands
    monitor_parser = subparsers.add_parser('monitor', help='Setup monitoring')
    monitor_parser.add_argument('--prometheus', action='store_true', help='Create Prometheus config')
    monitor_parser.add_argument('--grafana', action='store_true', help='Create Grafana dashboard')
    monitor_parser.add_argument('--logging', action='store_true', help='Create logging config')
    
    args = parser.parse_args()
    
    if args.command == 'deploy':
        manager = DeploymentManager()
        
        if args.build_package:
            result = manager.build_package()
            print(f"Package built: {result}")
        
        if args.build_docker:
            tag = manager.build_docker_image()
            print(f"Docker image built: {tag}")
        
        if args.build_executable:
            executables = manager.create_standalone_executable()
            print(f"Executables created: {executables}")
        
        if args.create_release:
            package = manager.create_release_package()
            print(f"Release package created: {package}")
    
    elif args.command == 'ci':
        ci = ContinuousIntegration()
        
        if args.quality_checks or args.full_ci:
            checks = ci.run_quality_checks()
            if not all(checks.values()):
                sys.exit(1)
        
        if args.run_tests or args.full_ci:
            results = ci.run_tests()
            for test_type, result in results.items():
                if not result['passed']:
                    print(f"{test_type} failed")
                    sys.exit(1)
        
        print("CI pipeline completed successfully")
    
    elif args.command == 'monitor':
        monitor = MonitoringSetup()
        
        if args.prometheus:
            config = monitor.create_prometheus_config()
            print(f"Prometheus config created: {config}")
        
        if args.grafana:
            dashboard = monitor.create_grafana_dashboard()
            print(f"Grafana dashboard created: {dashboard}")
        
        if args.logging:
            config = monitor.create_logging_config()
            print(f"Logging config created: {config}")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()