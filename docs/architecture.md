# Architecture

SentinelMesh is designed to be boring, predictable, and local-only.

## Core Components

### 1. Data Layer (`data/`)
- **Philosophy**: Plain text files. No hidden databases. You own your data.
- **Files**:
  - `audit.log`: Append-only secure log of all system actions.
  - `alerts.csv`: History of triggered alerts.
  - `devices.json`: State of known devices.
  - `history.csv`: Metrics trending.
  - `baseline.json`: Learned environment parameters.

### 2. Backend Layer (`backend/`)
- **Technology**: Python + FastAPI.
- **Modules**:
  - `scanner.py`: Passive ARP table reader.
  - `analyzer.py`: Metadata risk scoring engine.
  - `baseline.py`: Adaptive learning logic.
  - `health.py`: Self-monitoring diagnostics.
  - `alerts.py`: Notification dispatcher.

### 3. Frontend Layer
- Currently headless (Phase 0-9). UI is optional and decoupled.

## Data Flow
1. **Scan**: `main` calls `scanner` -> updates `devices.json`.
2. **Analysis**: `main` calls `analyzer` -> reads `psutil` + `baseline` -> calculates risk.
3. **Learning**: `main` calls `baseline` -> updates `baseline.json` if in learning mode.
4. **Alerting**: `main` calls `alerts` -> checks risk score -> logs to `alerts.csv` -> sends email (optional).
