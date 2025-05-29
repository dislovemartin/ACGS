"""
Policy Manifest Generation and Validation System

Addresses audit findings:
- Canonical manifest generation with SHA-256 checksums
- Framework breakdown tracking
- Provenance and integrity verification
- Reproducibility support
"""

import json
import hashlib
import os
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime, timezone
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

import logging
logger = logging.getLogger(__name__)


@dataclass
class PolicyFileInfo:
    """Information about a single policy file"""
    file_name: str
    file_path: str
    sha256: str
    size_bytes: int
    record_count: int
    framework: str
    last_modified: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = asdict(self)
        data['last_modified'] = self.last_modified.isoformat()
        return data


@dataclass
class FrameworkBreakdown:
    """Breakdown of policies by framework"""
    total_policies: int
    datalog_count: int
    rego_count: int
    json_count: int
    yaml_count: int
    unknown_count: int
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)
    
    @property
    def datalog_percentage(self) -> float:
        return (self.datalog_count / self.total_policies * 100) if self.total_policies > 0 else 0.0
    
    @property
    def rego_percentage(self) -> float:
        return (self.rego_count / self.total_policies * 100) if self.total_policies > 0 else 0.0
    
    @property
    def json_percentage(self) -> float:
        return (self.json_count / self.total_policies * 100) if self.total_policies > 0 else 0.0
    
    @property
    def yaml_percentage(self) -> float:
        return (self.yaml_count / self.total_policies * 100) if self.total_policies > 0 else 0.0


@dataclass
class PolicyManifest:
    """Complete policy dataset manifest"""
    manifest_version: str
    generated_at: datetime
    dataset_name: str
    dataset_version: str
    total_files: int
    total_policies: int
    framework_breakdown: FrameworkBreakdown
    files: List[PolicyFileInfo]
    integrity_info: Dict[str, Any]
    metadata: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        data = {
            'manifest_version': self.manifest_version,
            'generated_at': self.generated_at.isoformat(),
            'dataset_name': self.dataset_name,
            'dataset_version': self.dataset_version,
            'total_files': self.total_files,
            'total_policies': self.total_policies,
            'framework_breakdown': self.framework_breakdown.to_dict(),
            'files': [f.to_dict() for f in self.files],
            'integrity_info': self.integrity_info,
            'metadata': self.metadata
        }
        return data
    
    def to_json(self, indent: int = 2) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), indent=indent)


