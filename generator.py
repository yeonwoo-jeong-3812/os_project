import random
from process import Process # process.py의 Process 클래스를 가져옵니다.

def generate_random_processes(
    num_processes=10, 
    max_arrival_time=50, 
    max_cpu_burst=20, 
    max_io_burst=30, 
    max_priority=5, 
    io_probability=0.7
    ):
    """
    (수정됨) "CPU:X, IO:Y" 형식의 랜덤 프로세스 리스트를 생성합니다.
    (비-실시간 알고리즘 테스트용)
    """
    processes = []
    print(f"--- 랜덤 프로세스 {num_processes}개 생성 시작 ---")
    
    for i in range(num_processes):
        pid = i + 1
        arrival_time = random.randint(0, max_arrival_time)
        priority = random.randint(1, max_priority)
        
        burst_list_str = []
        
        # 1. 첫 번째 CPU 버스트
        cpu_burst = random.randint(1, max_cpu_burst)
        burst_list_str.append(f"CPU:{cpu_burst}")
        
        # 2. I/O Bound 프로세스를 위한 추가 버스트 생성
        while random.random() < io_probability:
            io_burst = random.randint(1, max_io_burst)
            cpu_burst = random.randint(1, max_cpu_burst)
            
            burst_list_str.append(f"IO:{io_burst}")
            burst_list_str.append(f"CPU:{cpu_burst}")
            
            if len(burst_list_str) > 10: # 최대 5쌍
                break
                
        # "CPU:3,IO:10,CPU:4" 형태의 문자열로 변환
        burst_pattern_str = ",".join(burst_list_str)
        
        proc = Process(pid, arrival_time, priority, burst_pattern_str, 0, 0)
        processes.append(proc)
        
        print(f"  P{pid}: 도착={arrival_time}, 우선순위={priority}, 패턴=\"{burst_pattern_str}\"")

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
    max_period=50
    ):
    """
    (새 함수) RM/EDF 테스트를 위한 랜덤 실시간 프로세스를 생성합니다.
    - 주기(Period)와 마감시한(Deadline)을 동일하게 설정합니다.
    - CPU 버스트는 주기보다 짧도록 보장합니다.
    """
    processes = []
    print(f"--- 랜덤 실시간 프로세스 {num_processes}개 생성 시작 ---")
    
    # (PID는 일반 프로세스와 겹치지 않게 101부터 시작)
    for i in range(num_processes):
        pid = i + 101 
        arrival_time = random.randint(0, max_arrival_time)
        
        # 주기/마감시한 (10 ~ max_period)
        period = random.randint(10, max_period)
        deadline = period
        
        # CPU 버스트 (주기보다 짧아야 함)
        cpu_burst = random.randint(2, max(3, int(period / 3)))
        burst_pattern_str = f"CPU:{cpu_burst}"
        
        # (우선순위는 RM/EDF에서 사용 안 함, 0으로 설정)
        proc = Process(pid, arrival_time, 0, burst_pattern_str, period, deadline)
        processes.append(proc)
        
        print(f"  P{pid} (실시간): 도착={arrival_time}, 패턴=\"{burst_pattern_str}\", 주기={period}")

    print("--- 랜덤 실시간 프로세스 생성 완료 ---")
    return processes


# --- 이 파일을 직접 실행할 경우 테스트 ---
if __name__ == "__main__":
    """
    'python generator.py'를 실행하면 
    랜덤 프로세스 7개를 생성하여 'random_input.txt' 파일로 저장합니다.
    """
    test_processes = generate_random_processes(
        num_processes=7, 
        max_arrival_time=20, 
        io_probability=0.5 # 50% 확률로 I/O 추가
    )
    
    save_processes_to_file(test_processes, "random_input.txt")