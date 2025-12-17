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

### 2.1. 환경 요구사항

- **Python 버전**: Python 3.7 이상
- **필수 라이브러리**: matplotlib, numpy, pandas

### 2.2. 라이브러리 설치

시각화를 위해 다음 라이브러리를 설치합니다:

```bash
pip install matplotlib numpy pandas
```

### 2.3. 프로그램 실행 방법

프로젝트는 세 가지 실행 방법을 제공합니다:

#### 방법 1: 메인 프로그램 (통합 성능 비교)

```bash
python main.py
```

실행 시 두 가지 모드를 선택할 수 있습니다:

```text
==================================================
          운영체제 스케줄러 시뮬레이션
==================================================
모드를 선택하세요:
  [1] PERFORMANCE (알고리즘 성능 비교 - 랜덤 생성)
  [2] SYNC (동기화/교착상태 테스트 - 파일 입력)
선택 (1 또는 2):
```

**[1] PERFORMANCE 모드**
- 랜덤으로 생성된 8개의 프로세스를 사용하여 모든 알고리즘을 5회 반복 실행합니다.
- 실행되는 알고리즘: FCFS, RR(Q=4), SJF, Priority(Static), Priority(Aging), MLFQ, RM, EDF
- 생성되는 시각화:
  - 알고리즘 성능 비교 차트 (평균 반환시간, 대기시간, CPU 사용률)
  - 실시간 스케줄링 분석 (RM, EDF 마감시한 초과 횟수)
  - 통합 간트 차트 (8개 알고리즘의 간트 차트 비교)
  - 문맥 교환 오버헤드 분석

**[2] SYNC 모드**
- 동기화 문제 및 교착상태 시나리오를 테스트합니다.
- 하위 메뉴에서 테스트할 시나리오를 선택합니다.

#### 방법 2: GUI 알고리즘 선택기

```bash
python gui_selector.py
```

- GUI 창에서 원하는 알고리즘을 체크박스로 선택할 수 있습니다.
- 선택한 알고리즘만 실행하여 결과를 비교합니다.
- 프로세스 개수, 도착률, CPU/IO 버스트 범위 등을 커스터마이징할 수 있습니다.

#### 방법 3: 프로세스 타임라인 시각화

```bash
python visualize_timeline.py
```

- 모든 알고리즘의 프로세스 상태 타임라인(Ready/Running/Waiting)을 시각화합니다.
- 각 프로세스의 상태 변화를 시간축에 따라 색상으로 표시합니다:
  - 🟧 Ready (주황색): CPU를 기다리는 상태
  - 🟦 Running (청록색): CPU를 사용하는 상태
  - 🟨 Waiting (노란색): I/O를 기다리는 상태

-----

## 3. 테스트 시뮬레이션 시나리오 🔬

본 프로젝트는 다양한 시나리오를 통해 스케줄링 알고리즘의 동작을 검증합니다.

### 3.1. 성능 비교 시나리오 (PERFORMANCE 모드)

#### 시나리오 A: 랜덤 워크로드 성능 비교

**실행 방법**: `python main.py` → `[1] PERFORMANCE` 선택

**테스트 구성**:
- **프로세스 수**: 8개 (일반 프로세스 6개 + 실시간 프로세스 2개)
- **프로세스 유형**: CPU-bound (30%), I/O-bound (40%), Mixed (30%)
- **도착 시간**: 포아송 분포 (λ=2.0)
- **CPU 버스트**: 1~20ms (균등 분포)
- **I/O 버스트**: 1~10ms (균등 분포)
- **반복 횟수**: 5회 (평균 및 표준편차 계산)

**측정 지표**:
1. **평균 반환 시간 (Turnaround Time)**: 프로세스 도착부터 종료까지의 시간
2. **평균 대기 시간 (Waiting Time)**: Ready 큐에서 대기한 총 시간
3. **CPU 사용률**: 전체 시간 대비 CPU가 작업을 수행한 시간의 비율
4. **문맥 교환 횟수**: 프로세스 간 전환이 발생한 횟수
5. **마감시한 초과 횟수** (실시간 알고리즘): 데드라인을 놓친 작업 수

