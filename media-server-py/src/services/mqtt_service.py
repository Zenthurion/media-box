import asyncio
from typing import Dict, Callable, List, Optional, Any
import json
from aiomqtt import Client, MqttError
from config.config import config

class MQTTService:
    def __init__(self):
        self._client: Optional[Client] = None
        self._event_handlers: Dict[str, List[Callable]] = {
            'url': []
        }
        self._running = False
        self._topic_handlers = {}
        
    def on(self, event: str, callback: Callable[[str], Any]) -> None:
        """Register an event handler"""
        if event in self._event_handlers:
            self._event_handlers[event].append(callback)
    
    async def _emit(self, event: str, *args) -> None:
        """Emit an event to all registered handlers"""
        print(f"Emitting event: {event}")
        if event in self._event_handlers:
            print(f"Event handlers for {event}: {self._event_handlers[event]}")
            for handler in self._event_handlers[event]:
                print(f"Calling handler: {handler}")
                if asyncio.iscoroutinefunction(handler):
                    print(f"Handler is a coroutine, awaiting it...")
                    await handler(*args)
                else:
                    print(f"Handler is not a coroutine, calling it directly...")
                    handler(*args)

    async def start(self) -> None:
        """Start the MQTT service"""
        try:
            print("Attempting to start MQTT client...")
            self._client = Client(
                hostname=config.mqtt.host,
                port=config.mqtt.port,
                keepalive=60  # Add keepalive to prevent connection drops
            )
            
            self._running = True
            print(f"Creating message loop task for {config.mqtt.host}:{config.mqtt.port}")
            asyncio.create_task(self._message_loop())
            
            print(f"MQTT client started and listening on port {config.mqtt.port}")
            
        except Exception as error:
            print(f"Failed to start MQTT client: {str(error)}")
            print(f"Error type: {type(error)}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            raise

    async def _message_loop(self) -> None:
        """Handle incoming MQTT messages"""
        while self._running:  # Add outer loop for reconnection attempts
            try:
                print("Attempting to establish MQTT connection...")
                async with self._client as client:
                    # Set up topic handlers
                    self._topic_handlers = {
                        config.mqtt.url_topic: self._handle_url_message
                    }
                    
                    # Subscribe to topics
                    for topic in self._topic_handlers.keys():
                        print(f"Subscribing to topic: {topic}")
                        await client.subscribe(topic)
                        print(f"Successfully subscribed to {topic}")
                    
                    print("Starting message loop...")
                    while self._running:
                        async for message in client.messages:
                            print(f"Raw message received: Topic={message.topic}, Payload={message.payload}")
                            await self._handle_message(message)

            except MqttError as error:
                print(f"MQTT Error: {str(error)}")
                print(f"Error type: {type(error)}")
                if self._running:
                    print("Attempting to reconnect in 5 seconds...")
                    await asyncio.sleep(5)  # Wait before retry
                    continue
            except Exception as error:
                print(f"Unexpected error in message loop: {str(error)}")
                print(f"Error type: {type(error)}")
                import traceback
                print(f"Traceback: {traceback.format_exc()}")
                if self._running:
                    print("Attempting to reconnect in 5 seconds...")
                    await asyncio.sleep(5)
                    continue

    async def _handle_message(self, message) -> None:
        """Process incoming MQTT message"""
        try:
            topic = message.topic.value
            payload = message.payload.decode()
            
            print(f"Received message on topic {topic}")
            
            # Dispatch to appropriate handler
            if topic in self._topic_handlers:
                await self._topic_handlers[topic](payload)
            else:
                print(f"No handler for topic: {topic}")
                
        except Exception as error:
            print(f"Error processing published message: {error}")

    async def _handle_url_message(self, payload: str) -> None:
        """Handle URL messages"""
        print(f"Processing URL: {payload}")
        await self._emit('url', payload)

    async def stop(self) -> None:
        """Stop the MQTT service"""
        try:
            self._running = False
            self._client = None
            print("MQTT client stopped")
        except Exception as error:
            print(f"Error stopping MQTT client: {error}")
            raise

    async def __aenter__(self):
        """Support for async context manager"""
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Support for async context manager"""
        await self.stop() 