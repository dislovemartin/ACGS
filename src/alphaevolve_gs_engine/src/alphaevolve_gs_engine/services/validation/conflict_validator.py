"""
conflict_validator.py

This module defines the ConflictValidator, responsible for identifying
conflicts between different policies or rules within the governance system.
Conflicts can arise between operational rules, between constitutional principles,
or between operational rules and constitutional principles.

Classes:
    ConflictDefinition: Describes a type of conflict to detect.
    ConflictValidator: Interface for conflict validation.
    OPAConflictDetector: Uses OPA's capabilities (e.g., `opa eval` with specific
                         queries, or `opa test`) to find conflicts.
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Tuple, Optional
import subprocess
import json
import os
import tempfile

from alphaevolve_gs_engine.utils.logging_utils import setup_logger
# from alphaevolve_gs_engine.core.constitutional_principle import ConstitutionalPrinciple
# from alphaevolve_gs_engine.core.operational_rule import OperationalRule

logger = setup_logger(__name__)

class ConflictDefinition:
    """
    Describes a specific type of conflict to detect between policies.

    Attributes:
        conflict_id (str): Unique identifier for the conflict type.
        name (str): Human-readable name (e.g., "Permit-Deny Conflict", "Subsumption").
        description (str): Explanation of the conflict type.
        detection_query (str): A query (e.g., Rego) used to detect this conflict.
                               This query typically takes multiple policies/rules as input
                               or operates on a combined set.
        severity (str): Potential impact of such a conflict (e.g., "high", "medium").
    """
    def __init__(self,
                 conflict_id: str,
                 name: str,
                 description: str,
                 detection_query: str, # This would be a Rego query or similar
                 severity: str = "medium"):
        self.conflict_id = conflict_id
        self.name = name
        self.description = description
        self.detection_query = detection_query # e.g., "data.conflict_checks.permit_deny_conflict"
        self.severity = severity

    def __repr__(self) -> str:
        return (f"ConflictDefinition(id='{self.conflict_id}', name='{self.name}', "
                f"severity='{self.severity}')")


class ConflictValidator(ABC):
    """
    Abstract base class for conflict validation services.
    """

    @abstractmethod
    def find_conflicts(self,
                       policies_to_check: List[Dict[str, str]], # e.g., [{"id": "P1", "code": "rego code P1"}, ...]
                       conflict_definitions: List[ConflictDefinition],
                       # Optional: context or specific input for which conflicts are checked
                       input_scenario: Optional[Dict[str, Any]] = None
                      ) -> List[Dict[str, Any]]: # List of found conflicts
        """
        Identifies conflicts among a set of policies based on conflict definitions.

        Args:
            policies_to_check (List[Dict[str, str]]): A list of policies, each with 'id' and 'code'.
            conflict_definitions (List[ConflictDefinition]): Definitions of conflicts to check for.
            input_scenario (Optional[Dict[str, Any]]): An optional input context. Some conflicts
                                                       are input-dependent.

        Returns:
            List[Dict[str, Any]]: A list of detected conflicts. Each dict could include:
                - "conflict_id": ID of the ConflictDefinition that was triggered.
                - "conflicting_policies": List of IDs of policies involved.
                - "details": Specifics of the conflict (e.g., problematic input).
                - "severity": Severity of the conflict.
        """
        pass


class OPAConflictDetector(ConflictValidator):
    """
    Detects conflicts by evaluating a combined set of policies and specific
    conflict detection queries using the OPA engine.
    """
    def __init__(self, opa_executable_path: str = "opa", conflict_check_rego_files: Optional[List[str]] = None):
        """
        Initializes the OPAConflictDetector.

        Args:
            opa_executable_path (str): Path to the OPA executable.
            conflict_check_rego_files (Optional[List[str]]):
                Paths to .rego files containing the logic for conflict detection queries
                (e.g., implementations of `data.conflict_checks.permit_deny_conflict`).
                These are loaded by OPA along with the policies being checked.
        """
        self.opa_executable_path = opa_executable_path
        self.conflict_check_rego_files = conflict_check_rego_files if conflict_check_rego_files else []
        self._check_opa_availability()

    def _check_opa_availability(self):
        try:
            subprocess.run([self.opa_executable_path, "version"], capture_output=True, text=True, check=True, timeout=5)
            logger.info(f"OPA executable found at '{self.opa_executable_path}'.")
        except (FileNotFoundError, subprocess.CalledProcessError, subprocess.TimeoutExpired) as e:
            logger.error(f"OPA executable not found or not working at '{self.opa_executable_path}'. "
                         f"Conflict detection will be impacted. Error: {e}")


    def _run_opa_eval_for_conflicts(self,
                                    temp_policy_files: List[str],
                                    conflict_query: str,
                                    input_scenario_file: Optional[str]
                                   ) -> Tuple[Optional[List[Any]], str]:
        """
        Runs `opa eval` with a set of policy files and a conflict query.
        """
        cmd = [
            self.opa_executable_path, "eval",
            "--format", "json",
            # Include all policies being checked
        ]
        for f_path in temp_policy_files:
            cmd.extend(["--data", f_path])
        
        # Include common conflict check logic files if provided
        for rego_lib_file in self.conflict_check_rego_files:
            if os.path.exists(rego_lib_file):
                cmd.extend(["--data", rego_lib_file])
            else:
                logger.warning(f"Conflict check Rego library file not found: {rego_lib_file}")

        if input_scenario_file:
            cmd.extend(["--input", input_scenario_file])
        
        cmd.append(conflict_query) # The specific query for a conflict type

        logger.debug(f"Executing OPA eval for conflict query '{conflict_query}': {' '.join(cmd)}")
        try:
            result = subprocess.run(cmd, capture_output=True, text=True, check=False, timeout=20)
            if result.returncode != 0:
                error_msg = f"OPA conflict evaluation failed for query '{conflict_query}'. Error: {result.stderr.strip()}"
                logger.error(error_msg)
                return None, error_msg

            try:
                opa_output = json.loads(result.stdout)
                # Expected output for conflict queries is often a list of conflict instances.
                # e.g., `[{"result": [{"conflict_type": "X", "policies": ["P1", "P2"]}]}]`
                # If `opa_output` is `[]`, query was undefined or no results.
                # If `opa_output` is `[{"result": []}]`, query ran but found no conflicts.
                if opa_output and isinstance(opa_output, list) and \
                   "result" in opa_output[0] and isinstance(opa_output[0]["result"], list):
                    detected_conflicts = opa_output[0]["result"]
                    logger.debug(f"OPA conflict query '{conflict_query}' successful. Found {len(detected_conflicts)} potential conflicts.")
                    return detected_conflicts, ""
                elif opa_output and isinstance(opa_output, list) and not opa_output[0].get("result"):
                    # Query was undefined or something unexpected, result is not in the expected list format
                    logger.warning(f"Conflict query '{conflict_query}' output was not in expected format (e.g. empty or no 'result' list): {result.stdout[:300]}")
                    return [], "" # No conflicts found / query undefined
                else: # Query ran, no conflicts found (e.g. result was empty list `[]`)
                    logger.debug(f"OPA conflict query '{conflict_query}' successful. No conflicts found. Output: {result.stdout[:300]}")
                    return [], ""


            except (json.JSONDecodeError, IndexError, KeyError) as e:
                error_msg = f"Failed to parse OPA output for conflict query '{conflict_query}'. Error: {e}. Output: {result.stdout[:500]}"
                logger.error(error_msg)
                return None, error_msg

        except FileNotFoundError:
            err = f"OPA executable not found at '{self.opa_executable_path}'."
            logger.error(err)
            return None, err
        except subprocess.TimeoutExpired:
            err = f"OPA conflict evaluation timed out for query '{conflict_query}'."
            logger.error(err)
            return None, err
        except Exception as e:
            err = f"An unexpected error occurred during OPA conflict evaluation: {e}"
            logger.error(err, exc_info=True)
            return None, err
        
        return [], "" # Default empty list if something unexpected happened but not an outright error

    def find_conflicts(self,
                       policies_to_check: List[Dict[str, str]],
                       conflict_definitions: List[ConflictDefinition],
                       input_scenario: Optional[Dict[str, Any]] = None
                      ) -> List[Dict[str, Any]]:
        
        all_detected_conflicts: List[Dict[str, Any]] = []
        temp_file_paths: List[str] = []
        input_scenario_file_path: Optional[str] = None

        try:
            # Create temporary files for each policy to check
            for i, policy_item in enumerate(policies_to_check):
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix=f"_policy_{i}_{policy_item['id']}.rego") as tmp_file:
                    tmp_file.write(policy_item["code"])
                    temp_file_paths.append(tmp_file.name)
            
            # Create a temporary file for the input scenario if provided
            if input_scenario:
                with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_conflict_input.json") as tmp_input_file:
                    json.dump(input_scenario, tmp_input_file)
                    input_scenario_file_path = tmp_input_file.name

            # Iterate through each conflict definition and run its detection query
            for conflict_def in conflict_definitions:
                logger.info(f"Checking for conflict type: '{conflict_def.name}' (ID: {conflict_def.conflict_id}) "
                            f"using query: {conflict_def.detection_query}")
                
                # detected_for_this_type is expected to be a list of dicts,
                # where each dict describes one instance of the conflict.
                detected_for_this_type, error_msg = self._run_opa_eval_for_conflicts(
                    temp_file_paths,
                    conflict_def.detection_query,
                    input_scenario_file_path
                )

                if error_msg:
                    logger.error(f"Error while checking for conflict '{conflict_def.name}': {error_msg}")
                    # Optionally, add this error to a list of processing errors
                    all_detected_conflicts.append({
                        "conflict_id": conflict_def.conflict_id,
                        "name": conflict_def.name,
                        "error": error_msg,
                        "severity": conflict_def.severity,
                        "conflicting_policies": []
                    })
                    continue # Skip to next conflict type if OPA failed for this one

                if detected_for_this_type:
                    for conflict_instance in detected_for_this_type:
                        # Standardize the conflict instance structure
                        # The `conflict_instance` from OPA should ideally already contain details
                        # like which specific policies are involved, under what conditions, etc.
                        # We add the definition's metadata here.
                        instance_details = {
                            "conflict_definition_id": conflict_def.conflict_id,
                            "conflict_name": conflict_def.name,
                            "severity": conflict_def.severity,
                            "details": conflict_instance # This is the payload from the OPA query
                        }
                        # Ensure 'conflicting_policies' is present, even if empty
                        if "conflicting_policies" not in instance_details["details"]:
                             instance_details["details"]["conflicting_policies"] = []
                        
                        all_detected_conflicts.append(instance_details)
                        logger.warning(f"Detected conflict instance for '{conflict_def.name}': {str(conflict_instance)[:200]}")
            
        finally:
            # Clean up all temporary files
            for f_path in temp_file_paths:
                if os.path.exists(f_path):
                    os.remove(f_path)
            if input_scenario_file_path and os.path.exists(input_scenario_file_path):
                os.remove(input_scenario_file_path)
        
        return all_detected_conflicts


# Example Usage:
if __name__ == "__main__":
    # --- Example Policies ---
    policy_allow_all_http = {
        "id": "AllowAllHTTP",
        "code": """
        package company.firewall
        default http_allowed = false
        http_allowed { input.protocol == "http" }
        """
    }
    policy_deny_http_port_80 = {
        "id": "DenyPort80",
        "code": """
        package company.firewall_ext # Different package to avoid direct redefinition if loaded together
        default http_port_80_denied = false
        http_port_80_denied { input.protocol == "http"; input.port == 80 }
        """
    }
    # This policy is a bit contrived for a simple conflict example.
    # Real conflict detection rules would be more complex.

    # --- Example Conflict Definitions ---
    # This requires a Rego file that defines `data.conflict_checks.permit_deny_on_http_port_80`
    # For this example, let's assume such a Rego file exists (`conflict_rules.rego`).
    # Content of a hypothetical `conflict_rules.rego`:
    # ```rego
    # package conflict_checks
    #
    # # Detects if HTTP is allowed generally, but specifically denied on port 80 for the same input.
    # permit_deny_on_http_port_80[conflict_info] {
    #     # Check if the main firewall allows HTTP
    #     data.company.firewall.http_allowed == true
    #     # Check if the extended firewall denies HTTP on port 80
    #     data.company.firewall_ext.http_port_80_denied == true
    #     # If both are true for the *same input*, it's a conflict
    #     conflict_info := {
    #         "type": "PermitThenDenyPort80",
    #         "message": "HTTP access is generally allowed, but denied on port 80, creating a conflict for port 80 HTTP traffic.",
    #         "conflicting_rules": ["company.firewall.http_allowed", "company.firewall_ext.http_port_80_denied"],
    #         "input_trigger": input # The input that triggers this conflict
    #     }
    # }
    # ```
    # We need to create this file for the example to run.
    conflict_rules_rego_content = """
    package conflict_checks

    # Detects if HTTP is allowed generally, but specifically denied on port 80 for the same input.
    permit_deny_on_http_port_80[conflict_info] {
        data.company.firewall.http_allowed == true
        data.company.firewall_ext.http_port_80_denied == true
        
        conflict_info := {
            "type": "PermitThenDenyPort80",
            "message": "HTTP access is generally allowed, but denied on port 80, creating a conflict for port 80 HTTP traffic.",
            "conflicting_policies_involved_ids_mock": ["AllowAllHTTP", "DenyPort80"], # Mock IDs for now
            "input_trigger_details": input 
        }
    }
    """
    with tempfile.NamedTemporaryFile(mode="w", delete=False, suffix="_conflict_rules.rego") as temp_conflict_rego_file:
        temp_conflict_rego_file.write(conflict_rules_rego_content)
        temp_conflict_rego_file_name = temp_conflict_rego_file.name

    cd1 = ConflictDefinition(
        conflict_id="CD001",
        name="Permit-Deny HTTP Port 80",
        description="HTTP is allowed by one rule but denied on port 80 by another for the same input.",
        detection_query="data.conflict_checks.permit_deny_on_http_port_80", # Query defined in conflict_rules.rego
        severity="high"
    )

    policies = [policy_allow_all_http, policy_deny_http_port_80]
    conflict_defs = [cd1]
    
    # Input scenario that should trigger the conflict
    triggering_input = {"protocol": "http", "port": 80, "user": "test"}

    print("--- OPAConflictDetector Example ---")
    # Pass the path to the temporary conflict_rules.rego file
    conflict_validator = OPAConflictDetector(conflict_check_rego_files=[temp_conflict_rego_file.name])
    
    # To make this example runnable, OPA must be installed.
    # The conflict_rules.rego must be correctly written to identify the conflict.
    
    detected_conflicts_list = conflict_validator.find_conflicts(
        policies, 
        conflict_defs, 
        input_scenario=triggering_input
    )

    print(f"\nDetected Conflicts ({len(detected_conflicts_list)} found):")
    if detected_conflicts_list:
        for conflict in detected_conflicts_list:
            print(f"  Conflict Name: {conflict.get('conflict_name')}")
            print(f"  Severity: {conflict.get('severity')}")
            print(f"  Details: {str(conflict.get('details'))[:300]}...") # Print snippet of details
            if "error" in conflict:
                print(f"  Error during detection: {conflict['error']}")
    else:
        print("  No conflicts detected (or OPA issues occurred).")

    # Cleanup the temporary conflict Rego file
    if os.path.exists(temp_conflict_rego_file.name):
        os.remove(temp_conflict_rego_file.name)
    
    # Assertion (depends on OPA being functional and conflict_rules.rego being correct)
    # If OPA is working and the logic is right, one conflict should be found.
    # The actual structure of `conflict.get('details')` depends on what the Rego rule `permit_deny_on_http_port_80` returns.
    if detected_conflicts_list and "error" not in detected_conflicts_list[0]:
        assert len(detected_conflicts_list) == 1
        assert detected_conflicts_list[0]["conflict_definition_id"] == "CD001"
        # Further assertions could check details from the Rego output
        assert detected_conflicts_list[0]["details"]["type"] == "PermitThenDenyPort80"
        assert detected_conflicts_list[0]["details"]["input_trigger_details"]["port"] == 80
        print("\nOPAConflictDetector example assertions passed (if OPA is functional).")
    else:
        print("\nOPAConflictDetector example assertions skipped or failed (check OPA setup and Rego logic).")

    print("\nConflict validator example completed.")
    print("Note: Results depend on OPA installation and correctness of conflict detection Rego rules.")
