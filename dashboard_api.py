import os
import json
import subprocess
import time
import uuid
from datetime import datetime
from flask import Flask, jsonify, request, send_from_directory
from flask_cORS import CORS
import redis
from database.db import execute_query, get_db_connection
from config import REDIS_HOST, REDIS_PORT, REDIS_DB, FLASK_HOST, FLASK_PORT, FLASK_DEBUG, settings

app = Flask(__name__, static_folder='dashboard')
CORS(app)

redis_client = redis.Redis(host=REDIS_HOST, port=REDIS_PORT, db=REDIS_DB, decode_responses=True)
crawler_process = None

def get_crawler_pid():
    pid = redis_client.get('crawler_pid')
    return int(pid) if pid else None

def set_crawler_pid(pid):
    redis_client.set('crawler_pid', pid)

def clear_crawler_pid():
    redis_client.delete('crawler_pid')

@app.route('/health', methods=['GET'])
def health_check():
    try:
        conn = get_db_connection().__enter__()
        conn.close()
        redis_client.ping()
        return jsonify({"status": "healthy", "database": "connected", "redis": "connected", "crawler_running": get_crawler_pid() is not None})
    except Exception as e:
        return jsonify({"status": "unhealthy", "error": str(e)}), 503

@app.route('/api/stats', methods=['GET'])
def get_stats():
    try:
        _, sites = execute_query("SELECT COUNT(*) as count FROM source_sites")
        total_sites = sites[0][0] if sites else 0
        _, articles = execute_query("SELECT COUNT(*) as count FROM articles")
        total_articles = articles[0][0] if articles else 0
        
        if total_sites == 0 and total_articles == 0:
            return jsonify({"total_sites": 156, "total_articles": 2847, "sites_by_result": {"P0": 23, "P0-": 45, "P1": 67, "P2": 15, "PX": 6}, "articles_by_evaluation": {"L1": 892, "L2": 1245, "L3": 456, "L-1": 254}, "articles_24h": 156, "success_rate": 0.87, "mock": True})
        
        _, sites_by_result = execute_query("SELECT final_result, COUNT(*) as count FROM source_sites GROUP BY final_result")
        _, articles_by_eval = execute_query("SELECT evaluation_result, COUNT(*) as count FROM articles GROUP BY evaluation_result")
        
        sites_result = {str(row[0]): row[1] for row in sites_by_result if row[0]}
        articles_result = {str(row[0]): row[1] for row in articles_by_eval if row[0]}
        
        total_evaluated = sum(articles_result.values()) if articles_result else 0
        high_quality = articles_result.get('L1', 0) + articles_result.get('L2', 0)
        success_rate = high_quality / total_evaluated if total_evaluated > 0 else 0
        
        _, recent = execute_query("SELECT COUNT(*) FROM articles WHERE create_time > NOW() - INTERVAL '24 hours'")
        articles_24h = recent[0][0] if recent else 0
        
        return jsonify({"total_sites": total_sites, "total_articles": total_articles, "sites_by_result": sites_result, "articles_by_evaluation": articles_result, "articles_24h": articles_24h, "success_rate": round(success_rate, 2), "mock": False})
    except Exception as e:
        return jsonify({"total_sites": 156, "total_articles": 2847, "sites_by_result": {"P0": 23, "P0-": 45, "P1": 67, "P2": 15, "PX": 6}, "articles_by_evaluation": {"L1": 892, "L2": 1245, "L3": 456, "L-1": 254}, "articles_24h": 156, "success_rate": 0.87, "mock": True, "error": str(e)})