**예상 결과**:
- **FCFS**: 간단하지만 convoy effect로 인해 대기 시간이 길어질 수 있음
- **RR**: 공평한 CPU 할당, 문맥 교환이 많아 오버헤드 발생
- **SJF**: 짧은 작업 우선 처리로 평균 대기 시간 최소화
- **Priority (Static)**: 우선순위에 따른 처리, 기아 현상 가능
- **Priority (Aging)**: 동적 우선순위로 기아 현상 방지
- **MLFQ**: 다양한 작업 유형에 적응적으로 대응
- **RM**: 주기가 짧은 실시간 작업 우선 처리
- **EDF**: 마감시한이 빠른 작업 우선 처리, 최적의 스케줄링 보장

#### 시나리오 B: 프로세스 타임라인 분석

**실행 방법**: `python visualize_timeline.py`

**목적**: 각 프로세스의 상태 변화(Ready → Running → Waiting)를 시각적으로 분석

**분석 내용**:
- 프로세스가 Ready 상태에서 얼마나 대기했는지
- CPU를 얼마나 효율적으로 사용했는지
- I/O 대기 시간이 전체 실행 시간에 미치는 영향
- 선점이 발생하는 시점과 빈도

### 3.2. 동기화 문제 시나리오 (SYNC 모드)

#### 시나리오 1: 우선순위 역전 (Priority Inversion)

**실행 방법**: `python main.py` → `[2] SYNC` → `[1] 고전적 동기화 문제`

**입력 파일**: `producer_consumer.txt`
```
3
1,0,5,LOCK:R1,CPU:10,UNLOCK:R1
2,3,1,LOCK:R1,CPU:5,UNLOCK:R1
3,2,3,CPU:8
```

**알고리즘**: 정적 우선순위 (SimulatorPriorityStatic)

**시나리오 설명**:
1. **t=0**: P1 (우선순위 5, 낮음) 도착
   - R1 Lock 획득
   - CPU 작업 시작
2. **t=2**: P3 (우선순위 3, 중간) 도착
   - P1보다 우선순위가 높아 P1을 선점
   - CPU 작업 수행
3. **t=3**: P2 (우선순위 1, 가장 높음) 도착
   - R1 Lock 시도 → 실패 (P1이 보유 중)
   - Waiting 상태로 전환

**문제점**: 
- P2 (최고 우선순위)가 P1 (최저 우선순위)이 보유한 자원을 기다림
- 하지만 P1은 P3 (중간 우선순위)에게 선점당해 실행되지 못함
- 결과적으로 P2가 P3보다 낮은 우선순위처럼 동작하는 **우선순위 역전** 발생

**관찰 포인트**:
- 간트 차트에서 P2가 긴 시간 동안 대기하는 것을 확인
- P3가 P1보다 먼저 종료되는 것을 확인
- 로그에서 "P2 자원 R1 대기 중" 메시지 확인

#### 시나리오 2: 교착상태 예방 (Deadlock Prevention)

**실행 방법**: `python main.py` → `[2] SYNC` → `[2] 교착상태 예방`

**입력 파일**: `deadlock_prevention.txt`
```
2
1,0,1,LOCK:R1,CPU:5,LOCK:R2,CPU:5,UNLOCK:R2,UNLOCK:R1
2,0,1,LOCK:R2,CPU:5,LOCK:R1,CPU:5,UNLOCK:R1,UNLOCK:R2
```

**알고리즘**: 정적 우선순위 (SimulatorPriorityStatic)

**예방 기법**: 자원 순서 할당 (Resource Ordering)
- 모든 자원에 고유 ID 부여 (R1=0, R2=1)
- 프로세스는 반드시 ID가 증가하는 순서로만 자원 요청 가능
- 규칙 위반 시 프로세스 강제 종료

**시나리오 설명**:
1. **P1의 동작**:
   - LOCK:R1 (ID 0) → 성공
   - LOCK:R2 (ID 1) → 성공 (올바른 순서)
   - 정상 실행 및 종료
2. **P2의 동작**:
   - LOCK:R2 (ID 1) → 성공
   - LOCK:R1 (ID 0) → **규칙 위반 감지**
   - 시스템이 P2를 강제 종료하고 R2 반납

**예상 결과**:
- P1은 정상적으로 완료
- P2는 "교착상태 예방: P2가 R2(ID: 1)를 보유한 상태에서 R1(ID: 0)을 순서 없이 요청함. 프로세스 강제 종료." 메시지와 함께 종료
- 교착상태가 발생하지 않음

#### 시나리오 3: 교착상태 회피 (Deadlock Avoidance)

**실행 방법**: `python main.py` → `[2] SYNC` → `[3] 교착상태 회피`

**입력 파일**: `deadlock_avoidance.txt`

