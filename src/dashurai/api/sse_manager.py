import json
import logging
import queue
import threading
import time
from typing import Set, Dict, Any

logger = logging.getLogger(__name__)

class SSEManager:
    def __init__(self):
        # Initialize the SSE manager with an empty client set.
        self._clients: Set[queue.Queue] = set()
        self._lock = threading.Lock()
        logger.info("SSE Manager initialized")
    
    def add_client(self, client_queue: queue.Queue) -> None:
        with self._lock:
            self._clients.add(client_queue)
            logger.info(f"Client added. Total clients: {len(self._clients)}")
    
    def remove_client(self, client_queue: queue.Queue) -> None:
        with self._lock:
            if client_queue in self._clients:
                self._clients.remove(client_queue)
                logger.info(f"Client removed. Total clients: {len(self._clients)}")
    
    def broadcast(self, data: Dict[str, Any]) -> None:

        if not data:
            return
        
        # Format data according to SSE specification
        message = f"data: {json.dumps(data)}\n\n"
        
        with self._lock:
            # Create a copy of clients to avoid modification during iteration
            clients_copy = self._clients.copy()
            disconnected_clients = []
            
            for client_queue in clients_copy:
                try:
                    # Put message in client queue with timeout to prevent blocking
                    client_queue.put(message, block=False)
                except queue.Full:
                    logger.warning("Client queue full, marking as disconnected")
                    disconnected_clients.append(client_queue)
                except Exception as e:
                    logger.error(f"Error broadcasting to client: {e}")
                    disconnected_clients.append(client_queue)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self._clients.discard(client)
    
    def get_client_count(self) -> int:
        with self._lock:
            return len(self._clients)
    
    def send_heartbeat(self) -> None:
        heartbeat_message = ": heartbeat\n\n"
        
        with self._lock:
            clients_copy = self._clients.copy()
            disconnected_clients = []
            
            for client_queue in clients_copy:
                try:
                    client_queue.put(heartbeat_message, block=False)
                except (queue.Full, Exception) as e:
                    logger.debug(f"Failed to send heartbeat to client: {e}")
                    disconnected_clients.append(client_queue)
            
            # Remove disconnected clients
            for client in disconnected_clients:
                self._clients.discard(client)


# Create the singleton instance at module level
sse_manager = SSEManager()


def get_sse_manager() -> SSEManager:
    return sse_manager


def broadcast_activity(activity_data: Dict[str, Any]) -> None:
    sse_manager.broadcast(activity_data)

def send_heartbeat_to_all() -> None:
    sse_manager.send_heartbeat()
