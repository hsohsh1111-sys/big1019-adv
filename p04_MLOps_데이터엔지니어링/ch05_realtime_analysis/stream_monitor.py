"""실시간 스트리밍 이상 탐지 — Kafka 없이 파이썬만으로 Producer → Broker(Queue) → Consumer 구조를 체험.

Producer : 설비 센서(온도·진동)를 초당 20건 생성, 가끔 이상값(과열·진동 급증) 주입
Broker   : queue.Queue (Kafka 토픽 역할)
Consumer : 슬라이딩 윈도우 통계 + Z-점수 탐지 + Isolation Forest 모델 판정 + 경보 쿨다운

실행:
  uvicorn web:app --reload                 # 브라우저 실시간 차트 → http://127.0.0.1:8000
  python stream_monitor.py --seconds 15    # 터미널
"""
import argparse
import json
import queue
import random
import statistics
import threading
import time
from collections import deque
from datetime import datetime

import numpy as np
from sklearn.ensemble import IsolationForest

RATE = 20  # 초당 메시지 수
WINDOW = 50  # 슬라이딩 윈도우 크기
WARMUP = 100  # 모델 학습에 쓸 초기 정상 데이터 수
Z_LIMIT = 3.0
COOLDOWN_SEC = 2.0


def producer(broker, stop, seed=7):
    rng = random.Random(seed)
    seq = 0
    while not stop.is_set():
        seq += 1
        temp, vib = rng.gauss(65, 1.5), rng.gauss(0.30, 0.03)
        if seq > WARMUP and rng.random() < 0.02:  # 2% 확률로 이상 상황
            if rng.random() < 0.5:
                temp += rng.uniform(10, 18)
            else:
                vib *= rng.uniform(2.5, 4)
        broker.put(json.dumps({"seq": seq, "ts": time.time(), "machine": "M-01",
                               "temp": round(temp, 2), "vibration": round(vib, 3)}))
        time.sleep(1 / RATE)
    broker.put(None)  # 종료 신호


class Consumer:
    def __init__(self):
        self.window = {"temp": deque(maxlen=WINDOW), "vibration": deque(maxlen=WINDOW)}
        self.train_buffer, self.model = [], None
        self.last_alert, self.stats = 0.0, {"processed": 0, "z_alerts": 0, "ml_alerts": 0, "suppressed": 0}
        self.latencies = []

    def zscores(self, msg):
        scores = {}
        for key, win in self.window.items():
            if len(win) >= 10:
                mean, std = statistics.fmean(win), statistics.pstdev(win) or 1e-9
                scores[key] = (msg[key] - mean) / std
        return scores

    def handle(self, raw):
        """메시지 1건 처리 → 판정 결과(event dict) 반환."""
        msg = json.loads(raw)
        self.stats["processed"] += 1
        features = [msg["temp"], msg["vibration"]]
        event = {"seq": msg["seq"], "time": f"{datetime.fromtimestamp(msg['ts']):%H:%M:%S}", "temp": msg["temp"],
                 "vibration": msg["vibration"], "warmup": self.model is None, "alert": False, "suppressed": False}

        if self.model is None:  # 워밍업: 정상 데이터를 모아 모델 학습
            self.train_buffer.append(features)
            if len(self.train_buffer) == WARMUP:
                self.model = IsolationForest(contamination=0.01, random_state=0).fit(np.array(self.train_buffer))
                event["model_trained"] = True
        z = self.zscores(msg)
        z_hit = {k: round(v, 1) for k, v in z.items() if abs(v) > Z_LIMIT}
        ml_hit = self.model is not None and bool(self.model.predict([features])[0] == -1)

        if z_hit or ml_hit:
            self.stats["z_alerts"] += bool(z_hit)
            self.stats["ml_alerts"] += ml_hit
            now = time.time()
            event["reason"] = ", ".join([f"{k} Z={v}" for k, v in z_hit.items()] + (["ML 이상 판정"] if ml_hit else []))
            if now - self.last_alert < COOLDOWN_SEC:  # 같은 상황의 경보 폭주 방지
                self.stats["suppressed"] += 1
                event["suppressed"] = True
            else:
                self.last_alert = now
                event["alert"] = True
        else:  # 이상값은 윈도우에 넣지 않아 기준이 오염되지 않게 한다
            for key in self.window:
                self.window[key].append(msg[key])
        self.latencies.append((time.time() - msg["ts"]) * 1000)

        if self.stats["processed"] % (RATE * 5) == 0:  # 5초마다 텀블링 요약
            event["tumbling"] = {"temp": round(statistics.fmean(self.window["temp"]), 1),
                                 "vibration": round(statistics.fmean(self.window["vibration"]), 3)}
        return event

    def summary(self):
        return {**self.stats, "avg_latency_ms": round(statistics.fmean(self.latencies), 2) if self.latencies else 0}


def stream(seconds, consumer):
    """Producer 스레드를 띄우고, 정해진 시간 동안 Consumer 판정 결과를 하나씩 내보낸다(generator)."""
    broker, stop = queue.Queue(maxsize=1000), threading.Event()
    threading.Thread(target=producer, args=(broker, stop), daemon=True).start()
    timer = threading.Timer(seconds, stop.set)
    timer.start()
    try:
        while (raw := broker.get()) is not None:
            yield consumer.handle(raw)
    finally:  # 브라우저가 연결을 끊어도 생산을 멈춘다
        stop.set()
        timer.cancel()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--seconds", type=int, default=15)
    args = parser.parse_args()

    consumer = Consumer()
    print(f"스트리밍 시작 ({args.seconds}초, 초당 {RATE}건) — 처음 {WARMUP / RATE:.0f}초는 모델 학습용 워밍업")
    for e in stream(args.seconds, consumer):
        if e.get("model_trained"):
            print(f"[모델] 초기 {WARMUP}건으로 Isolation Forest 학습 완료 → 실시간 판정 시작")
        if e["alert"]:
            print(f"🚨 {e['time']} #{e['seq']:<4} 온도 {e['temp']:5.1f}℃ 진동 {e['vibration']:.3f}  ← {e['reason']}")
        if "tumbling" in e:
            print(f"   ⏱ {e['seq']}건 처리 | 최근 평균 온도 {e['tumbling']['temp']}℃ 진동 {e['tumbling']['vibration']}")

    s = consumer.summary()
    print(f"\n[요약] 처리 {s['processed']}건 | Z-점수 경보 {s['z_alerts']} | ML 경보 {s['ml_alerts']} | "
          f"쿨다운으로 묶인 경보 {s['suppressed']} | 평균 지연 {s['avg_latency_ms']}ms")


if __name__ == "__main__":
    main()
