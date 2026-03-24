#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
ContinuousSourcing Main Entry Point
智能数据采集与质量评估系统 - 主程序
"""

import os
import sys
import time
import signal
from datetime import datetime
from multiprocessing import Process
import redis

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config import (
    REDIS_HOST, REDIS_PORT, REDIS_DB,
    TASK_NAME, CRAWLER_WORKER_RESTART_INTERVAL
)

crawler_process = None
running = True

def signal_handler(sig, frame):
    global running
    print("收到退出信号，正在关闭...")
    running = False
    if crawler_process:
        crawler_process.terminate()
    sys.exit(0)

def init_redis():
    return redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)

def start_worker_process(worker_name, queue_name):
    print(f"启动 Worker: {worker_name} -> 队列: {queue_name}")
    try:
        worker_module = __import__(f'workers.{worker_name}', fromlist=[''])
        worker_module.run(queue_name)
    except Exception as e:
        print(f"Worker {worker_name} 启动失败: {e}")

def run_crawler():
    global crawler_process
    
    print(f"=== ContinuousSourcing Crawler 启动 ===")
    print(f"任务名称: {TASK_NAME}")
    print(f"启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    redis_client = init_redis()
    redis_client.set('crawler_status', 'running')
    redis_client.set('crawler_start_time', datetime.now().isoformat())
    
    workers = [
        ('priority_judge', 'priority_judge'),
        ('get_categories', 'get_categories'),
        ('data_volume', 'data_volume'),
        ('quality_judgment', 'quality_judgment'),
        ('get_picture', 'get_picture'),
        ('get_screenshot', 'get_screenshot'),
        ('get_website_info', 'get_website_info'),
    ]
    
    worker_processes = []
    for worker_name, queue_name in workers:
        try:
            p = Process(target=start_worker_process, args=(worker_name, queue_name))
            p.daemon = True
            p.start()
            worker_processes.append(p)
            print(f"Worker {worker_name} 已启动 (PID: {p.pid})")
        except Exception as e:
            print(f"启动 Worker {worker_name} 失败: {e}")
    
    restart_counter = 0
    while running:
        try:
            time.sleep(60)
            redis_client.set('crawler_last_heartbeat', datetime.now().isoformat())
            alive_count = sum(1 for p in worker_processes if p.is_alive())
            redis_client.set('crawler_active_workers', alive_count)
            
            restart_counter += 1
            if restart_counter >= (CRAWLER_WORKER_RESTART_INTERVAL // 60):
                print("执行定期重启...")
                for p in worker_processes:
                    if p.is_alive():
                        p.terminate()
                
                worker_processes = []
                for worker_name, queue_name in workers:
                    try:
                        p = Process(target=start_worker_process, args=(worker_name, queue_name))
                        p.daemon = True
                        p.start()
                        worker_processes.append(p)
                    except Exception as e:
                        print(f"重启 Worker {worker_name} 失败: {e}")
                
                restart_counter = 0
                
        except KeyboardInterrupt:
            print("收到中断信号")
            break
        except Exception as e:
            print(f"主循环异常: {e}")
            time.sleep(5)
    
    print("正在停止 Workers...")
    for p in worker_processes:
        if p.is_alive():
            p.terminate()
    
    redis_client.set('crawler_status', 'stopped')
    print("=== ContinuousSourcing Crawler 已停止 ===")

if __name__ == '__main__':
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    run_crawler()
