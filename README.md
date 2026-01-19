# SentinelMesh

Local-first network monitoring and security visibility tool.

SentinelMesh is a privacy-first, local-only network monitoring project built to help you understand what is happening inside your own network without sending any data to the cloud.
It focuses on clarity, trust, and explainability instead of fake AI, telemetry, or tracking.

This project was built as a learning + portfolio project and also works as a real lightweight WiFi monitoring system for home labs, students, and small environments.

---

## What it does

* Discovers devices on the local network (metadata only)
* Learns a baseline per environment (home / office / lab)
* Tracks changes and activity over time
* Shows a clean SOC-style dashboard
* Explains system state instead of panicking
* Stores everything locally (JSON / CSV / logs)
* Exports logs for analysis
* Includes post-quantum security awareness (informational)
* No cloud, no tracking, no telemetry, no uploads

---

## Privacy first (important)

SentinelMesh is designed to be safe by default.

* No data leaves your device
* No cloud services used
* No telemetry
* No tracking
* All logs stay local
* Screenshots shared publicly are masked
* You stay in control of your data

This makes it safe for home labs, learning, SOC practice, and research.

---

## Screenshots

All screenshots are taken from a local deployment.
IP addresses and MAC addresses are intentionally masked before publishing.

Dashboard overview
docs/screenshots/sentinelmesh_masked_1.png

Device detection
docs/screenshots/sentinelmesh_masked_2.png

Timeline and awareness panel
docs/screenshots/sentinelmesh_masked_3.png

---

## How to run locally

Backend:

```bash
python -m uvicorn backend.main:app --reload
```

Frontend:

```bash
cd frontend
python -m http.server 5500
```

Open in browser:

```text
http://127.0.0.1:5500
```

Everything runs locally on your machine.

---

## Project structure

```
SentinelMesh/
├── backend/
├── frontend/
├── docs/
│   └── screenshots/
├── data/          (local runtime data, not uploaded)
├── README.md
├── LICENSE
└── .gitignore
```

---

## Future direction

SentinelMesh is intentionally lightweight and local-first.

This architecture can be extended into:

* Personal WiFi health monitor
* Small office network visibility tool
* Privacy-preserving alternative to cloud monitors
* Learning platform for SOC and blue-team training

The core rule will always stay the same:
**no cloud, no tracking, no data leaving the device.**

---

## License

MIT License

---

## Author

Built by Adrian A
Cybersecurity student
Network security · SOC · Blue team · VAPT

---

SentinelMesh · Local monitoring active · No data leaves this device