class ManifestManager:
    """
    Manages policy dataset manifests for integrity and reproducibility.
    """
    
    def __init__(self, manifest_version: str = "1.0"):
        self.manifest_version = manifest_version
    
    def generate_manifest(self, 
                         dataset_path: str,
                         dataset_name: str,
                         dataset_version: str,
                         include_patterns: List[str] = None,
                         exclude_patterns: List[str] = None) -> PolicyManifest:
        """
        Generate a comprehensive manifest for a policy dataset.
        
        Args:
            dataset_path: Path to the dataset directory
            dataset_name: Name of the dataset
            dataset_version: Version of the dataset
            include_patterns: File patterns to include (e.g., ['*.jsonl', '*.json'])
            exclude_patterns: File patterns to exclude
            
        Returns:
            PolicyManifest object
        """
        if include_patterns is None:
            include_patterns = ['*.jsonl', '*.json', '*.yaml', '*.yml', '*.rego']
        
        if exclude_patterns is None:
            exclude_patterns = ['.*', '__pycache__', '*.pyc']
        
        dataset_path = Path(dataset_path)
        if not dataset_path.exists():
            raise FileNotFoundError(f"Dataset path does not exist: {dataset_path}")
        
        logger.info(f"Generating manifest for dataset: {dataset_name} v{dataset_version}")
        
        # Collect file information
        files_info = []
        total_policies = 0
        framework_counts = {
            'datalog': 0,
            'rego': 0,
            'json': 0,
            'yaml': 0,
            'unknown': 0
        }
        
        for pattern in include_patterns:
            for file_path in dataset_path.rglob(pattern):
                if self._should_exclude_file(file_path, exclude_patterns):
                    continue
                
                try:
                    file_info = self._analyze_file(file_path, dataset_path)
                    files_info.append(file_info)
                    total_policies += file_info.record_count
                    
                    # Update framework counts
                    framework_key = file_info.framework.lower()
                    if framework_key in framework_counts:
                        framework_counts[framework_key] += file_info.record_count
                    else:
                        framework_counts['unknown'] += file_info.record_count
                        
                except Exception as e:
                    logger.warning(f"Failed to analyze file {file_path}: {e}")
                    continue
        
        # Create framework breakdown
        framework_breakdown = FrameworkBreakdown(
            total_policies=total_policies,
            datalog_count=framework_counts['datalog'],
            rego_count=framework_counts['rego'],
            json_count=framework_counts['json'],
            yaml_count=framework_counts['yaml'],
            unknown_count=framework_counts['unknown']
        )
        
        # Generate integrity information
        integrity_info = self._generate_integrity_info(files_info)
        
        # Create metadata
        metadata = {
            'generator': 'ACGS-PGP ManifestManager',
            'generator_version': '1.0',
            'dataset_path': str(dataset_path),
            'include_patterns': include_patterns,
            'exclude_patterns': exclude_patterns,
            'analysis_timestamp': datetime.now(timezone.utc).isoformat()
        }
        
        # Create manifest
        manifest = PolicyManifest(
            manifest_version=self.manifest_version,
            generated_at=datetime.now(timezone.utc),
            dataset_name=dataset_name,
            dataset_version=dataset_version,
            total_files=len(files_info),
            total_policies=total_policies,
            framework_breakdown=framework_breakdown,
            files=files_info,
            integrity_info=integrity_info,
            metadata=metadata
        )
        
        logger.info(f"Generated manifest: {len(files_info)} files, {total_policies} policies")
        return manifest
    
    def _should_exclude_file(self, file_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if file should be excluded based on patterns"""
        file_name = file_path.name
        for pattern in exclude_patterns:
            if file_name.startswith(pattern.replace('*', '')):
                return True
        return False
    
    def _analyze_file(self, file_path: Path, base_path: Path) -> PolicyFileInfo:
        """Analyze a single policy file"""
        # Calculate file hash
        sha256_hash = self._calculate_file_hash(file_path)
        
        # Get file stats
        stat = file_path.stat()
        size_bytes = stat.st_size
        last_modified = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc)
        
        # Determine framework and count records
        framework, record_count = self._analyze_file_content(file_path)
        
        # Calculate relative path
        relative_path = file_path.relative_to(base_path)
        
        return PolicyFileInfo(
            file_name=file_path.name,
            file_path=str(relative_path),
            sha256=sha256_hash,
            size_bytes=size_bytes,
            record_count=record_count,
            framework=framework,
            last_modified=last_modified
        )
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file"""
        sha256_hash = hashlib.sha256()
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()
    
    def _analyze_file_content(self, file_path: Path) -> Tuple[str, int]:
        """Analyze file content to determine framework and count records"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Determine framework
            framework = self._detect_framework_from_content(content, file_path.suffix)
            
            # Count records
            if file_path.suffix == '.jsonl':
                # JSONL file - count lines
                record_count = len([line for line in content.split('\n') if line.strip()])
            elif file_path.suffix in ['.json', '.yaml', '.yml']:
                # Single document files
                record_count = 1
            elif file_path.suffix == '.rego':
                # Rego files - count packages or rules
                record_count = len([line for line in content.split('\n') 
                                  if line.strip().startswith('package ') or 
                                     line.strip().startswith('allow ') or
                                     line.strip().startswith('deny ')])
                record_count = max(1, record_count)  # At least 1 record
            else:
                record_count = 1
            
            return framework, record_count
            
        except Exception as e:
            logger.warning(f"Failed to analyze content of {file_path}: {e}")
            return "Unknown", 1
    
    def _detect_framework_from_content(self, content: str, file_extension: str) -> str:
        """Detect policy framework from content"""
        content_lower = content.lower()
        
        # File extension based detection
        if file_extension == '.rego':
            return "Rego"
        elif file_extension in ['.json', '.jsonl']:
            return "JSON"
        elif file_extension in ['.yaml', '.yml']:
            return "YAML"
        
        # Content-based detection
        if 'package ' in content and ('allow' in content_lower or 'deny' in content_lower):
            return "Rego"
        elif content.strip().startswith('{') or '"Statement"' in content:
            return "JSON"
        elif any(line.strip().endswith(':') for line in content.split('\n')[:5]):
            return "YAML"
        elif '<=' in content or ':-' in content:
            return "Datalog"
        
        return "Unknown"
    
    def _generate_integrity_info(self, files_info: List[PolicyFileInfo]) -> Dict[str, Any]:
        """Generate integrity information for the dataset"""
        # Calculate overall dataset hash
        all_hashes = [f.sha256 for f in files_info]
        all_hashes.sort()  # Ensure deterministic order
        dataset_hash = hashlib.sha256(''.join(all_hashes).encode()).hexdigest()
        
        # Calculate total size
        total_size = sum(f.size_bytes for f in files_info)
        
        return {
            'dataset_hash': dataset_hash,
            'total_size_bytes': total_size,
            'hash_algorithm': 'SHA-256',
            'file_count': len(files_info),
            'integrity_check_timestamp': datetime.now(timezone.utc).isoformat()
        }
    
    def validate_manifest(self, manifest_path: str, dataset_path: str) -> Dict[str, Any]:
        """
        Validate a manifest against the actual dataset.
        
        Args:
            manifest_path: Path to the manifest file
            dataset_path: Path to the dataset directory
            
        Returns:
            Validation result dictionary
        """
        try:
            with open(manifest_path, 'r') as f:
                manifest_data = json.load(f)
            
            validation_result = {
                'is_valid': True,
                'errors': [],
                'warnings': [],
                'file_checks': []
            }
            
            dataset_path = Path(dataset_path)
            
            # Check each file in manifest
            for file_info in manifest_data.get('files', []):
                file_path = dataset_path / file_info['file_path']
                file_check = {
                    'file_path': file_info['file_path'],
                    'exists': file_path.exists(),
                    'hash_match': False,
                    'size_match': False
                }
                
                if file_path.exists():
                    # Check hash
                    actual_hash = self._calculate_file_hash(file_path)
                    expected_hash = file_info['sha256']
                    file_check['hash_match'] = actual_hash == expected_hash
                    
                    if not file_check['hash_match']:
                        validation_result['errors'].append(
                            f"Hash mismatch for {file_info['file_path']}: "
                            f"expected {expected_hash}, got {actual_hash}"
                        )
                        validation_result['is_valid'] = False
                    
                    # Check size
                    actual_size = file_path.stat().st_size
                    expected_size = file_info['size_bytes']
                    file_check['size_match'] = actual_size == expected_size
                    
                    if not file_check['size_match']:
                        validation_result['warnings'].append(
                            f"Size mismatch for {file_info['file_path']}: "
                            f"expected {expected_size}, got {actual_size}"
                        )
                else:
                    validation_result['errors'].append(f"File not found: {file_info['file_path']}")
                    validation_result['is_valid'] = False
                
                validation_result['file_checks'].append(file_check)
            
            return validation_result
            
        except Exception as e:
            return {
                'is_valid': False,
                'errors': [f"Validation failed: {str(e)}"],
                'warnings': [],
                'file_checks': []
            }
    
    def save_manifest(self, manifest: PolicyManifest, output_path: str) -> None:
        """Save manifest to file"""
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w') as f:
            f.write(manifest.to_json())
        
        logger.info(f"Manifest saved to: {output_path}")
    
    def load_manifest(self, manifest_path: str) -> PolicyManifest:
        """Load manifest from file"""
        with open(manifest_path, 'r') as f:
            data = json.load(f)
        
        # Convert back to PolicyManifest object
        files = [PolicyFileInfo(**f) for f in data['files']]
        framework_breakdown = FrameworkBreakdown(**data['framework_breakdown'])
        
        return PolicyManifest(
            manifest_version=data['manifest_version'],
            generated_at=datetime.fromisoformat(data['generated_at']),
            dataset_name=data['dataset_name'],
            dataset_version=data['dataset_version'],
            total_files=data['total_files'],
            total_policies=data['total_policies'],
            framework_breakdown=framework_breakdown,
            files=files,
            integrity_info=data['integrity_info'],
            metadata=data['metadata']
        )
