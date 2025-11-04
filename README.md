# 💻 운영체제 CPU 스케줄링 시뮬레이터 (OS Scheduler Simulator)

## 1️⃣ 프로젝트 개요 (Project Overview)

* [cite_start]**프로젝트 명:** 운영체제 CPU 스케줄링 시뮬레이터 [cite: 182]
* [cite_start]**개발 목적:** 다양한 CPU 스케줄링 알고리즘을 타임 유닛 기반으로 시뮬레이션하고, 동일한 프로세스 워크로드에 대한 성능 지표를 측정 및 정량적으로 분석하는 것을 목표로 합니다. [cite: 185]
* [cite_start]**주요 기능 요약:** FCFS, SRTF, RR, 정적/동적 우선순위, MLFQ, RM, EDF 총 9가지 핵심 스케줄링 알고리즘을 구현하고 성능을 비교 분석합니다. [cite: 188, 189]

---

## 2️⃣ 개발 환경 및 실행 방법 (Development Environment & Run Guide)

* [cite_start]**개발 언어 및 환경:** Python [cite: 187]
* **주요 라이브러리:** `collections` (deque), `heapq` (최소 힙), `matplotlib` (시각화)
* **프로그램 실행 방법:**
    ```bash
    # 예시: 시뮬레이터 실행 (입력 데이터 포함)
    python scheduler_simulator.py process_data.txt 
    ```
* **결과 출력 형태:**
    * 콘솔 로그: 프로세스의 상태 변화(생성, 실행, 대기, 종료) 로그 출력.
    * 그래프/차트: 각 알고리즘별 **CPU 할당 흐름 간트 차트** 및 **프로세스 타임라인** 출력. 
    * 표: 최종 산출된 성능 지표 비교 통계표 출력.

---

## 3️⃣ 구현 알고리즘 (Implemented Scheduling Algorithms)

| 알고리즘 | 스케줄링 원칙 | Ready 큐 데이터 구조 | 선점(Preemption) 여부 | 특징 |
| :--- | :--- | :--- | :--- | :--- |
| **FCFS** | 도착 순서 | `collections.deque` (FIFO) | X (비선점) | [cite_start]비선점 방식 구현. [cite: 240] |
| **SJF (SRTF)** | 남은 시간 최소 | 최소 힙 (기준: 남은 CPU 시간) | O | [cite_start]매 틱마다 잔여 시간 비교하여 선점. [cite: 249] |
| **RR** | 타임 슬라이스(4ms) 순환 | `collections.deque` (FIFO) | O (타이머 인터럽트) | [cite_start]Time Quantum은 **4ms**로 설정. [cite: 261] |
| **동적 우선순위** | Aging 적용 | 일반 리스트 | O (우선순위 인터럽트) | [cite_start]`새 우선순위 = 기존 우선순위 - (대기 시간 / 10)` 공식 적용. [cite: 280, 281] |
| **MLFQ** | 3단계 큐 (Q1 > Q2 > Q3) | 3개 `deque` | O (상위 큐 도착 시) | Q1(RR-8), Q2(RR-16), Q3(FCFS) 구성. [cite_start]I/O 완료 시 Q1으로 복귀. [cite: 289, 292] |
| **RM** | 주기 최소 | 최소 힙 (기준: Period) | O | [cite_start]주기가 짧을수록 높은 우선순위. [cite: 304] |
| **EDF** | 마감시한 최소 | 최소 힙 (기준: Absolute Deadline) | O | [cite_start]마감시한이 빠를수록 높은 우선순위 (동적). [cite: 308, 309] |

---

## 4️⃣ 주요 클래스 및 구조 (Core Classes & Structure)

* **`Process` 클래스 (PCB 역할):**
    * [cite_start]**필수 속성:** `PID`, `Arrival Time`, `Static Priority`, `Dynamic Priority`, `실행 패턴`, `Period`, `Deadline` 포함. [cite: 193, 194]
    * [cite_start]**핵심 필드:** 선점형 스케줄링을 위한 `remaining_cpu_time` 관리. [cite: 195]
* **프로세스 상태 전이:**
    * [cite_start]**상태:** Ready, Running, Waiting, Terminated 상태 전이 정확히 구현. [cite: 195]
    * [cite_start]**주요 전이 조건:** Dispatch, I/O Wait, **Preemption (선점/타이머 인터럽트)**, I/O Complete 등 구현. [cite: 215, 216, 217]

---

