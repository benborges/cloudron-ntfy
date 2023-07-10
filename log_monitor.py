import os
import requests
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

class LogFileHandler(FileSystemEventHandler):
    def on_modified(self, event):
        if not event.is_directory and event.src_path.endswith('.log'):
            log_file = event.src_path
            with open(log_file, 'r') as file:
                content = file.read()
                if any(keyword in content for keyword in KEYWORDS):
                    send_webhook(content)


def monitor_logs():
    event_handler = LogFileHandler()
    observer = Observer()
    for log_directory in LOG_DIRECTORIES:
        observer.schedule(event_handler, path=log_directory, recursive=False)
    observer.start()
    try:
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
        print('Webhook sent successfully.')
    else:
        print('Failed to send webhook.')


if __name__ == '__main__':
    monitor_logs()
