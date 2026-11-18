"""Small Flask service used to demonstrate a CI/CD pipeline."""
import logging
import threading
import time

from flask import Flask, jsonify, request

logger = logging.getLogger("cicd-demo")


def create_app():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    app = Flask(__name__)
    started_at = time.time()
    counter = {"requests": 0}
    lock = threading.Lock()

    @app.before_request
    def count_request():
        with lock:
            counter["requests"] += 1

    @app.after_request
    def log_request(response):
        logger.info("%s %s -> %s", request.method, request.path, response.status_code)
        return response

    @app.get("/")
    def index():
        return jsonify(
            message="Hello from the CI/CD pipeline demo",
            author="Payal Shekhawat",
        )

    @app.get("/health")
    def health():
        return jsonify(status="ok")

    @app.get("/metrics")
    def metrics():
        return jsonify(
            requests_total=counter["requests"],
            uptime_seconds=round(time.time() - started_at, 1),
        )

    @app.get("/api/add")
    def add():
        a = request.args.get("a", type=int)
        b = request.args.get("b", type=int)
        if a is None or b is None:
            return jsonify(error="Query parameters a and b must be integers"), 400
        return jsonify(result=a + b)

    return app
