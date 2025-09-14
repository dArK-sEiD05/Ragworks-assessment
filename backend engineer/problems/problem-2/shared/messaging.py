"""
Message queue utilities for inter-service communication.
"""

import json
import asyncio
from typing import Any, Dict, Callable, Optional, List
from pika import ConnectionParameters
from pika.adapters.asyncio_connection import AsyncioConnection
from pika.exchange_type import ExchangeType
import logging

from .schemas import Event, EventType

logger = logging.getLogger(__name__)


class MessagePublisher:
    """Message publisher for sending events."""
    
    def __init__(self, rabbitmq_url: str):
        self.rabbitmq_url = rabbitmq_url
        self.connection = None
        self.channel = None
    
    async def connect(self):
        """Connect to RabbitMQ."""
        try:
            self.connection = AsyncioConnection(
                ConnectionParameters.from_url(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange='ecommerce_events',
                exchange_type=ExchangeType.topic
            )
            logger.info("Connected to RabbitMQ")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    async def publish_event(self, event: Event, routing_key: Optional[str] = None):
        """Publish an event to the message queue."""
        if not self.channel:
            await self.connect()
        
        try:
            message = json.dumps(event.model_dump(), default=str)
            routing_key = routing_key or event.event_type.value
            
            self.channel.basic_publish(
                exchange='ecommerce_events',
                routing_key=routing_key,
                body=message,
                properties={
                    'content_type': 'application/json',
                    'delivery_mode': 2,  # Make message persistent
                }
            )
            logger.info(f"Published event: {event.event_type.value}")
        except Exception as e:
            logger.error(f"Failed to publish event: {e}")
            raise
    
    async def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()


class MessageConsumer:
    """Message consumer for receiving events."""
    
    def __init__(self, rabbitmq_url: str, service_name: str):
        self.rabbitmq_url = rabbitmq_url
        self.service_name = service_name
        self.connection = None
        self.channel = None
        self.handlers: Dict[EventType, Callable] = {}
    
    async def connect(self):
        """Connect to RabbitMQ."""
        try:
            self.connection = AsyncioConnection(
                ConnectionParameters.from_url(self.rabbitmq_url)
            )
            self.channel = self.connection.channel()
            self.channel.exchange_declare(
                exchange='ecommerce_events',
                exchange_type=ExchangeType.topic
            )
            logger.info(f"Connected to RabbitMQ for {self.service_name}")
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise
    
    def register_handler(self, event_type: EventType, handler: Callable):
        """Register an event handler."""
        self.handlers[event_type] = handler
        logger.info(f"Registered handler for {event_type.value}")
    
    async def start_consuming(self, queue_patterns: List[str]):
        """Start consuming messages."""
        if not self.channel:
            await self.connect()
        
        # Create queue
        queue_name = f"{self.service_name}_queue"
        self.channel.queue_declare(queue=queue_name, durable=True)
        
        # Bind queue to exchange with patterns
        for pattern in queue_patterns:
            self.channel.queue_bind(
                exchange='ecommerce_events',
                queue=queue_name,
                routing_key=pattern
            )
        
        # Set up consumer
        self.channel.basic_consume(
            queue=queue_name,
            on_message_callback=self._handle_message,
            auto_ack=False
        )
        
        logger.info(f"Started consuming messages for {self.service_name}")
        self.channel.start_consuming()
    
    def _handle_message(self, channel, method, properties, body):
        """Handle incoming message."""
        try:
            message = json.loads(body.decode('utf-8'))
            event = Event(**message)
            
            if event.event_type in self.handlers:
                # Run the handler in the event loop
                loop = asyncio.get_event_loop()
                loop.create_task(self.handlers[event.event_type](event))
                channel.basic_ack(delivery_tag=method.delivery_tag)
                logger.info(f"Processed event: {event.event_type.value}")
            else:
                logger.warning(f"No handler for event: {event.event_type.value}")
                channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
        except Exception as e:
            logger.error(f"Failed to process message: {e}")
            channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)
    
    async def close(self):
        """Close the connection."""
        if self.connection and not self.connection.is_closed:
            self.connection.close()