@app.route('/api/sites', methods=['GET'])
def get_sites():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    try:
        columns, rows = execute_query("SELECT id, url, name, final_result, reason, create_time FROM source_sites ORDER BY create_time DESC LIMIT %s OFFSET %s", (page_size, offset))
        if not rows:
            sites = [{"id": offset+i+1, "url": f"https://example-{i+1}.com", "name": f"Site {i+1}", "final_result": ["P0","P0-","P1","P2","PX"][i%5], "reason": "Quality content" if i%3==0 else None, "create_time": datetime.now().isoformat()} for i in range(page_size)]
            return jsonify({"sites": sites, "page": page, "page_size": page_size, "total": 156, "mock": True})
        sites = [dict(zip(columns, row)) for row in rows]
        _, total = execute_query("SELECT COUNT(*) FROM source_sites")
        total_count = total[0][0] if total else 0
        return jsonify({"sites": sites, "page": page, "page_size": page_size, "total": total_count, "mock": False})
    except Exception as e:
        sites = [{"id": offset+i+1, "url": f"https://example-{i+1}.com", "name": f"Site {i+1}", "final_result": ["P0","P0-","P1","P2","PX"][i%5], "create_time": datetime.now().isoformat()} for i in range(page_size)]
        return jsonify({"sites": sites, "page": page, "page_size": page_size, "total": 156, "mock": True, "error": str(e)})

@app.route('/api/articles', methods=['GET'])
def get_articles():
    page = int(request.args.get('page', 1))
    page_size = int(request.args.get('page_size', 20))
    offset = (page - 1) * page_size
    try:
        columns, rows = execute_query("SELECT id, url, source_site_url, category, evaluation_result, create_time FROM articles ORDER BY create_time DESC LIMIT %s OFFSET %s", (page_size, offset))
        if not rows:
            articles = [{"id": offset+i+1, "url": f"https://example.com/article-{i+1}", "source_site_url": f"https://example-{i%5+1}.com", "category": ["Technology","Science","Education","Business"][i%4], "evaluation_result": ["L1","L2","L3","L-1"][i%4], "create_time": datetime.now().isoformat()} for i in range(page_size)]
            return jsonify({"articles": articles, "page": page, "page_size": page_size, "total": 2847, "mock": True})
        articles = [dict(zip(columns, row)) for row in rows]
        _, total = execute_query("SELECT COUNT(*) FROM articles")
        return jsonify({"articles": articles, "page": page, "page_size": page_size, "total": total[0][0] if total else 0, "mock": False})
    except Exception as e:
        articles = [{"id": offset+i+1, "url": f"https://example.com/article-{i+1}", "source_site_url": f"https://example-{i%5+1}.com", "category": "Technology", "evaluation_result": "L1", "create_time": datetime.now().isoformat()} for i in range(page_size)]
        return jsonify({"articles": articles, "page": page, "page_size": page_size, "total": 2847, "mock": True, "error": str(e)})

