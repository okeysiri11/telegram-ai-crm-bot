"""Telemetry AI engines — live stream, record/replay, analyzers (Sprint 11.3)."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone
from statistics import mean
from typing import Any

from applications.drone_platform.shared.exceptions import NotFoundError, ValidationError
from applications.drone_platform.shared.store import DroneStore, drone_store
from applications.drone_platform.telemetry.service import TelemetryService, telemetry_service


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _samples(session: dict[str, Any]) -> list[dict[str, Any]]:
    return list(session.get("samples") or [])


class LiveTelemetryEngine:
    def __init__(self, service: TelemetryService | None = None) -> None:
        self.service = service or telemetry_service

    def ingest(self, session_id: str, sample: dict[str, Any]) -> dict[str, Any]:
        return self.service.record_sample(session_id, {**sample, "source": sample.get("source", "live")})

    def snapshot(self, session_id: str) -> dict[str, Any]:
        session = self.service.get_session(session_id)
        samples = _samples(session)
        latest = samples[-1] if samples else {}
        return {
            "session_id": session_id,
            "sample_count": len(samples),
            "latest": latest,
            "status": session.get("status"),
        }


class TelemetryRecorder:
    def __init__(self, store: DroneStore | None = None, service: TelemetryService | None = None) -> None:
        self.store = store or drone_store
        self.service = service or telemetry_service

    def start(self, session_id: str, *, label: str = "") -> dict[str, Any]:
        session = self.service.get_session(session_id)
        rid = f"rec_{uuid.uuid4().hex[:12]}"
        recording = {
            "recording_id": rid,
            "session_id": session_id,
            "label": label or f"recording-{rid}",
            "uav_id": session.get("uav_id", ""),
            "started_at": _now(),
            "status": "recording",
            "sample_count_at_start": len(_samples(session)),
        }
        self.store.telemetry_recordings.save(rid, recording)
        return recording

    def stop(self, recording_id: str) -> dict[str, Any]:
        recording = self.store.telemetry_recordings.get(recording_id)
        if recording is None:
            raise NotFoundError("telemetry_recording", recording_id)
        session = self.service.get_session(recording["session_id"])
        recording["stopped_at"] = _now()
        recording["status"] = "stopped"
        recording["sample_count"] = len(_samples(session)) - int(recording.get("sample_count_at_start", 0))
        self.store.telemetry_recordings.save(recording_id, recording)
        return recording

    def list(self) -> list[dict[str, Any]]:
        return self.store.telemetry_recordings.list_all()


class TelemetryDatabase:
    def __init__(self, store: DroneStore | None = None, service: TelemetryService | None = None) -> None:
        self.store = store or drone_store
        self.service = service or telemetry_service

    def query(self, session_id: str, *, fields: list[str] | None = None, limit: int = 1000) -> dict[str, Any]:
        session = self.service.get_session(session_id)
        samples = _samples(session)[-limit:]
        if fields:
            samples = [{k: s.get(k) for k in fields if k in s or k == "recorded_at"} | {"recorded_at": s.get("recorded_at")} for s in samples]
        return {"session_id": session_id, "count": len(samples), "samples": samples}


class TelemetryReplay:
    def __init__(self, store: DroneStore | None = None, service: TelemetryService | None = None) -> None:
        self.store = store or drone_store
        self.service = service or telemetry_service

    def create(self, session_id: str, *, speed: float = 1.0) -> dict[str, Any]:
        session = self.service.get_session(session_id)
        rid = f"rpl_{uuid.uuid4().hex[:12]}"
        replay = {
            "replay_id": rid,
            "session_id": session_id,
            "speed": speed,
            "cursor": 0,
            "total": len(_samples(session)),
            "status": "ready",
            "created_at": _now(),
        }
        self.store.telemetry_replays.save(rid, replay)
        return replay

    def step(self, replay_id: str) -> dict[str, Any]:
        replay = self.store.telemetry_replays.get(replay_id)
        if replay is None:
            raise NotFoundError("telemetry_replay", replay_id)
        session = self.service.get_session(replay["session_id"])
        samples = _samples(session)
        cursor = int(replay.get("cursor", 0))
        if cursor >= len(samples):
            replay["status"] = "finished"
            self.store.telemetry_replays.save(replay_id, replay)
            return {"replay_id": replay_id, "finished": True, "sample": None}
        sample = samples[cursor]
        replay["cursor"] = cursor + 1
        replay["status"] = "playing"
        self.store.telemetry_replays.save(replay_id, replay)
        return {"replay_id": replay_id, "finished": False, "sample": sample, "cursor": replay["cursor"]}


class TelemetryTimeline:
    def build(self, session: dict[str, Any]) -> dict[str, Any]:
        events = []
        for idx, sample in enumerate(_samples(session)):
            events.append(
                {
                    "index": idx,
                    "at": sample.get("recorded_at") or sample.get("t"),
                    "kind": sample.get("event") or "sample",
                    "summary": {
                        k: sample.get(k)
                        for k in ("lat", "lon", "alt", "battery", "gps_fix", "mode", "voltage")
                        if k in sample
                    },
                }
            )
        return {"session_id": session.get("session_id"), "event_count": len(events), "events": events}


class SignalQualityMonitor:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        rssi = [float(s["rssi"]) for s in samples if s.get("rssi") is not None]
        quality = "unknown"
        if rssi:
            avg = mean(rssi)
            quality = "good" if avg > 70 else "degraded" if avg > 40 else "poor"
        return {"metric": "signal_quality", "sample_count": len(rssi), "avg_rssi": mean(rssi) if rssi else None, "quality": quality}


class RadioLinkAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        losses = sum(1 for s in samples if s.get("radio_loss") or s.get("link_loss"))
        return {
            "metric": "radio_link",
            "loss_events": losses,
            "status": "ok" if losses == 0 else "intermittent" if losses < 3 else "critical",
        }


class GPSQualityAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        sats = [int(s["gps_fix"]) for s in samples if s.get("gps_fix") is not None]
        hdop = [float(s["hdop"]) for s in samples if s.get("hdop") is not None]
        glitches = 0
        prev = None
        for s in samples:
            if prev is not None and s.get("lat") is not None and prev.get("lat") is not None:
                if abs(float(s["lat"]) - float(prev["lat"])) > 0.01:
                    glitches += 1
            prev = s
        avg_sats = mean(sats) if sats else None
        quality = "unknown"
        if avg_sats is not None:
            quality = "good" if avg_sats >= 10 else "fair" if avg_sats >= 6 else "poor"
        return {
            "metric": "gps_quality",
            "avg_satellites": avg_sats,
            "avg_hdop": mean(hdop) if hdop else None,
            "glitch_count": glitches,
            "quality": quality,
        }


class BatteryAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        pct = [float(s["battery"]) for s in samples if s.get("battery") is not None]
        volts = [float(s["voltage"]) for s in samples if s.get("voltage") is not None]
        drain = None
        if len(pct) >= 2:
            drain = pct[0] - pct[-1]
        status = "ok"
        if pct and pct[-1] < 20:
            status = "low"
        if pct and pct[-1] < 10:
            status = "critical"
        return {
            "metric": "battery",
            "start_pct": pct[0] if pct else None,
            "end_pct": pct[-1] if pct else None,
            "drain_pct": drain,
            "avg_voltage": mean(volts) if volts else None,
            "status": status,
        }


class PowerConsumptionAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        amps = [float(s["current"]) for s in samples if s.get("current") is not None]
        return {
            "metric": "power_consumption",
            "avg_current_a": mean(amps) if amps else None,
            "peak_current_a": max(amps) if amps else None,
            "status": "ok" if not amps or max(amps) < 80 else "high_draw",
        }


class MotorPerformanceAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        outputs = []
        for s in samples:
            motors = s.get("motors") or s.get("motor_outputs")
            if isinstance(motors, list) and motors:
                outputs.append([float(x) for x in motors])
        imbalance = 0.0
        if outputs:
            spreads = [max(row) - min(row) for row in outputs]
            imbalance = mean(spreads)
        return {
            "metric": "motor_performance",
            "frames": len(outputs),
            "avg_imbalance": imbalance,
            "status": "ok" if imbalance < 15 else "imbalanced",
        }


class ESCAnalyzer:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        temps = []
        faults = 0
        for s in samples:
            if s.get("esc_fault"):
                faults += 1
            esc_temp = s.get("esc_temp") or s.get("esc_temperature")
            if isinstance(esc_temp, list):
                temps.extend(float(t) for t in esc_temp)
            elif esc_temp is not None:
                temps.append(float(esc_temp))
        return {
            "metric": "esc",
            "fault_events": faults,
            "avg_temp_c": mean(temps) if temps else None,
            "status": "ok" if faults == 0 else "fault",
        }


class SensorHealthMonitor:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        issues = []
        for s in samples:
            if s.get("imu_error"):
                issues.append("imu")
            if s.get("baro_error"):
                issues.append("baro")
            if s.get("mag_error") or s.get("compass_error"):
                issues.append("compass")
            if s.get("ekf_error"):
                issues.append("ekf")
        unique = sorted(set(issues))
        return {"metric": "sensor_health", "issues": unique, "status": "ok" if not unique else "degraded"}


class FailsafeMonitor:
    def analyze(self, samples: list[dict[str, Any]]) -> dict[str, Any]:
        events = []
        for s in samples:
            if s.get("failsafe") or s.get("fs_event"):
                events.append({"at": s.get("recorded_at"), "type": s.get("failsafe") or s.get("fs_event")})
            if s.get("rc_loss"):
                events.append({"at": s.get("recorded_at"), "type": "rc_loss"})
            if s.get("telemetry_loss"):
                events.append({"at": s.get("recorded_at"), "type": "telemetry_loss"})
        return {"metric": "failsafe", "event_count": len(events), "events": events, "status": "ok" if not events else "triggered"}


class TelemetryAIManager:
    """Unified Telemetry AI facade."""

    def __init__(self, store: DroneStore | None = None, service: TelemetryService | None = None) -> None:
        self.store = store or drone_store
        self.service = service or telemetry_service
        self.live = LiveTelemetryEngine(self.service)
        self.recorder = TelemetryRecorder(self.store, self.service)
        self.database = TelemetryDatabase(self.store, self.service)
        self.replay = TelemetryReplay(self.store, self.service)
        self.timeline = TelemetryTimeline()
        self.signal = SignalQualityMonitor()
        self.radio = RadioLinkAnalyzer()
        self.gps = GPSQualityAnalyzer()
        self.battery = BatteryAnalyzer()
        self.power = PowerConsumptionAnalyzer()
        self.motor = MotorPerformanceAnalyzer()
        self.esc = ESCAnalyzer()
        self.sensors = SensorHealthMonitor()
        self.failsafe = FailsafeMonitor()

    def analyze_session(self, session_id: str) -> dict[str, Any]:
        session = self.service.get_session(session_id)
        samples = _samples(session)
        if not samples:
            raise ValidationError("No telemetry samples to analyze")
        return {
            "session_id": session_id,
            "sample_count": len(samples),
            "timeline": self.timeline.build(session),
            "analyzers": {
                "signal_quality": self.signal.analyze(samples),
                "radio_link": self.radio.analyze(samples),
                "gps_quality": self.gps.analyze(samples),
                "battery": self.battery.analyze(samples),
                "power": self.power.analyze(samples),
                "motor": self.motor.analyze(samples),
                "esc": self.esc.analyze(samples),
                "sensor_health": self.sensors.analyze(samples),
                "failsafe": self.failsafe.analyze(samples),
            },
            "analyzed_at": _now(),
        }

    def status(self) -> dict[str, Any]:
        return {
            "telemetry_ai": "1.0",
            "sessions": self.store.telemetry_sessions.count(),
            "recordings": self.store.telemetry_recordings.count(),
            "capabilities": [
                "live_engine",
                "recorder",
                "database",
                "replay",
                "timeline",
                "signal_quality",
                "radio_link",
                "gps_quality",
                "battery",
                "power",
                "motor",
                "esc",
                "sensor_health",
                "failsafe",
            ],
        }


telemetry_ai_manager = TelemetryAIManager()