**알고리즘**: 정적 우선순위 (SimulatorPriorityStatic)

**회피 기법**: Banker's Algorithm
- 프로세스가 자원을 요청할 때 시스템이 안전 상태를 유지하는지 검사
- 불안전 상태가 예상되면 자원 할당을 거부하고 프로세스를 대기시킴

**측정 내용**:
- 안전 상태 검사 횟수
- 자원 요청 거부 횟수
- 모든 프로세스의 정상 완료 여부

#### 시나리오 4: 교착상태 탐지 및 복구 (Deadlock Detection & Recovery)

**실행 방법**: `python main.py` → `[2] SYNC` → `[4] 교착상태 탐지`

**입력 파일**: `deadlock_detection.txt`

**알고리즘**: 정적 우선순위 (SimulatorPriorityStatic)

**탐지 기법**: 자원 할당 그래프 (Resource Allocation Graph) 순환 검사
- 주기적으로 자원 할당 상태를 분석하여 순환 대기 감지
- 교착상태 발견 시 희생자 프로세스 선택 및 종료

**복구 전략**:
- 교착상태에 연루된 프로세스 중 하나를 선택하여 강제 종료
- 종료된 프로세스가 보유한 모든 자원을 반납
- 대기 중인 다른 프로세스들이 진행할 수 있도록 함

### 3.3. 실시간 스케줄링 시나리오

#### 시나리오 5: RM vs EDF 비교

**실행 방법**: `python main.py` → `[1] PERFORMANCE`

**실시간 프로세스 구성**:
- P101: period=37ms, deadline=34ms, execution=12ms
- P102: period=43ms, deadline=40ms, execution=15ms

**비교 항목**:
1. **스케줄 가능성 (Schedulability)**:
   - RM: U = 12/37 + 15/43 ≈ 0.673 < 0.693 (2개 프로세스의 RM 한계)
   - EDF: U = 12/34 + 15/40 ≈ 0.728 < 1.0 (EDF 한계)
   - 두 알고리즘 모두 이론적으로 스케줄 가능

2. **마감시한 초과 횟수**:
   - RM: 정적 우선순위로 인해 특정 상황에서 마감시한 초과 가능
   - EDF: 동적 우선순위로 최적의 스케줄링 보장

3. **평균 반환 시간**:
   - 두 알고리즘의 평균 반환 시간 비교

**예상 결과**:
- EDF가 RM보다 마감시한 초과가 적거나 없음
- EDF의 문맥 교환이 RM보다 약간 많을 수 있음
- 두 알고리즘 모두 높은 CPU 사용률 (90% 이상) 달성

---

## 4. 프로젝트 구조

```
os_project/
├── main.py                          # 메인 실행 파일
├── gui_selector.py                  # GUI 알고리즘 선택기
├── visualize_timeline.py            # 타임라인 전용 시각화
├── process.py                       # 프로세스 클래스 정의
├── generator.py                     # 랜덤 워크로드 생성기
├── visualizer.py                    # 시각화 모듈
├── sync.py                          # 동기화 및 자원 관리
├── simulator_fcfs.py                # FCFS 스케줄러
├── simulator_rr.py                  # Round Robin 스케줄러
├── simulator_sjf.py                 # SJF 스케줄러
├── simulator_priority_static.py     # 정적 우선순위 스케줄러
├── simulator_priority_dynamic.py    # 동적 우선순위 스케줄러
├── simulator_mlfq.py                # MLFQ 스케줄러
├── simulator_rm.py                  # RM 실시간 스케줄러
├── simulator_edf.py                 # EDF 실시간 스케줄러
├── random_input.txt                 # 샘플 입력 파일
├── producer_consumer.txt            # 우선순위 역전 시나리오
├── deadlock_prevention.txt          # 교착상태 예방 시나리오
├── deadlock_avoidance.txt           # 교착상태 회피 시나리오
├── deadlock_detection.txt           # 교착상태 탐지 시나리오
└── deadlock_recovery.txt            # 교착상태 복구 시나리오
```

---

## 5. 참고 사항

- 모든 시뮬레이션은 시간 단위(tick) 기반으로 동작합니다.
- 문맥 교환 오버헤드는 1ms로 설정되어 있습니다 (실시간 알고리즘 제외).
- 시각화 결과는 matplotlib 창으로 표시되며, 창을 닫으면 다음 시각화로 진행됩니다.
- 자세한 실행 로그는 콘솔에 출력됩니다.
