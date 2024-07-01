import os

import pika
import threading
from concurrent.futures import ThreadPoolExecutor
import time
import json
from loguru import logger
from pika.exceptions import ConnectionClosedByBroker, AMQPConnectionError, AMQPChannelError


class RabbitMQHelper:
    def __init__(self,
                 queue_name,
                 host='localhost',
                 port=5672,
                 username='guest',
                 password='guest',
                 virtual_host='/',
                 exchange='',
                 exchange_type='direct',
                 routing_key=None,
                 prefetch_count=1):
        self.retries = 3
        self.queue_name = queue_name
        self.exchange = exchange
        self.exchange_type = exchange_type
        self.routing_key = routing_key or queue_name
        self.prefetch_count = prefetch_count

        self.credentials = pika.PlainCredentials(username, password)
        self.parameters = pika.ConnectionParameters(
            host,
            port=port,
            virtual_host=virtual_host,
            credentials=self.credentials)
        self.channel = None
        self.connection = None
        self.connect()

    def connect(self, retry=3):
        try:
            if retry > 0:
                self.connection = pika.BlockingConnection(self.parameters)
                self.channel = self.connection.channel()
                if self.exchange:
                    self.channel.exchange_declare(exchange=self.exchange, exchange_type=self.exchange_type,
                                                  durable=True)
                self.channel.queue_declare(queue=self.queue_name, durable=True)
                if self.exchange:
                    self.channel.queue_bind(exchange=self.exchange, queue=self.queue_name, routing_key=self.routing_key)
        except pika.exceptions.ProbableAuthenticationError as err:
            logger.error(f"Failed to connect to RabbitMQ: {err}, retrying...")
            time.sleep(3)
            self.connect(retry - 1)
        except Exception as e:
            logger.error(f"Failed to connect to RabbitMQ: {e}")
            raise

    def send_task(self, task, retries=3):
        try:
            task_body = json.dumps(task).encode('utf-8')
            self.channel.basic_publish(
                exchange=self.exchange,
                routing_key=self.routing_key,
                body=task_body,
                properties=pika.BasicProperties(
                    delivery_mode=2,  # make message persistent
                ))
            logger.info(f"Sent task: {task}")
        except Exception as e:
            if retries > 0:
                logger.error(f"Failed to send task: {task}, error: {e}, retrying {retries} more times")
                time.sleep(3)  # Wait before retrying
                self.connect()  # Attempt to reconnect
                self.send_task(task, retries - 1)
            else:
                logger.error(f"Failed to send task after retries: {task}, error: {e}")

    def receive_task(self, callback, retries=3):
        def on_message(channel, method, properties, body):
            try:
                task = json.loads(body.decode('utf-8'))
                callback(task)
                channel.basic_ack(delivery_tag=method.delivery_tag)
            except Exception as e:
                logger.error(f"Failed to process task: {body}, error: {e}")
                if retries > 0:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=True)  # Requeue message for retry
                else:
                    channel.basic_nack(delivery_tag=method.delivery_tag, requeue=False)  # Discard message

        while True:
            try:
                self.channel.basic_qos(prefetch_count=self.prefetch_count)
                self.channel.basic_consume(queue=self.queue_name, on_message_callback=on_message)
                logger.info(f"Waiting for messages in {self.queue_name}...")
                self.channel.start_consuming()
            except (ConnectionClosedByBroker, AMQPConnectionError, AMQPChannelError) as e:
                logger.error(f"Error in consuming messages: {e}")
                self.connect()
            except Exception as e:
                logger.error(f"Unexpected error: {e}")
                self.connect()

    def stop_consuming(self):
        if self.channel and self.channel.is_open:
            self.channel.stop_consuming()
        else:
            logger.warning("Channel is already closed or not open")

    def close(self):
        try:
            self.stop_consuming()
            if self.connection and self.connection.is_open:
                self.connection.close()
            else:
                logger.warning("Connection is already closed or not open")
        except Exception as e:
            logger.error(f"Error closing connection: {e}")

    def consume_tasks(self, rabbitmq_helper, executor, task_callback):

        def on_task_received(task, retry_count=self.retries):
            try:
                if not executor._shutdown:
                    future = executor.submit(task_callback, task)
                    future.add_done_callback(
                        lambda f: handle_task_result(f, task)
                    )
                else:
                    logger.error(f"Failed to process task: {task}, executor has been shut down")
            except Exception as e:
                logger.error(f"Exception occurred in task: {task}, error: {e}")
                if retry_count > 0:
                    logger.info(f"Retrying task: {task}")
                    rabbitmq_helper.send_task(task, retries=self.retries)
                else:
                    logger.error(f"Exhausted retries for task: {task}")

        def handle_task_result(future, task):
            if future.exception():
                logger.error(f"Task failed: {task}, exception: {future.exception()}")
                if self.retries > 0:
                    logger.info(f"Retrying task: {task}, retries left: {self.retries}")
                    rabbitmq_helper.send_task(task, retries=self.retries)
                    self.retries -= 1
                else:
                    logger.error(f"Exhausted retries for task: {task}")
            else:
                logger.info(f"Task completed successfully: {task}")

        rabbitmq_helper.receive_task(on_task_received)


def run_spider(queue_name,
               tasks,
               spider,
               host='localhost',
               username='guest',
               password='guest',
               max_workers=min(32, (os.cpu_count() or 1) + 4),
               timeout=20):
    """

    Args:
        queue_name: 队列名称
        tasks: 任务信息
        spider: 爬虫函数
        host: 主机
        username: 用户名
        password: 密码
        max_workers: 线程数
        timeout: 预计时间

    Returns:

    """
    rabbitmq_helper = RabbitMQHelper(queue_name, host=host, username=username, password=password)
    # Create ThreadPoolExecutor
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        stop_event = threading.Event()
        # Start a thread to handle message reception and submit tasks to the thread pool
        consumer_thread = threading.Thread(target=rabbitmq_helper.consume_tasks,
                                           args=(rabbitmq_helper, executor, spider))
        consumer_thread.start()
        for task in tasks:
            rabbitmq_helper.send_task(task)

        consumer_thread.join(timeout=timeout)
        executor.shutdown(wait=True)
        stop_event.set()
        rabbitmq_helper.close()
    exit()


def spider(task):
    try:
        logger.info(f"Processing task: {task}")
        time.sleep(2)  # 模拟爬取任务耗时
        logger.info(f"Finished task: {task}")
    except Exception as e:
        logger.error(f"Error processing task: {task}, error: {e}")
        raise  # 重新抛出异常以便进行回滚重试


if __name__ == "__main__":
    queue_name = 'task_queue'
    tasks = [{"url": f"http://example.com/{i}"} for i in range(10)]
    run_spider(queue_name, tasks, spider, timeout=20)
