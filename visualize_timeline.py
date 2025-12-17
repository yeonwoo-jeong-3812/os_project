"""
프로세스 상태 타임라인 시각화 전용 스크립트
각 스케줄링 알고리즘의 프로세스 상태 변화를 시각화합니다.
"""

from visualizer import SchedulingVisualizer
from simulator_fcfs import SimulatorFCFS
from simulator_rr import SimulatorRR
from simulator_sjf import SimulatorSJF
from simulator_priority_static import SimulatorPriorityStatic
from simulator_priority_dynamic import SimulatorPriorityDynamic
from simulator_mlfq import SimulatorMLFQ
from simulator_rm import SimulatorRM
from simulator_edf import SimulatorEDF
from generator import generate_random_processes
import copy

print("=" * 70)
print("프로세스 상태 타임라인 시각화")
print("=" * 70)

# 워크로드 생성
print("\n워크로드 생성 중...")

# 일반 프로세스 생성
general_processes = generate_random_processes(
    num_processes=6,
    arrival_lambda=2.0,
    max_cpu_burst=20,
    max_io_burst=10,
    workload_distribution={'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
)

# 실시간 프로세스 생성 (수동으로 생성)
from process import Process
realtime_processes = [
    Process(101, 0, 0, "CPU:5,IO:3,CPU:4", period=23, deadline=20),
    Process(102, 0, 0, "CPU:8,IO:5,CPU:2", period=31, deadline=28)
]

processes = general_processes + realtime_processes
print(f"✓ 총 {len(processes)}개 프로세스 생성 완료 (일반: {len(general_processes)}개, 실시간: {len(realtime_processes)}개)")

# Visualizer 초기화
visualizer = SchedulingVisualizer()

# 각 알고리즘별 시뮬레이션 및 타임라인 시각화
algorithms = [
    ("FCFS", SimulatorFCFS, {}, False),
    ("RR (Q=4)", SimulatorRR, {"time_quantum": 4}, False),
    ("SJF (Preemptive)", SimulatorSJF, {}, False),
    ("Priority (Static)", SimulatorPriorityStatic, {}, False),
    ("Priority (Aging)", SimulatorPriorityDynamic, {"aging_factor": 10}, False),
    ("MLFQ", SimulatorMLFQ, {}, False),
    ("RM (Rate Monotonic)", SimulatorRM, {}, True),
    ("EDF (Earliest Deadline First)", SimulatorEDF, {}, True)
]

print("\n" + "=" * 70)
print("시뮬레이션 실행 및 타임라인 시각화")
print("=" * 70)

for i, (name, SimulatorClass, kwargs, is_realtime) in enumerate(algorithms, 1):
    print(f"\n[{i}/{len(algorithms)}] {name}...")
    
    # 실시간 알고리즘은 실시간 프로세스만, 일반 알고리즘은 일반 프로세스만 필터링
    if is_realtime:
        procs = [p for p in copy.deepcopy(processes) if p.period > 0]
    else:
        procs = [p for p in copy.deepcopy(processes) if p.period == 0]
    
    if not procs:
        print(f"   ⚠️ {name}에 적합한 프로세스가 없습니다. 건너뜁니다.")
        continue
    
    # 시뮬레이션 실행
    simulator = SimulatorClass(procs, **kwargs)
    simulator.run()
    
    # 타임라인 시각화
    print(f"   타임라인 시각화 중...")
    visualizer.visualize_process_state_timeline(
        simulator.completed_processes, 
        name
    )
    print(f"   ✓ {name} 완료")

print("\n" + "=" * 70)
print("✅ 모든 타임라인 시각화 완료!")
print("=" * 70)
print("\n타임라인 범례:")
print("  🟧 Ready (주황색)   - 프로세스가 CPU를 기다리는 상태")
print("  🟦 Running (청록색) - 프로세스가 CPU를 사용하는 상태")
print("  🟨 Waiting (노란색) - 프로세스가 I/O를 기다리는 상태")
print("  🟢 도착 (녹색 점)  - 프로세스 도착 시간")
print("  🔴 종료 (빨간 점)  - 프로세스 종료 시간")
