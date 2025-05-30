"""
Policy Format Router and Converter

Addresses audit findings:
- Framework homogenisation (JSON/YAML/Rego conversion)
- Automatic format detection and routing
- Missing module stubber for OPA imports
- Syntax validation pipeline
"""

import json
import yaml
import re
import hashlib
import tempfile
import subprocess
from typing import Dict, Any, List, Optional, Tuple, Union
from pathlib import Path
from dataclasses import dataclass
from enum import Enum

import logging
logger = logging.getLogger(__name__)


class PolicyFramework(Enum):
    """Supported policy frameworks"""
    DATALOG = "Datalog"
    REGO = "Rego"
    JSON = "JSON"
    YAML = "YAML"
    UNKNOWN = "Unknown"


@dataclass
class PolicyConversionResult:
    """Result of policy format conversion"""
    success: bool
    converted_content: Optional[str]
    target_framework: PolicyFramework
    error_message: Optional[str]
    warnings: List[str]
    import_dependencies: List[str]


@dataclass
class PolicyValidationResult:
    """Result of policy syntax validation"""
    is_valid: bool
    error_message: Optional[str]
    warnings: List[str]
    missing_imports: List[str]


class PolicyFormatRouter:
    """
    Routes and converts policies between different frameworks.
    Implements automatic format detection and conversion pipeline.
    """
    
    def __init__(self, opa_executable_path: str = "opa"):
        self.opa_executable_path = opa_executable_path
        self._check_opa_availability()
    
    def _check_opa_availability(self) -> bool:
        """Check if OPA executable is available"""
        try:
            result = subprocess.run(
                [self.opa_executable_path, "version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"OPA available: {result.stdout.strip()}")
                return True
            else:
                logger.warning(f"OPA not available: {result.stderr}")
                return False
        except Exception as e:
            logger.warning(f"OPA check failed: {e}")
            return False
    
    def detect_framework(self, content: str, metadata: Optional[Dict[str, Any]] = None) -> PolicyFramework:
        """
        Detect the framework of a policy based on content and metadata.
        
        Args:
            content: Policy content string
            metadata: Optional metadata dict with 'framework' field
            
        Returns:
            Detected PolicyFramework
        """
        # Check metadata first
        if metadata and 'framework' in metadata:
            framework_str = metadata['framework'].upper()
            try:
                return PolicyFramework(framework_str.title())
            except ValueError:
                pass
        
        # Content-based detection
        content_stripped = content.strip()
        
        # JSON detection
        if content_stripped.startswith('{') and content_stripped.endswith('}'):
            try:
                json.loads(content)
                return PolicyFramework.JSON
            except json.JSONDecodeError:
                pass
        
        # YAML detection
        if any(line.strip().endswith(':') for line in content.split('\n')[:5]):
            try:
                yaml.safe_load(content)
                return PolicyFramework.YAML
            except yaml.YAMLError:
                pass
        
        # Rego detection
        if re.search(r'\bpackage\s+\w+', content) or re.search(r'\bdefault\s+\w+\s*=', content):
            return PolicyFramework.REGO
        
        # Datalog detection (fallback for rule-like syntax)
        if re.search(r'\w+\([^)]*\)\s*<=', content) or re.search(r'\w+\([^)]*\)\s*:-', content):
            return PolicyFramework.DATALOG
        
        return PolicyFramework.UNKNOWN
    
    def convert_to_rego(self, content: str, source_framework: PolicyFramework, 
                       policy_name: str = "converted_policy") -> PolicyConversionResult:
        """
        Convert policy content to Rego format.
        
        Args:
            content: Source policy content
            source_framework: Source framework type
            policy_name: Name for the converted policy
            
        Returns:
            PolicyConversionResult with conversion details
        """
        warnings = []
        import_dependencies = []
        
        try:
            if source_framework == PolicyFramework.REGO:
                # Already Rego, just validate and extract dependencies
                validation = self.validate_rego_syntax(content)
                return PolicyConversionResult(
                    success=True,
                    converted_content=content,
                    target_framework=PolicyFramework.REGO,
                    error_message=None,
                    warnings=validation.warnings,
                    import_dependencies=validation.missing_imports
                )
            
            elif source_framework == PolicyFramework.JSON:
                return self._convert_json_to_rego(content, policy_name)
            
            elif source_framework == PolicyFramework.YAML:
                return self._convert_yaml_to_rego(content, policy_name)
            
            elif source_framework == PolicyFramework.DATALOG:
                return self._convert_datalog_to_rego(content, policy_name)
            
            else:
                return PolicyConversionResult(
                    success=False,
                    converted_content=None,
                    target_framework=PolicyFramework.REGO,
                    error_message=f"Unsupported source framework: {source_framework}",
                    warnings=[],
                    import_dependencies=[]
                )
                
        except Exception as e:
            logger.error(f"Conversion error: {e}")
            return PolicyConversionResult(
                success=False,
                converted_content=None,
                target_framework=PolicyFramework.REGO,
                error_message=str(e),
                warnings=[],
                import_dependencies=[]
            )
    
    def _convert_json_to_rego(self, json_content: str, policy_name: str) -> PolicyConversionResult:
        """Convert JSON policy (e.g., Azure Policy) to Rego"""
        try:
            policy_data = json.loads(json_content)
            warnings = []
            
            # Handle Azure Policy format
            if 'properties' in policy_data and 'policyRule' in policy_data['properties']:
                azure_rule = policy_data['properties']['policyRule']
                rego_content = self._azure_policy_to_rego(azure_rule, policy_name)
                warnings.append("Converted from Azure Policy format - manual review recommended")
            
            # Handle AWS IAM Policy format
            elif 'Statement' in policy_data:
                rego_content = self._aws_iam_to_rego(policy_data, policy_name)
                warnings.append("Converted from AWS IAM Policy format - manual review recommended")
            
            else:
                # Generic JSON to Rego conversion
                rego_content = self._generic_json_to_rego(policy_data, policy_name)
                warnings.append("Generic JSON conversion - manual review required")
            
            return PolicyConversionResult(
                success=True,
                converted_content=rego_content,
                target_framework=PolicyFramework.REGO,
                error_message=None,
                warnings=warnings,
                import_dependencies=[]
            )
            
        except json.JSONDecodeError as e:
            return PolicyConversionResult(
                success=False,
                converted_content=None,
                target_framework=PolicyFramework.REGO,
                error_message=f"Invalid JSON: {e}",
                warnings=[],
                import_dependencies=[]
            )
    
    def _convert_yaml_to_rego(self, yaml_content: str, policy_name: str) -> PolicyConversionResult:
        """Convert YAML policy to Rego"""
        try:
            policy_data = yaml.safe_load(yaml_content)
            
            # Convert YAML dict to JSON then to Rego
            json_content = json.dumps(policy_data)
            return self._convert_json_to_rego(json_content, policy_name)
            
        except yaml.YAMLError as e:
            return PolicyConversionResult(
                success=False,
                converted_content=None,
                target_framework=PolicyFramework.REGO,
                error_message=f"Invalid YAML: {e}",
                warnings=[],
                import_dependencies=[]
            )
    
    def _convert_datalog_to_rego(self, datalog_content: str, policy_name: str) -> PolicyConversionResult:
        """Convert Datalog rules to Rego format"""
        warnings = ["Datalog to Rego conversion is experimental - manual review required"]
        
        # Basic Datalog to Rego conversion
        rego_lines = [
            f"package {policy_name.replace('-', '_')}",
            "",
            "# Converted from Datalog",
            "default allow = false",
            ""
        ]
        
        # Convert Datalog rules to Rego format
        for line in datalog_content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#'):
                rego_lines.append(line)
                continue
            
            # Convert Datalog rule syntax to Rego
            if '<=' in line:
                # Convert "head <= body" to Rego format
                head, body = line.split('<=', 1)
                head = head.strip()
                body = body.strip()
                
                rego_lines.append(f"allow {{")
                rego_lines.append(f"    # {head}")
                rego_lines.append(f"    {self._convert_datalog_body_to_rego(body)}")
                rego_lines.append("}")
                rego_lines.append("")
        
        rego_content = '\n'.join(rego_lines)
        
        return PolicyConversionResult(
            success=True,
            converted_content=rego_content,
            target_framework=PolicyFramework.REGO,
            error_message=None,
            warnings=warnings,
            import_dependencies=[]
        )
    
    def _azure_policy_to_rego(self, azure_rule: Dict[str, Any], policy_name: str) -> str:
        """Convert Azure Policy rule to Rego"""
        package_name = policy_name.replace('-', '_').replace(' ', '_').lower()
        
        rego_lines = [
            f"package azure.{package_name}",
            "",
            "# Converted from Azure Policy",
            "default allow = false",
            "default deny = false",
            ""
        ]
        
        # Handle Azure Policy effects
        effect = azure_rule.get('then', {}).get('effect', 'deny')
        
        if effect.lower() == 'deny':
            rego_lines.extend([
                "deny {",
                f"    # Azure Policy condition",
                f"    {self._convert_azure_condition_to_rego(azure_rule.get('if', {}))}",
                "}",
                ""
            ])
        else:
            rego_lines.extend([
                "allow {",
                f"    # Azure Policy condition",
                f"    {self._convert_azure_condition_to_rego(azure_rule.get('if', {}))}",
                "}",
                ""
            ])
        
        return '\n'.join(rego_lines)
    
    def _aws_iam_to_rego(self, iam_policy: Dict[str, Any], policy_name: str) -> str:
        """Convert AWS IAM Policy to Rego"""
        package_name = policy_name.replace('-', '_').replace(' ', '_').lower()
        
        rego_lines = [
            f"package aws.{package_name}",
            "",
            "# Converted from AWS IAM Policy",
            "default allow = false",
            ""
        ]
        
        statements = iam_policy.get('Statement', [])
        if not isinstance(statements, list):
            statements = [statements]
        
        for i, statement in enumerate(statements):
            effect = statement.get('Effect', 'Deny')
            actions = statement.get('Action', [])
            resources = statement.get('Resource', [])
            
            if effect.lower() == 'allow':
                rego_lines.extend([
                    f"allow {{",
                    f"    # Statement {i+1}",
                    f"    input.action in {json.dumps(actions if isinstance(actions, list) else [actions])}",
                    f"    input.resource in {json.dumps(resources if isinstance(resources, list) else [resources])}",
                    "}",
                    ""
                ])
        
        return '\n'.join(rego_lines)
    
    def _generic_json_to_rego(self, json_data: Dict[str, Any], policy_name: str) -> str:
        """Generic JSON to Rego conversion"""
        package_name = policy_name.replace('-', '_').replace(' ', '_').lower()
        
        rego_lines = [
            f"package generic.{package_name}",
            "",
            "# Generic JSON conversion",
            "default allow = false",
            "",
            "# Converted from generic JSON structure",
            "allow {",
            "    # Basic allow rule - customize based on requirements",
            "    input.action == \"read\"",
            "}",
            "",
            f"# Original JSON structure: {json.dumps(json_data, indent=2)}",
            ""
        ]
        
        return '\n'.join(rego_lines)
    
    def _convert_azure_condition_to_rego(self, condition: Dict[str, Any]) -> str:
        """Convert Azure Policy condition to Rego syntax"""
        # Basic conversion for common Azure Policy conditions
        if isinstance(condition, dict):
            if 'field' in condition and 'equals' in condition:
                field = condition['field'].replace('.', '_')
                value = condition['equals']
                return f"input.{field} == \"{value}\""
            elif 'field' in condition and 'in' in condition:
                field = condition['field'].replace('.', '_')
                values = condition['in']
                value_list = ', '.join([f'"{v}"' for v in values])
                return f"input.{field} in [{value_list}]"

        # Fallback for complex conditions
        return f"# Complex condition: {json.dumps(condition)}"
    
    def _convert_datalog_body_to_rego(self, body: str) -> str:
        """Convert Datalog body to Rego syntax"""
        # Basic conversion of Datalog predicates to Rego
        body = body.replace('&', '\n    ')
        return body
    
    def validate_rego_syntax(self, rego_content: str) -> PolicyValidationResult:
        """
        Validate Rego syntax using OPA parse command.
        
        Args:
            rego_content: Rego policy content to validate
            
        Returns:
            PolicyValidationResult with validation details
        """
        try:
            with tempfile.NamedTemporaryFile(mode='w', suffix='.rego', delete=False) as f:
                f.write(rego_content)
                temp_file = f.name
            
            # Run OPA parse
            result = subprocess.run(
                [self.opa_executable_path, "parse", temp_file],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Clean up temp file
            Path(temp_file).unlink()
            
            if result.returncode == 0:
                # Extract import dependencies
                missing_imports = self._extract_missing_imports(rego_content, result.stderr)
                
                return PolicyValidationResult(
                    is_valid=True,
                    error_message=None,
                    warnings=[],
                    missing_imports=missing_imports
                )
            else:
                return PolicyValidationResult(
                    is_valid=False,
                    error_message=result.stderr,
                    warnings=[],
                    missing_imports=[]
                )
                
        except Exception as e:
            return PolicyValidationResult(
                is_valid=False,
                error_message=str(e),
                warnings=[],
                missing_imports=[]
            )
    
    def _extract_missing_imports(self, rego_content: str, stderr_output: str) -> List[str]:
        """Extract missing import dependencies from Rego content and OPA output"""
        missing_imports = []
        
        # Look for data.* references in the code
        import_pattern = r'data\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
        imports = re.findall(import_pattern, rego_content)
        
        # Check stderr for undefined references
        if 'undefined' in stderr_output.lower():
            undefined_pattern = r'undefined.*?data\.([a-zA-Z_][a-zA-Z0-9_]*(?:\.[a-zA-Z_][a-zA-Z0-9_]*)*)'
            undefined_imports = re.findall(undefined_pattern, stderr_output)
            imports.extend(undefined_imports)
        
        return list(set(imports))
    
    def generate_content_hash(self, content: str) -> str:
        """Generate SHA-256 hash of policy content"""
        return hashlib.sha256(content.encode('utf-8')).hexdigest()
    
    def create_missing_module_stub(self, module_path: str) -> str:
        """Create a stub for missing OPA module"""
        module_parts = module_path.split('.')
        package_name = '.'.join(module_parts)
        
        stub_content = f"""
# Auto-generated stub for missing module: {module_path}
package {package_name}

# Default empty data structure
default data = {{}}

# Placeholder rules - replace with actual implementation
default allow = false
default deny = false
"""
        return stub_content.strip()
