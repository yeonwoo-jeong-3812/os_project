# 💻 OS 스케줄러 시뮬레이션 프로젝트

본 프로젝트는 Python으로 다양한 CPU 스케줄링 알고리즘과 동기화 문제를 시뮬레이션하기 위해 개발되었습니다.
시뮬레이터는 시간 단위(tick)로 이벤트를 처리하며, 각 알고리즘의 성능을 비교하고 교착상태 및 우선순위 역전과 같은 동기화 시나리오를 테스트할 수 있습니다.

---

## 1. 구현 방법 🚀

프로젝트는 여러 모듈로 구성되어 있으며, 각 모듈의 핵심 구현 방법은 다음과 같습니다.

### 📄 `process.py` (프로세스 정의)

* **`Process` 클래스**: PCB(Process Control Block) 역할을 합니다.
* **실행 패턴 파싱**: 프로세스 생성 시 `"CPU:5,IO:10,LOCK:R1,UNLOCK:R1"` 과 같은 문자열을 입력받습니다.
* `__init__` 메서드 내에서 이 문자열을 파싱하여 `[('CPU', 5), ('IO', 10), ('LOCK', 'R1'), ('UNLOCK', 'R1')]` 형태의 튜플 리스트(`self.burst_pattern`)로 변환하여 저장합니다.
* `get_current_burst()`: 현재 실행해야 할 버스트(작업)를 반환합니다.
* `advance_to_next_burst()`: 다음 작업으로 인덱스를 이동시킵니다.

### 🔒 `sync.py` (동기화 구현)

* **`Resource` 클래스**: Mutex 역할을 하는 공유 자원을 정의합니다.
* `lock()`: 자원 획득을 시도합니다.
    * 성공 시: `self.is_locked = True`, `self.owner_pid = process.pid` 설정 후 `True` 반환.
    * 실패 시: 해당 프로세스를 `self.waiting_queue` (FIFO, `collections.deque`)에 추가하고 `False` 반환.
* `unlock()`: 자원을 반납합니다.
    * `self.waiting_queue`에 대기 중인 프로세스가 있으면, 큐에서 하나를 꺼내(`popleft`) 새 소유자로 즉시 지정하고 해당 프로세스 객체를 반환합니다. (이후 시뮬레이터에서 Ready 큐로 이동됨)
* **자원 ID 할당**: `sync.py`의 전역 카운터(`RESOURCE_ID_COUNTER`)를 통해 `initialize_resources` 시 "R1", "R2" 등 순서대로 0, 1... 과 같은 고유 ID가 자원에 할당됩니다.

### ⚙️ `simulator_*.py` (스케줄러 알고리즘)

모든 시뮬레이터는 `current_time`을 1씩 증가시키는 메인 `run()` 루프를 가집니다. 각 루프마다 도착/I/O 완료/CPU 작업을 처리합니다.

* **FCFS (`simulator_fcfs.py`)**: Ready 큐로 `collections.deque`를 사용합니다. `append()`로 큐에 넣고 `popleft()`로 꺼내어 FIFO를 구현합니다.
* **RR (`simulator_rr.py`)**: FCFS와 동일하게 `collections.deque`를 사용합니다. `time_quantum`과 `current_time_slice` 변수를 추가로 관리합니다.
    * CPU 버스트가 끝나지 않아도 `current_time_slice`가 `time_quantum`에 도달하면, 프로세스를 Ready 큐의 맨 뒤(`append()`)로 보냅니다.
* **SJF (SRTF) (`simulator_sjf.py`)**: 선점형 SJF (SRTF)로 구현되었습니다.
    * Ready 큐로 `heapq` (최소 힙)를 사용하며, `(남은 CPU 시간, PID, 프로세스)` 튜플을 저장하여 항상 남은 시간이 가장 짧은 프로세스가 힙의 루트에 오도록 합니다.
    * 매 루프마다 새로 도착하거나 I/O가 완료된 프로세스의 남은 시간과 현재 실행 중인 프로세스의 남은 시간을 비교하여 선점(`Preemption`) 로직을 수행합니다.
* **Static Priority (`simulator_priority_static.py`)**: 선점형 정적 우선순위입니다.
    * Ready 큐로 `heapq`를 사용하며, `(명령어 우선순위, 정적 우선순위, PID)` 튜플을 키로 사용합니다.
    * **0-tick 처리**: 'LOCK'/'UNLOCK' 명령어는 CPU 작업보다 우선 처리되어야 하므로, '명령어 우선순위'를 0 (CPU는 1)으로 설정하여 힙에서 항상 최우선으로 선택되도록 구현했습니다.
* **Dynamic Priority (Aging) (`simulator_priority_dynamic.py`)**: 선점형 동적 우선순위입니다.
    * Ready 큐로 일반 `list`를 사용합니다.
    * **Aging 구현**: 매시간 `run()` 루프가 돌 때마다 Ready 큐에 있는 모든 프로세스를 순회하며 `dynamic_priority = static_priority - (대기 시간 // aging_factor)` 공식을 적용하여 우선순위를 갱신합니다.
    * 큐에서 프로세스를 선택할 때(`min(self.ready_queue, key=...)`)와 선점을 결정할 때 이 동적 우선순위를 사용합니다.
* **MLFQ (`simulator_mlfq.py`)**: 다단계 피드백 큐입니다.
    * 3개의 Ready 큐(`collections.deque`)를 구현했습니다. (Q1: RR Q=8, Q2: RR Q=16, Q3: FCFS)
    * 새 프로세스나 I/O 완료 프로세스는 항상 Q1으로 진입합니다.
    * Q1 또는 Q2에서 퀀텀을 모두 소진한 프로세스는 하위 큐(Q2 또는 Q3)로 강등됩니다.
    * 상위 큐(Q1)에 작업이 도착하면 하위 큐(Q2, Q3)에서 실행 중이던 프로세스는 선점됩니다.
* **RM (`simulator_rm.py`)**: Rate Monotonic (실시간, 정적 우선순위)
    * Ready 큐(`heapq`)에서 프로세스의 `period` (주기)를 우선순위 키로 사용합니다. 주기가 짧을수록 우선순위가 높습니다.
* **EDF (`simulator_edf.py`)**: Earliest Deadline First (실시간, 동적 우선순위)
    * Ready 큐(`heapq`)에서 `absolute_deadline` (도착 시간 + 마감 시한)을 우선순위 키로 사용합니다. 마감시한이 빠를수록 우선순위가 높습니다.

### 📊 `visualizer.py` (시각화)

* `matplotlib`, `numpy`, `pandas` 라이브러리를 사용하여 시뮬레이션 결과를 시각화합니다.
* `visualize_algorithm_complete`: 한 알고리즘의 간트 차트, 프로세스 타임라인, 통계표를 한 화면에 출력합니다.
* `compare_algorithms`: 여러 비실시간 알고리즘의 평균 반환/대기 시간, CPU 사용률을 막대그래프로 비교합니다.
* `create_realtime_analysis`: RM과 EDF의 마감시한 초과 횟수와 평균 반환 시간을 비교합니다.

---

## 2. 실행 방법 ⌨️

### 1. (필요시) 라이브러리 설치

시각화를 위해 `matplotlib`, `numpy`, `pandas`가 필요합니다.

```bash
pip install matplotlib numpy pandas
