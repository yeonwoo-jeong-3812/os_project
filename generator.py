import random
import numpy as np
from process import Process # process.py의 Process 클래스를 가져옵니다.

def generate_random_processes(
    num_processes=10,
    arrival_lambda=5.0,  # 지수 분포의 람다 값 (평균 도착 간격)
    max_cpu_burst=20,
    max_io_burst=30,
    max_priority=5,
    workload_distribution=None
    ):
    """
    [고도화 버전] 워크로드 타입을 구분하여 현실적인 프로세스를 생성합니다.
    
    Args:
        num_processes: 생성할 프로세스 개수
        arrival_lambda: 지수 분포 람다 값 (값이 클수록 도착 간격이 짧음)
        max_cpu_burst: 최대 CPU 버스트 시간
        max_io_burst: 최대 I/O 버스트 시간
        max_priority: 최대 우선순위 값
        workload_distribution: 워크로드 타입 비율 {'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
    
    워크로드 타입:
        - CPU Bound: 긴 CPU 버스트, 적은 I/O (연산 집약적)
        - I/O Bound: 짧은 CPU 버스트, 잦은 I/O (입출력 집약적)
        - Mixed: 중간 형태
    """
    if workload_distribution is None:
        workload_distribution = {'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
    
    processes = []
    print(f"--- 랜덤 프로세스 {num_processes}개 생성 시작 (고도화 버전) ---")
    print(f"워크로드 분포: CPU Bound {workload_distribution['cpu_bound']*100:.0f}%, "
          f"I/O Bound {workload_distribution['io_bound']*100:.0f}%, "
          f"Mixed {workload_distribution['mixed']*100:.0f}%")
    
    # 워크로드 타입 리스트 생성
    workload_types = []
    workload_types.extend(['cpu_bound'] * int(num_processes * workload_distribution['cpu_bound']))
    workload_types.extend(['io_bound'] * int(num_processes * workload_distribution['io_bound']))
    workload_types.extend(['mixed'] * int(num_processes * workload_distribution['mixed']))
    
    # 부족한 개수는 mixed로 채움
    while len(workload_types) < num_processes:
        workload_types.append('mixed')
    
    # 랜덤 섞기
    random.shuffle(workload_types)
    
    # 지수 분포로 도착 시간 생성
    arrival_times = [0]  # 첫 프로세스는 시간 0에 도착
    for i in range(1, num_processes):
        # 지수 분포로 도착 간격 생성
        interval = np.random.exponential(1.0 / arrival_lambda)
        arrival_times.append(int(arrival_times[-1] + interval))
    
    for i in range(num_processes):
        pid = i + 1
        arrival_time = arrival_times[i]
        priority = random.randint(1, max_priority)
        workload_type = workload_types[i]
        
        burst_list_str = []
        
        # 워크로드 타입에 따른 버스트 패턴 생성
        if workload_type == 'cpu_bound':
            # CPU Bound: 긴 CPU 버스트, 적은 I/O
            cpu_burst = random.randint(max_cpu_burst // 2, max_cpu_burst)
            burst_list_str.append(f"CPU:{cpu_burst}")
            
            # 10% 확률로 I/O 추가 (최대 1~2회)
            for _ in range(random.randint(0, 2)):
                if random.random() < 0.1:
                    io_burst = random.randint(1, max_io_burst // 3)
                    cpu_burst = random.randint(max_cpu_burst // 2, max_cpu_burst)
                    burst_list_str.append(f"IO:{io_burst}")
                    burst_list_str.append(f"CPU:{cpu_burst}")
        
        elif workload_type == 'io_bound':
            # I/O Bound: 짧은 CPU 버스트, 잦은 I/O
            cpu_burst = random.randint(1, max_cpu_burst // 3)
            burst_list_str.append(f"CPU:{cpu_burst}")
            
            # 80% 확률로 I/O 추가 (최대 3~5회)
            for _ in range(random.randint(3, 5)):
                if random.random() < 0.8:
                    io_burst = random.randint(max_io_burst // 2, max_io_burst)
                    cpu_burst = random.randint(1, max_cpu_burst // 3)
                    burst_list_str.append(f"IO:{io_burst}")
                    burst_list_str.append(f"CPU:{cpu_burst}")
        
        else:  # mixed
            # Mixed: 중간 형태
            cpu_burst = random.randint(max_cpu_burst // 4, max_cpu_burst // 2)
            burst_list_str.append(f"CPU:{cpu_burst}")
            
            # 50% 확률로 I/O 추가 (최대 2~3회)
            for _ in range(random.randint(2, 3)):
                if random.random() < 0.5:
                    io_burst = random.randint(max_io_burst // 3, max_io_burst // 2)
                    cpu_burst = random.randint(max_cpu_burst // 4, max_cpu_burst // 2)
                    burst_list_str.append(f"IO:{io_burst}")
                    burst_list_str.append(f"CPU:{cpu_burst}")
        
        # "CPU:3,IO:10,CPU:4" 형태의 문자열로 변환
        burst_pattern_str = ",".join(burst_list_str)
        
        proc = Process(pid, arrival_time, priority, burst_pattern_str, 0, 0)
        processes.append(proc)
        
        # 워크로드 타입 표시
        type_label = {'cpu_bound': 'CPU집약', 'io_bound': 'I/O집약', 'mixed': '혼합형'}[workload_type]
        print(f"  P{pid}: 도착={arrival_time:3d}, 우선순위={priority}, 타입=[{type_label}], 패턴=\"{burst_pattern_str}\"")

    print("--- 랜덤 프로세스 생성 완료 ---")
    return processes

def save_processes_to_file(processes, filename="random_input.txt"):
    """
    생성된 프로세스 리스트를 입력 파일 형식으로 저장합니다.
    """
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            f.write("# OS Scheduler Project - Randomly Generated Input Data\n")
            f.write("# 형식: PID,생성시간,우선순위,실행패턴,[주기,마감시한]\n")
            f.write("# --------------------------------------------------\n")
            
            for proc in processes:
                # Process 객체에서 burst_pattern 리스트를 다시 문자열로
                burst_str = ",".join(f"{cmd}:{val}" for cmd, val in proc.burst_pattern)
                
                line = f'{proc.pid},{proc.arrival_time},{proc.static_priority},"{burst_str}",{proc.period},{proc.deadline}\n'
                f.write(line)
        
        print(f"\n✅ 랜덤 생성된 프로세스를 '{filename}' 파일로 저장했습니다.")
        
    except Exception as e:
        print(f"\n❌ 파일 저장 중 오류 발생: {e}")

def generate_random_realtime_processes(
    num_processes=4, 
    max_arrival_time=10, 
    target_utilization=0.85
    ):
    """
    (개선된 함수) RM/EDF 테스트를 위한 랜덤 실시간 프로세스를 생성합니다.
    - CPU 이용률을 목표치(target_utilization)에 맞춰 생성합니다.
    - RM의 이론적 한계(약 0.69)와 1.0 사이의 이용률을 설정하면 RM은 실패하고 EDF는 성공하는 시나리오를 만들 수 있습니다.
    - 주기를 서로 소(coprime) 관계로 설정하여 충돌을 유도합니다.
    """
    processes = []
    print(f"--- 랜덤 실시간 프로세스 {num_processes}개 생성 시작 (목표 이용률: {target_utilization:.2f}) ---")
    
    # 서로 소인 주기 후보 (충돌 유도)
    coprime_periods = [17, 23, 29, 31, 37, 41, 43, 47]  # 소수들
    random.shuffle(coprime_periods)
    
    # 각 프로세스의 이용률 (C/T)을 균등하게 분배
    individual_utilization = target_utilization / num_processes
    
    # (PID는 일반 프로세스와 겹치지 않게 101부터 시작)
    for i in range(num_processes):
        pid = i + 101 
        arrival_time = random.randint(0, max_arrival_time)
        
        # 주기 선택 (서로 소인 값들 중에서)
        if i < len(coprime_periods):
            period = coprime_periods[i]
        else:
            # 후보가 부족하면 랜덤 소수 생성
            period = random.choice([19, 37, 53])
        
        deadline = period
        
        # CPU 버스트 = 주기 × 개별 이용률
        # 약간의 랜덤성 추가 (±10%)
        cpu_burst = int(period * individual_utilization * random.uniform(0.9, 1.1))
        cpu_burst = max(2, min(cpu_burst, period - 1))  # 최소 2, 최대 period-1
        
        burst_pattern_str = f"CPU:{cpu_burst}"
        
        # (우선순위는 RM/EDF에서 사용 안 함, 0으로 설정)
        proc = Process(pid, arrival_time, 0, burst_pattern_str, period, deadline)
        processes.append(proc)
        
        utilization = cpu_burst / period
        print(f"  P{pid} (실시간): 도착={arrival_time}, 패턴=\"{burst_pattern_str}\", 주기={period}, 이용률={utilization:.2f}")

    # 실제 총 이용률 계산
    total_utilization = sum(
        sum(val for cmd, val in p.burst_pattern if cmd == 'CPU') / p.period 
        for p in processes
    )
    print(f"--- 실제 총 CPU 이용률: {total_utilization:.2f} ---")
    print(f"--- RM 이론적 한계: {num_processes * (2**(1/num_processes) - 1):.2f} ---")
    
    if total_utilization > num_processes * (2**(1/num_processes) - 1):
        print("⚠️  RM 이론적 한계 초과 - RM은 실패할 가능성이 있습니다!")
    
    print("--- 랜덤 실시간 프로세스 생성 완료 ---")
    return processes


# --- 이 파일을 직접 실행할 경우 테스트 ---
if __name__ == "__main__":
    """
    'python generator.py'를 실행하면 
    랜덤 프로세스를 생성하여 'random_input.txt' 파일로 저장합니다.
    """
    print("\n=== 고도화된 워크로드 생성기 테스트 ===")
    
    test_processes = generate_random_processes(
        num_processes=10,
        arrival_lambda=3.0,  # 평균 3ms 간격으로 도착
        max_cpu_burst=20,
        max_io_burst=30,
        workload_distribution={'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
    )
    
    save_processes_to_file(test_processes, "random_input.txt")
    
    # 통계 출력
    print("\n=== 생성된 워크로드 통계 ===")
    total_cpu = sum(sum(val for cmd, val in p.burst_pattern if cmd == 'CPU') for p in test_processes)
    total_io = sum(sum(val for cmd, val in p.burst_pattern if cmd == 'IO') for p in test_processes)
    print(f"총 CPU 버스트 시간: {total_cpu}ms")
    print(f"총 I/O 버스트 시간: {total_io}ms")
    print(f"CPU/IO 비율: {total_cpu/(total_io+1):.2f}")