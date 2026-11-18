# CI/CD Pipeline with GitHub Actions, Docker and Monitoring

**Author:** Payal Shekhawat

A small Flask web service with a complete automated pipeline:

**GitHub → Build → Test → Docker → Deploy → Monitor**

Everything used here is free and open source (GitHub Actions free tier, Python, Flask, pytest, Docker Engine). No paid service or credit card is needed.

## Project structure

```
.
├── .github/workflows/ci-cd.yml   # the pipeline (GitHub Actions)
├── app/app.py                    # Flask app (/, /health, /metrics, /api/add) with request logging
├── tests/test_app.py             # automated tests (pytest)
├── scripts/deploy.sh             # Deploy stage: docker compose up + wait until healthy
├── scripts/monitor.sh            # Monitor stage: state, health, metrics, logs
├── Dockerfile                    # image with a built-in HEALTHCHECK
├── docker-compose.yml            # runs the container on port 8080
├── requirements.txt              # runtime dependencies
├── requirements-dev.txt          # runtime + pytest
└── LICENSE, .gitignore, .gitattributes
```

## The app

| Endpoint | Returns |
|---|---|
| `GET /` | `{"author":"Payal Shekhawat","message":"Hello from the CI/CD pipeline demo"}` |
| `GET /health` | `{"status":"ok"}` |
| `GET /metrics` | `{"requests_total":<number>,"uptime_seconds":<number>}` |
| `GET /api/add?a=2&b=3` | `{"result":5}` (HTTP 400 if `a` or `b` is missing or not an integer) |

Every request is written to the logs, for example `GET /health -> 200`. These logs are the basic observability of the project.

## Pipeline, stage by stage

The workflow `.github/workflows/ci-cd.yml` runs on every push to `main`, every pull request to `main`, and manually (Run workflow button). The jobs run in order; if one fails, the next ones do not run.

### 1. GitHub (trigger)
You push code with Git. GitHub starts the workflow automatically.

### 2. Build (job `build`)
Installs Python 3.12 and the dependencies, compiles the code and checks that the app can be created.
```bash
pip install -r requirements-dev.txt
python -m compileall app
python -c "from app.app import create_app; create_app(); print('App created OK')"
```
Expected output ends with: `App created OK`

### 3. Test (job `test`)
Runs the automated tests.
```bash
pytest -v
```
Expected output:
```
tests/test_app.py::test_index_returns_message PASSED
tests/test_app.py::test_health_is_ok PASSED
tests/test_app.py::test_add_returns_sum PASSED
tests/test_app.py::test_add_rejects_bad_input PASSED
tests/test_app.py::test_metrics_counts_requests PASSED
============================== 5 passed ==============================
```

### 4. Docker (job `docker`)
Builds the image and runs a smoke test: the container is started and `/health` must answer.
```bash
docker build -t cicd-demo-app:ci .
docker run -d --name smoke -p 8080:5000 cicd-demo-app:ci
curl -fsS http://localhost:8080/health
docker rm -f smoke
```
Expected: the build finishes without errors and curl prints `{"status":"ok"}`.

### 5. Deploy (job `deploy-and-monitor`, step "Deploy")
Starts the app with Docker Compose and waits until the container health check reports `healthy`.
```bash
bash scripts/deploy.sh
```
Expected output (the number of attempts can differ):
```
Waiting for container cicd-demo-app to become healthy...
  attempt 1: starting
  attempt 2: starting
  attempt 3: healthy
Deploy OK: cicd-demo-app is healthy on http://localhost:8080
```
Docker Compose also prints its own build and start lines before this.

### 6. Monitor (same job, step "Monitor")
Checks the container state, the `/health` and `/metrics` endpoints, and prints the latest logs.
```bash
bash scripts/monitor.sh
```
Expected output (values and log lines will differ):
```
== Container state ==
running / healthy
== GET /health ==
{"status":"ok"}
== GET /metrics ==
{"requests_total":3,"uptime_seconds":25.4}
== Last 10 log lines ==
cicd-demo-app  | 2026-11-19 10:00:00,000 INFO cicd-demo GET /health -> 200
...
Monitor OK
```
The job then uploads the full container logs as an artifact named `container-logs` and stops the deployment (`docker compose down`).

## Setup guide for my environment

**Windows PC (PowerShell + VS Code):** install Git for Windows and VS Code, edit the files, and push to GitHub (commands in the next section).

**Ubuntu Server in VirtualBox (Docker Engine + Compose plugin already installed):**
```bash
sudo apt update
sudo apt install -y git curl python3-venv
git clone https://github.com/payalshekhawat08-cpu/cicd-pipeline-flask-docker.git
cd cicd-pipeline-flask-docker
```
Run the tests without Docker:
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
pytest -v
deactivate
```
Run the Deploy and Monitor stages on your VM:
```bash
bash scripts/deploy.sh
bash scripts/monitor.sh
curl http://localhost:8080/
```
Stop the app:
```bash
docker compose down
```

## Push to GitHub (PowerShell)

1. On GitHub, create an **empty** repository named `cicd-pipeline-flask-docker` (do not add a README, .gitignore or license).
2. In PowerShell, inside the project folder:
```powershell
git init
git add .
git commit -m "CI/CD pipeline with GitHub Actions, Docker and monitoring"
git branch -M main
git remote add origin https://github.com/payalshekhawat08-cpu/cicd-pipeline-flask-docker.git
git push -u origin main
```

## See the pipeline run

1. Open your repository on GitHub and click the **Actions** tab.
2. Click the latest run of **CI/CD Pipeline**.
3. Click a job (Build, Test, Docker, Deploy and Monitor) to read its logs. A green tick means success.
4. In the finished run, scroll to **Artifacts** to download `container-logs`.
5. To start it manually: Actions → CI/CD Pipeline → **Run workflow**.

## Troubleshooting

| Problem | Cause | Fix |
|---|---|---|
| `permission denied while trying to connect to the Docker daemon socket` | Your Ubuntu user is not in the `docker` group | `sudo usermod -aG docker $USER`, then log out and log in again (or run the command with `sudo`) |
| `bind: address already in use` on port 8080 | Another program uses port 8080 | Stop it, or change `8080:5000` in `docker-compose.yml` and the URLs in `scripts/monitor.sh` |
| `Deploy FAILED: container did not become healthy` | The app crashed on start | Run `docker compose logs` and read the error |
| `bash: scripts/deploy.sh: No such file` or `\r: command not found` | Windows line endings | This repo forces LF with `.gitattributes`; run `git add --renormalize .` and commit again |
| `ModuleNotFoundError: No module named 'app'` when running `pytest` | pytest was not started from the project root | `cd` into the project folder and run `pytest -v` |
| `curl: command not found` | curl is not installed | `sudo apt install -y curl` |
| Workflow does not appear in the Actions tab | The file is not at `.github/workflows/ci-cd.yml` on the `main` branch | Check the path and that you pushed to `main` |
| `remote: Repository not found` or `Authentication failed` on `git push` | Wrong repo name, or the repo was not created | Create the empty repo with the exact name, and sign in with your GitHub account when asked |
| `failed to push some refs` | The new GitHub repo is not empty (README was added) | Create a new empty repo without README, or run `git pull origin main --allow-unrelated-histories` first |

## License

MIT License. Copyright (c) 2026 Payal Shekhawat.
