import os
import requests
import re
import datetime
import logging
from dotenv import load_dotenv
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler

# Load environment variables from .env file
load_dotenv('.env')

# Webhook URL from environment variable
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# Log directories from environment variable
LOG_DIRECTORIES = os.getenv('LOG_DIRECTORIES').split(',')

# Keywords from environment variable
KEYWORDS = os.getenv('KEYWORDS').split(',')

# Regular expression pattern to match timestamp
TIMESTAMP_PATTERN = r'\d{4}/\d{2}/\d{2} \d{2}:\d{2}:\d{2}'

# Maximum number of lines to read from each log file
MAX_LINES = int(os.getenv('MAX_LINES'))

# Time threshold for excluding logs older than a week
TIME_THRESHOLD = datetime.datetime.now() - datetime.timedelta(days=int(os.getenv('TIME_THRESHOLD')))

# Log level from environment variable
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Configure logging
logging.basicConfig(level=LOG_LEVEL)
logger = logging.getLogger(__name__)


class LogFileHandler(FileSystemEventHandler):
    def __init__(self):
        self.log_entries = {}

    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            log_file = event.src_path
            logger.info(f'Processing log file: {log_file}')
            with open(log_file, 'r') as file:
                lines = file.readlines()
                lines = lines[-MAX_LINES:]  # Read only the last MAX_LINES lines
                content = ''.join(lines)
                events = self.extract_events(content)
                logger.info(f'Found {len(events)} events in log file')
                for event_content in events:
                    if any(keyword in event_content for keyword in KEYWORDS):
                        logger.info(f'Sending webhook for event:\n{event_content}\n')
                        send_webhook(event_content)

    def extract_events(self, content):
        events = re.split(TIMESTAMP_PATTERN, content)
        events = [event.strip() for event in events if event.strip()]
        return events


def monitor_logs():
    event_handler = LogFileHandler()
    observer = Observer()
    for log_directory in LOG_DIRECTORIES:
        observer.schedule(event_handler, path=log_directory, recursive=False)
    observer.start()
    try:
        logger.info('Log monitoring started...')
        while True:
            pass
    except KeyboardInterrupt:
        observer.stop()
    observer.join()


def send_webhook(content):
    payload = {
        'log_content': content
    }
    response = requests.post(WEBHOOK_URL, json=payload)
    if response.status_code == 200:
        logger.info('Webhook sent successfully.')
    else:
        logger.error('Failed to send webhook.')


if __name__ == '__main__':
    monitor_logs()
