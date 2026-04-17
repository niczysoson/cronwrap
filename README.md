# cronwrap

A lightweight wrapper for cron jobs that adds logging, alerting, and retry logic.

---

## Installation

```bash
pip install cronwrap
```

---

## Usage

Wrap any shell command or script with `cronwrap` to get automatic logging, failure alerts, and retries.

**Command line:**

```bash
cronwrap --retries 3 --alert email@example.com -- python /path/to/job.py
```

**Python API:**

```python
from cronwrap import CronJob

job = CronJob(
    command="python /path/to/job.py",
    retries=3,
    alert="email@example.com",
    log_file="/var/log/cronwrap/job.log"
)

job.run()
```

**Key options:**

| Option | Description |
|--------|-------------|
| `--retries` | Number of retry attempts on failure |
| `--alert` | Email address to notify on failure |
| `--log-file` | Path to write job output logs |
| `--timeout` | Max execution time in seconds |

Logs are written in structured JSON format for easy parsing and monitoring.

---

## Features

- 📋 Structured logging for every job run
- 🔁 Configurable retry logic with backoff
- 🚨 Email alerts on job failure
- ⏱️ Execution timeout support
- 🪶 Zero heavy dependencies

---

## License

This project is licensed under the [MIT License](LICENSE).