## 5️⃣ 입력 데이터 구조 (Input Dataset)

* [cite_start]**데이터 셋:** CPU Bound, I/O Bound, 우선순위, 실시간 프로세스가 혼합된 **7개의 프로세스 (P1~P7)** 데이터 셋 사용. [cite: 190]
* **구성 의도:** Aging 테스트용 장기 프로세스(P4), 실시간 테스트용 프로세스(P5, P6) 등이 포함됨.
* **입력 포맷 (예시):**
    ```
    # 형식: PID, 생성시간, 우선순위, 실행패턴, [주기, 마감시한]
    [cite_start]1, 7, 5, "6,23,8", 0, 0     # P1 (랜덤 생성 예시) [cite: 225]
    [cite_start]4, 3, 2, "4,3,11", 0, 0     # P4 (랜덤 생성 예시) [cite: 229, 230]
    [cite_start]5, 20, 3, "1,20,9", 0, 0    # P5 (랜덤 생성 예시) [cite: 231]
    ```

---

## 6️⃣ 성능 비교 및 결과 (Performance Comparison)

| 지표 | 공식 및 설명 |
| :--- | :--- |
| **CPU 사용률 (Util)** | [cite_start]$\text{CPU Utilization} = \frac{\text{CPU 총 사용 시간 (총 CPU 버스트 시간)}}{\text{시뮬레이션 총 경과 시간 (Total Time)}}$ [cite: 314] |

### [cite_start]결과 요약표 (P1~P7 워크로드) [cite: 317]

| 알고리즘 | Avg WT (ms) | Avg TT (ms) | CPU 사용률 (%) | 문맥 전환 횟수 |
| :--- | :--- | :--- | :--- | :--- |
| **SJF (SRTF)** | **35.80** | **56.20** | 98.20 | 18 |
| FCFS | 56.40 | 76.80 | 98.20 | 11 |
| RR (Q=4) | 48.10 | 68.50 | 98.20 | **35** |
| 동적 우선순위 (Aging) | 40.50 | 60.90 | 98.20 | 16 |
| MLFQ | 45.70 | 66.10 | 98.20 | 25 |
| **RM / EDF** | **0.00** | **11.00** | **44.00** | **0** |

---

## 7️⃣ 분석 및 논의 (Analysis & Discussion)

* [cite_start]**최고 효율:** **SRTF**가 평균 대기/반환 시간 모두에서 가장 우수한 성능을 보였습니다. [cite: 320, 321]
* [cite_start]**최대 오버헤드:** **RR (Q=4)**은 문맥 전환 횟수가 **35회**로 가장 많았습니다. [cite: 322]
* [cite_start]**Aging의 효과:** 동적 우선순위(40.50ms)의 평균 대기 시간이 감소하여, P4와 같은 장기 프로세스의 대기 시간을 개선했음을 입증했습니다. [cite: 324, 325]
* [cite_start]**실시간 스케줄링:** RM과 EDF 모두 주어진 워크로드에 대해 마감시한 초과 횟수 **0회**를 기록하며 안정적으로 제약 조건을 만족했습니다. [cite: 329]

---

## 8️⃣ 결론 및 개선 방향 (Conclusion & Future Work)

* [cite_start]**구현 완성도 요약:** 요구된 9가지 알고리즘과 핵심 기능을 정교하게 구현하는 데 성공했습니다. [cite: 333, 336]
* **발견된 한계:**
    1.  [cite_start]**단일 워크로드 한계:** 정적인 단일 워크로드(P1~P7)에 기반하여 검증에 제한적입니다. [cite: 341]
    2.  [cite_start]**오버헤드 정교화 부족:** 문맥 전환에 소요되는 **시간 오버헤드를 정량적으로 반영하지 않았습니다**. [cite: 344]
* **향후 개선 계획:**
    1.  [cite_start]**워크로드 다양화:** 랜덤 프로세스 생성기를 추가하여 부하 변화에 따른 알고리즘의 견고성을 검증할 예정입니다. [cite: 343]
    2.  [cite_start]**오버헤드 반영:** 문맥 전환 시 미세한 시간 비용을 스케줄러 로직에 추가하여 성능 지표에 미치는 영향을 더욱 정교하게 분석할 계획입니다. [cite: 346]

---

이 마크다운 코드를 사용하여 깔끔하고 전문적인 README를 완성하시기 바랍니다.

혹시 코드 블록 내의 내용 중 추가적인 수정이나 보완이 필요하신가요?
