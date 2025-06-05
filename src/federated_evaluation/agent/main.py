import grpc
from concurrent import futures
import time
import logging
import sys
import os
import uuid

import docker

# Add the proto directory to the path to ensure generated files are found
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'proto'))
import evaluation_pb2
import evaluation_pb2_grpc

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class NodeAgentService(evaluation_pb2_grpc.NodeAgentServiceServicer):
    """
    Implements the NodeAgentService for the federated evaluation agent.
    """
    def DispatchTest(self, request, context):
        """
        Receives a test package from the coordinator, logs it, and returns a
        dispatch response.
        """
        logger.info(f"Received test package: {request}")
        
        task_id = str(uuid.uuid4())
        
        try:
            client = docker.from_env()
            
            # Pull the latest alpine image
            logger.info("Pulling alpine:latest image...")
            client.images.pull('alpine', 'latest')
            
            # Run a simple command in the container
            command = 'echo "Test execution successful"'
            logger.info(f"Running command in container: {command}")
            container = client.containers.run('alpine:latest', command, detach=False)
            
            # Decode the output from bytes to string
            output = container.decode('utf-8').strip()
            logger.info(f"Container output: {output}")
            
            return evaluation_pb2.DispatchResponse(
                task_id=task_id,
                status=output
            )
        except docker.errors.DockerException as e:
            logger.error(f"An error occurred with Docker: {e}")
            return evaluation_pb2.DispatchResponse(
                task_id=task_id,
                status=f"Docker error: {e}"
            )
        except Exception as e:
            logger.error(f"An unexpected error occurred: {e}")
            return evaluation_pb2.DispatchResponse(
                task_id=task_id,
                status=f"Unexpected error: {e}"
            )

def serve():
    """
    Starts the gRPC server and waits for requests.
    """
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    evaluation_pb2_grpc.add_NodeAgentServiceServicer_to_server(NodeAgentService(), server)
    server.add_insecure_port('[::]:50051')
    server.start()
    logger.info("Node Agent gRPC server started on port 50051.")
    try:
        while True:
            time.sleep(86400)  # One day
    except KeyboardInterrupt:
        server.stop(0)
        logger.info("Node Agent gRPC server stopped.")

if __name__ == '__main__':
    serve()