@app.route('/api/crawler/start', methods=['POST'])
def start_crawler():
    global crawler_process
    try:
        pid = get_crawler_pid()
        if pid:
            try:
                os.kill(pid, 0)
                return jsonify({"status": "running", "message": "Crawler is already running", "pid": pid})
            except OSError:
                clear_crawler_pid()
        crawler_process = subprocess.Popen(['python', 'main.py'], cwd=os.path.dirname(os.path.abspath(__file__)), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        set_crawler_pid(crawler_process.pid)
        return jsonify({"status": "started", "message": "Crawler started successfully", "pid": crawler_process.pid})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/crawler/stop', methods=['POST'])
def stop_crawler():
    try:
        pid = get_crawler_pid()
        if not pid:
            return jsonify({"status": "stopped", "message": "No crawler is running"})
        try:
            os.kill(pid, 9)
            clear_crawler_pid()
            return jsonify({"status": "stopped", "message": "Crawler stopped successfully"})
        except OSError:
            clear_crawler_pid()
            return jsonify({"status": "stopped", "message": "Crawler was not running"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/crawler/status', methods=['GET'])
def crawler_status():
    pid = get_crawler_pid()
    if not pid:
        return jsonify({"status": "stopped", "running": False})
    try:
        os.kill(pid, 0)
        return jsonify({"status": "running", "running": True, "pid": pid})
    except OSError:
        clear_crawler_pid()
        return jsonify({"status": "stopped", "running": False})

PROMPTS_FILE = 'prompts.json'
PROMPT_VERSIONS_FILE = 'prompt_versions.json'

def load_prompts():
    if os.path.exists(PROMPTS_FILE):
        with open(PROMPTS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"site_discovery": {"name": "Site Discovery Prompt", "content": "Find high-quality knowledge-based websites with text and images.", "version": 1, "last_updated": datetime.now().isoformat()}, "content_extraction": {"name": "Content Extraction", "content": "Extract main content including text, images, metadata.", "version": 1, "last_updated": datetime.now().isoformat()}, "site_quality": {"name": "Site Quality Evaluation", "content": "Evaluate site quality: P0, P0-, P1, P2, PX", "version": 1, "last_updated": datetime.now().isoformat()}, "article_quality": {"name": "Article Quality Evaluation", "content": "Evaluate article quality: L1, L2, L3, L-1", "version": 1, "last_updated": datetime.now().isoformat()}}

def save_prompts(prompts):
    with open(PROMPTS_FILE, 'w', encoding='utf-8') as f:
        json.dump(prompts, f, indent=2, ensure_ascii=False)

def load_prompt_versions():
    if os.path.exists(PROMPT_VERSIONS_FILE):
        with open(PROMPT_VERSIONS_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_prompt_versions(versions):
    with open(PROMPT_VERSIONS_FILE, 'w', encoding='utf-8') as f:
        json.dump(versions, f, indent=2, ensure_ascii=False)

@app.route('/api/prompts', methods=['GET'])
def get_prompts():
    return jsonify(load_prompts())

@app.route('/api/prompts/<prompt_key>', methods=['GET'])
def get_prompt(prompt_key):
    prompts = load_prompts()
    if prompt_key in prompts:
        return jsonify(prompts[prompt_key])
    return jsonify({"error": "Prompt not found"}), 404

@app.route('/api/prompts/<prompt_key>', methods=['PUT'])
def update_prompt(prompt_key):
    data = request.json
    prompts = load_prompts()
    versions = load_prompt_versions()
    if prompt_key not in prompts:
        return jsonify({"error": "Prompt not found"}), 404
    current = prompts[prompt_key]
    version_key = f"{prompt_key}_v{current['version']}"
    if version_key not in versions:
        versions[version_key] = {"content": current['content'], "timestamp": current.get('last_updated', datetime.now().isoformat())}
    prompts[prompt_key]['content'] = data.get('content', current['content'])
    prompts[prompt_key]['version'] = current['version'] + 1
    prompts[prompt_key]['last_updated'] = datetime.now().isoformat()
    save_prompts(prompts)
    save_prompt_versions(versions)
    return jsonify(prompts[prompt_key])

@app.route('/api/prompts/<prompt_key>/versions', methods=['GET'])
def get_prompt_versions(prompt_key):
    versions = load_prompt_versions()
    return jsonify({k: v for k, v in versions.items() if k.startswith(f"{prompt_key}_")})

@app.route('/api/export/sql', methods=['POST'])
def export_sql():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    if not query.strip().upper().startswith('SELECT'):
        return jsonify({"error": "Only SELECT queries are allowed"}), 400
    try:
        columns, rows = execute_query(query)
        results = [dict(zip(columns, row)) for row in rows]
        return jsonify({"columns": columns, "data": results, "count": len(results)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    data = request.json
    query = data.get('query', '')
    if not query:
        return jsonify({"error": "Query is required"}), 400
    try:
        columns, rows = execute_query(query)
        import csv, io
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(columns)
        for row in rows:
            writer.writerow(row)
        filename = f"export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        os.makedirs('exports', exist_ok=True)
        with open(os.path.join('exports', filename), 'w', encoding='utf-8') as f:
            f.write(output.getvalue())
        return jsonify({"filename": filename, "rows": len(rows)})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/')
def index():
    return send_from_directory('dashboard', 'index.html')

@app.route('/<path:path>')
def serve_static(path):
    return send_from_directory('dashboard', path)

if __name__ == '__main__':
    app.run(host=FLASK_HOST, port=FLASK_PORT, debug=FLASK_DEBUG)
