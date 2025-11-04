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

````

### 2\. 시뮬레이터 실행

메인 파일인 `main.py`를 실행합니다.

```bash
python main.py
```

### 3\. 모드 선택

실행 시 두 가지 모드를 선택할 수 있습니다.

```text
==================================================
          운영체제 스케줄러 시뮬레이션
==================================================
모드를 선택하세요:
  [1] PERFORMANCE (알고리즘 성능 비교 - 랜덤 생성)
  [2] SYNC (동기화/교착상태 테스트 - 파일 입력)
선택 (1 또는 2):
```

  * **`1` 입력 (PERFORMANCE)**: `generator.py`를 이용해 랜덤 프로세스를 생성하고 8가지 알고리즘(FCFS, RR, SJF, Priority 2종, MLFQ, RM, EDF)을 모두 실행한 뒤, 성능 비교 차트를 시각화합니다.
  * **`2` 입력 (SYNC)**: 동기화 테스트용 하위 메뉴가 나타납니다.

-----

## 3\. 테스트 시뮬레이션 시나리오 🔬

`main.py`의 [SYNC] 모드 선택 시, 다음과 같은 특정 시나리오를 테스트할 수 있습니다.

### 시나리오 1: 우선순위 역전 (Priority Inversion)

  * **선택**: `[2] SYNC` 모드 -\> `[1] 고전적 동기화 문제 (우선순위 역전)`
  * **입력 파일**: `producer_consumer.txt`
  * **알고리즘**: 정적 우선순위 (`SimulatorPriorityStatic`)
  * **상황 설명**:
    1.  `t=0`, P1 (우선순위 5, 낮음) 도착, 'R1' Lock 획득 후 CPU 작업.
    2.  `t=2`, P3 (우선순위 3, 중간) 도착, CPU 작업 시작 (P1 선점).
    3.  `t=3`, P2 (우선순위 1, 높음) 도착, 'R1' Lock 시도.
  * **예상 결과**: P2는 P1이 'R1'을 반납할 때까지 대기(Waiting) 상태가 됩니다. 하지만 P1은 P3(중간 우선순위)에게 CPU를 빼앗겨 실행되지 못합니다. 결과적으로 가장 높은 우선순위의 P2가 중간 우선순위의 P3 때문에 무한정 대기하는 **우선순위 역전** 현상이 시뮬레이션 로그와 간트 차트를 통해 관찰됩니다.

### 시나리오 2: 교착상태 예방 (Deadlock Prevention)

  * **선택**: `[2] SYNC` 모드 -\> `[2] 교착상태 예방 (자원 순서 할당)`
  * **입력 파일**: `deadlock_prevention.txt`
  * **알고리즘**: 정적 우선순위 (`SimulatorPriorityStatic`)
  * **구현된 예방책**:
      * 자원('R1', 'R2')에 고유 ID (R1=0, R2=1)를 부여합니다.
      * `simulator_priority_static.py`의 'LOCK' 처리 로직에서, 프로세스가 **자신이 보유한 자원의 최대 ID보다 낮은 ID의 자원**을 요청하는지 검사합니다.
      * 규칙 위반 시, 해당 프로세스를 강제 종료(Terminated)시키고 보유한 모든 자원을 즉시 반납(Unlock)하여 교착 상태를 원천적으로 방지합니다.
  * **상황 설명**:
    1.  P1: `LOCK:R1` (ID 0 요청) -\> `LOCK:R2` (ID 1 요청). (올바른 순서, 성공)
    2.  P2: `LOCK:R2` (ID 1 요청, 획득) -\> `LOCK:R1` (ID 0 요청). (잘못된 순서)
  * **예상 결과**: P1은 정상 종료됩니다. P2가 R2(ID 1)를 보유한 상태에서 R1(ID 0)을 요청하는 순간, 시뮬레이터가 "교착상태 예방: ... 순서 없이 요청함. 프로세스 강제 종료." 로그를 출력하며 P2를 즉시 종료시킵니다.

<!-- end list -->

```
```
