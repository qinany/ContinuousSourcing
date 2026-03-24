#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Worker for processing tasks
"""
import time
import json
import redis
from config import REDIS_HOST, REDIS_PORT, REDIS_DB

def run(queue_name):
    """Run the worker"""
    print(f"Worker started for queue: {queue_name}")
    r = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
    
    while True:
        try:
            task = r.lpop(f'queue:{queue_name}')
            if task:
                task_data = json.loads(task)
                print(f"Processing task: {task_data.get('url', 'unknown')}")
                result = {'status': 'completed', 'url': task_data.get('url')}
                r.set(f'result:{queue_name}:{task_data.get("url")}', json.dumps(result))
            else:
                time.sleep(1)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

if __name__ == '__main__':
    import sys
    queue = sys.argv[1] if len(sys.argv) > 1 else 'default'
    run(queue)
