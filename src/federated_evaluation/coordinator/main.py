import uuid
import sys
import os
import grpc
from fastapi import FastAPI, Body
import logging

# Add the proto directory to the path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))
import evaluation_pb2
import evaluation_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

def dispatch_test_package(test_package_dict: dict):
    """
    Dispatches a test package to a node agent via gRPC.
    """
    logger.info(f"Dispatching test package: {test_package_dict}")
    try:
        with grpc.insecure_channel('localhost:50051') as channel:
            stub = evaluation_pb2_grpc.NodeAgentServiceStub(channel)
            
            test_package = evaluation_pb2.TestPackage(
                test_id=test_package_dict.get("test_id", ""),
                test_content=test_package_dict.get("test_content", "")
            )
            
            response = stub.DispatchTest(test_package)
            logger.info(f"Received response from agent: {response}")
            return response
    except grpc.RpcError as e:
        logger.error(f"Could not connect to node agent: {e}")
        return None


@app.post("/tests")
async def receive_test(payload: dict = Body(...)):
    """
    Receives a test package, logs it, dispatches it to an agent,
    and returns a confirmation.
    """
    task_id = str(uuid.uuid4())
    logger.info(f"Received test payload: {payload}")

    # Dispatch the test package to the node agent
    dispatch_response = dispatch_test_package(payload)

    if dispatch_response:
        return {"status": "test dispatched", "task_id": task_id, "agent_response": {
            "task_id": dispatch_response.task_id,
            "status": dispatch_response.status
        }}
    else:
        return {"status": "failed to dispatch test", "task_id": task_id}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)