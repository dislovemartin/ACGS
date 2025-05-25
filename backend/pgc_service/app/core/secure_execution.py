from ..schemas import PETContextInput, PETContextOutput, TEEContextInput, TEEContextOutput
from typing import Dict, Any

# --- Mock PETs Integration ---

async def apply_pet_transformation(input_data: PETContextInput) -> PETContextOutput:
    """
    Mocks applying a Privacy Enhancing Technology transformation.
    """
    print(f"Mock PET: Applying transformation '{input_data.transformation}' to data: {str(input_data.data)[:100]}...")
    
    processed_data: Any = None
    status = "success"

    if input_data.transformation == "homomorphic_encryption":
        # Simulate encrypting the data (e.g., replacing values with "[encrypted_value]")
        processed_data = {key: f"[encrypted_{value}]" for key, value in input_data.data.items()}
    elif input_data.transformation == "differential_privacy":
        # Simulate adding noise or generalizing data
        processed_data = {key: f"[dp_protected_{value}]" for key, value in input_data.data.items()}
        # Add some mock noise if data is numeric
        for key, value in input_data.data.items():
            if isinstance(value, (int, float)):
                # processed_data[key] = value + random.uniform(-0.1*value, 0.1*value) # Requires import random
                processed_data[key] = f"[dp_numeric_{value}_plus_noise]"
    elif input_data.transformation == "data_masking":
        processed_data = {key: f"***MASKED***" if isinstance(value, str) and len(value)>3 else value for key, value in input_data.data.items()}

    else:
        status = "error"
        processed_data = {"error": f"Unknown PET transformation: {input_data.transformation}"}

    print(f"Mock PET: Output data: {str(processed_data)[:100]}...")
    return PETContextOutput(processed_data=processed_data, status=status)

# --- Mock TEEs Integration ---

async def execute_in_mock_tee(input_context: TEEContextInput) -> TEEContextOutput:
    """
    Mocks executing code within a Trusted Execution Environment.
    """
    print(f"Mock TEE: Preparing to execute code for data: {str(input_context.data)[:100]}...")
    print(f"Mock TEE: Code to execute (reference): {input_context.code_to_execute}")

    # Simulate execution based on the 'code_to_execute' reference
    result: Any = None
    status = "success"
    mock_attestation = "mock_tee_attestation_report_for_" + input_context.code_to_execute

    if input_context.code_to_execute == "sensitive_data_aggregation":
        # Example: Aggregate some numeric values from the input data
        try:
            total_sum = sum(v for v in input_context.data.values() if isinstance(v, (int, float)))
            result = {"aggregated_sum": total_sum}
        except Exception as e:
            result = {"error": f"Failed aggregation: {str(e)}"}
            status = "error"
            mock_attestation = None # No attestation on error

    elif input_context.code_to_execute == "policy_check_module":
        # Example: A mock policy check that always permits if 'role' is 'admin'
        user_role = input_context.data.get("user_role")
        if user_role == "admin":
            result = {"decision": "permit", "reason": "User is admin (TEE check)"}
        else:
            result = {"decision": "deny", "reason": "User is not admin (TEE check)"}
    else:
        result = {"error": f"Unknown code reference for TEE: {input_context.code_to_execute}"}
        status = "error"
        mock_attestation = None

    print(f"Mock TEE: Execution result: {result}")
    return TEEContextOutput(result=result, attestation_report=mock_attestation, status=status)


# Example Usage
if __name__ == "__main__":
    import asyncio

    async def test_secure_execution_mocks():
        print("--- Testing PET Mock ---")
        pet_in1 = PETContextInput(data={"user_id": "u123", "query": "SELECT * FROM table"}, transformation="homomorphic_encryption")
        pet_out1 = await apply_pet_transformation(pet_in1)
        print(f"PET Output 1: {pet_out1.model_dump_json(indent=2)}\n")

        pet_in2 = PETContextInput(data={"age": 30, "salary": 50000}, transformation="differential_privacy")
        pet_out2 = await apply_pet_transformation(pet_in2)
        print(f"PET Output 2: {pet_out2.model_dump_json(indent=2)}\n")
        
        pet_in3 = PETContextInput(data={"name": "Alice Wonderland", "address": "123 Main St"}, transformation="data_masking")
        pet_out3 = await apply_pet_transformation(pet_in3)
        print(f"PET Output 3: {pet_out3.model_dump_json(indent=2)}\n")

        print("--- Testing TEE Mock ---")
        tee_in1 = TEEContextInput(data={"value1": 10, "value2": 20, "value3": "abc"}, code_to_execute="sensitive_data_aggregation")
        tee_out1 = await execute_in_mock_tee(tee_in1)
        print(f"TEE Output 1: {tee_out1.model_dump_json(indent=2)}\n")

        tee_in2 = TEEContextInput(data={"user_role": "editor", "resource_id": "doc789"}, code_to_execute="policy_check_module")
        tee_out2 = await execute_in_mock_tee(tee_in2)
        print(f"TEE Output 2: {tee_out2.model_dump_json(indent=2)}\n")
        
        tee_in3 = TEEContextInput(data={"user_role": "admin", "resource_id": "doc789"}, code_to_execute="policy_check_module")
        tee_out3 = await execute_in_mock_tee(tee_in3)
        print(f"TEE Output 3: {tee_out3.model_dump_json(indent=2)}\n")


    asyncio.run(test_secure_execution_mocks())
