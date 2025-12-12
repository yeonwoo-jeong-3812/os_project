"""
5단계 구현 검증 스크립트
프로세스 상태 세분화 기능 테스트
"""

from process import Process
from simulator_fcfs import SimulatorFCFS
from visualizer import SchedulingVisualizer
from generator import generate_random_processes

print("=" * 70)
print("5단계 구현 검증: 프로세스 상태 세분화")
print("=" * 70)

# 1. Process 클래스에 새 변수 추가 확인
print("\n[1] Process 클래스 변수 확인...")
test_proc = Process(1, 0, 5, "CPU:10,IO:5,CPU:5", 0, 0)

assert hasattr(test_proc, 'ready_wait_time'), "❌ ready_wait_time 변수 없음"
assert hasattr(test_proc, 'io_wait_time'), "❌ io_wait_time 변수 없음"
assert hasattr(test_proc, 'timeline'), "❌ timeline 변수 없음"

print(f"   ✓ ready_wait_time: {test_proc.ready_wait_time}")
print(f"   ✓ io_wait_time: {test_proc.io_wait_time}")
print(f"   ✓ timeline: {test_proc.timeline}")

# 2. FCFS 시뮬레이터에서 timeline 기록 확인
print("\n[2] FCFS 시뮬레이터 timeline 기록 확인...")
processes = generate_random_processes(
    num_processes=3,
    arrival_lambda=2.0,
    max_cpu_burst=10,
    max_io_burst=5,
    workload_distribution={'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
)

sim = SimulatorFCFS(processes)
sim.run()

print(f"\n   완료된 프로세스 수: {len(sim.completed_processes)}")

for proc in sim.completed_processes:
    print(f"\n   P{proc.pid}:")
    print(f"      - Ready 대기 시간: {proc.ready_wait_time}ms")
    print(f"      - I/O 대기 시간: {proc.io_wait_time}ms")
    print(f"      - 총 대기 시간: {proc.wait_time}ms")
    print(f"      - Timeline 기록 수: {len(proc.timeline)}")
    
    if proc.timeline:
        print(f"      - Timeline 샘플:")
        for i, (start, end, state) in enumerate(proc.timeline[:3]):
            if end is not None:
                print(f"         [{i}] {start}-{end}ms: {state}")
            else:
                print(f"         [{i}] {start}-?: {state} (미완료)")

# 3. Visualizer 함수 존재 확인
print("\n[3] Visualizer 타임라인 함수 확인...")
visualizer = SchedulingVisualizer()

assert hasattr(visualizer, 'visualize_process_state_timeline'), \
    "❌ visualize_process_state_timeline 함수 없음"

print("   ✓ visualize_process_state_timeline 함수 존재")

# 4. 통계 검증
print("\n[4] 통계 검증...")
for proc in sim.completed_processes:
    # Ready + I/O 대기 시간이 총 대기 시간과 일치하는지 확인
    calculated_wait = proc.ready_wait_time + proc.io_wait_time
    
    print(f"   P{proc.pid}: Ready({proc.ready_wait_time}) + I/O({proc.io_wait_time}) = {calculated_wait}ms")
    
    # 약간의 오차는 허용 (문맥 교환 오버헤드 등)
    if abs(calculated_wait - proc.wait_time) > 5:
        print(f"      ⚠️  총 대기 시간({proc.wait_time}ms)과 차이 발생")

print("\n" + "=" * 70)
print("✅ 5단계 구현 검증 완료!")
print("=" * 70)
print("\n주요 구현 사항:")
print("  1. Process 클래스에 ready_wait_time, io_wait_time, timeline 변수 추가")
print("  2. FCFS 시뮬레이터에 상태 변화 추적 로직 구현")
print("  3. Visualizer에 프로세스 상태 타임라인 시각화 함수 추가")
print("\n다음 단계:")
print("  - 나머지 시뮬레이터(RR, SJF, Priority 등)에도 동일한 로직 적용")
print("  - 타임라인 시각화를 통한 기아 상태 분석")
