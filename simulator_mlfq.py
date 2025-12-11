import collections
import heapq 
from process import Process, parse_input_file
from sync import get_resource

# 👇👇👇 2. 클래스 이름이 'SimulatorMLFQ'인지 확인!
class SimulatorMLFQ:
    """
    다단계 피드백 큐 (Multi-Level Feedback Queue) 시뮬레이터
    - Q1: RR (Quantum=8)
    - Q2: RR (Quantum=16)
    - Q3: FCFS
    """
    # 👇👇👇 2. __init__ 메소드도 3개의 큐가 있는지 확인!
    def __init__(self, process_list, context_switch_overhead=1):
        self.processes_to_arrive = []
        for proc in process_list:
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # --- 1. 3개의 Ready 큐 ---
        self.ready_queue_q1 = collections.deque() # 최상위: RR (Q=8)
        self.ready_queue_q2 = collections.deque() # 중간: RR (Q=16)
        self.ready_queue_q3 = collections.deque() # 최하위: FCFS
        
        self.waiting_queue = []
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 
        
        # [문맥 전환 횟수 추가]
        self.context_switches = 0
        self.context_switch_overhead = context_switch_overhead
        self.total_overhead_time = 0
        self.cpu_was_idle = True
        self.overhead_remaining = 0
        
        # [큐 상태 로깅]
        self.queue_log = []
        
        self.time_quantum_q1 = 8
        self.time_quantum_q2 = 16
        self.current_process_level = 0
        self.current_quantum = 0
        self.current_time_slice = 0

    def run(self):
        print(f"\n--- 다단계 피드백 큐 (MLFQ) 시뮬레이션 시작 ---")

        while (self.processes_to_arrive or self.ready_queue_q1 or self.ready_queue_q2 or 
               self.ready_queue_q3 or self.waiting_queue or self.running_process):
            
            # --- 1. 신규 프로세스 도착 처리 ---
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue_q1.append(proc) # 👈 Q1으로 진입
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Q1 진입)")

            # --- 2. I/O 완료 처리 ---
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue_q1.append(proc) # 👈 Q1으로 진입
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Q1 진입)")

            # --- 3. 큐 간 선점 로직 ---
            # [ 2. 수정된 부분 (CPU 실행 중에만 선점) ]
            if (self.running_process and 
                self.running_process.get_current_burst() and
                self.running_process.get_current_burst()[0] == 'CPU'): # CPU 실행 중에만
                
                # Q1에 작업이 있고, 현재 작업이 Q1이 아닐 때 선점
                if self.ready_queue_q1 and self.current_process_level > 1:
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} (Q{self.current_process_level}) 선점됨 (Q1에 작업 도착)")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time
                    
                    proc = self.running_process
                    proc.state = Process.READY
                    proc.last_ready_time = self.current_time
                    
                    # 자신(선점된 프로세스)의 큐 맨 앞에 다시 넣음
                    if self.current_process_level == 2:
                        self.ready_queue_q2.appendleft(proc)
                    else: # 3
                        self.ready_queue_q3.appendleft(proc)
                    
                    self.running_process = None
                    self.current_time_slice = 0

            # --- 4. Dispatcher ---
            if not self.running_process and self.overhead_remaining == 0:
                if self.ready_queue_q1:
                    self.running_process = self.ready_queue_q1.popleft()
                    self.current_process_level = 1
                    self.current_quantum = 8
                elif self.ready_queue_q2:
                    self.running_process = self.ready_queue_q2.popleft()
                    self.current_process_level = 2
                    self.current_quantum = 16
                elif self.ready_queue_q3:
                    self.running_process = self.ready_queue_q3.popleft()
                    self.current_process_level = 3
                    self.current_quantum = float('inf') # FCFS
                
                if self.running_process:
                    proc = self.running_process
                    proc.state = Process.RUNNING
                    
                    # 문맥 교환 오버헤드 적용
                    if not self.cpu_was_idle:
                        self.context_switches += 1
                        self.overhead_remaining = self.context_switch_overhead
                        self.total_overhead_time += self.context_switch_overhead
                        print(f"[Time {self.current_time:3d}] 문맥 교환 발생 (오버헤드: {self.context_switch_overhead}ms)")
                    self.cpu_was_idle = False
                    wait = self.current_time - proc.last_ready_time
                    proc.wait_time += wait
                    self.current_time_slice = 0 # 퀀텀 리셋
                    
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} (Q{self.current_process_level}) 선택됨 (대기: {wait}ms)")

            # --- 4-1. 오버헤드 처리 ---
            if self.overhead_remaining > 0:
                self.overhead_remaining -= 1
                self.current_time += 1
                continue

            # --- 5. 실행 로직 ---
            # [ 3. 수정된 부분 (RR과 동일한 로직) ]
            if self.running_process:
                proc = self.running_process
                current_burst = proc.get_current_burst()
                
                # 5-a. TERMINATED
                if not current_burst:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    self.running_process = None

                # 5-b. 'CPU'
                elif current_burst[0] == 'CPU':
                    if (not self.gantt_chart or 
                        self.gantt_chart[-1][0] != proc.pid or 
                        len(self.gantt_chart[-1]) == 3):
                        
                        self.gantt_chart.append((proc.pid, self.current_time))
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} (Q{self.current_process_level}) CPU 작업 시작 (남은 시간: {proc.remaining_cpu_time}ms)")

                    # 1ms 실행
                    proc.remaining_cpu_time -= 1
                    self.current_time_slice += 1 # 👈 타임 슬라이스 소모
                    
                    # (1) CPU 버스트가 끝났는지
                    if proc.remaining_cpu_time == 0:
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} (Q{self.current_process_level}) CPU 버스트 완료")
                        
                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                        self.last_cpu_busy_time = self.current_time + 1
                        
                        proc.advance_to_next_burst()
                        
                        # --- 👇 [버그 수정] ---
                        next_burst = proc.get_current_burst()
                        if not next_burst:
                            # [다음 작업이 없음] 종료 처리
                            proc.state = Process.TERMINATED
                            proc.completion_time = self.current_time + 1
                            proc.turnaround_time = proc.completion_time - proc.arrival_time
                            self.completed_processes.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")
                        
                        # (CPU 버스트가 끝났으므로 CPU 반납)
                        self.running_process = None
                        self.current_time_slice = 0
                        # --- 👆 [버그 수정 끝] ---

                    # (2) 퀀텀이 만료되었는지 (Q3-FCFS 제외)
                    elif self.current_time_slice == self.current_quantum and self.current_process_level < 3:
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} (Q{self.current_process_level}) 퀀텀 만료")
                        
                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                        self.last_cpu_busy_time = self.current_time + 1
                        
                        proc.state = Process.READY
                        proc.last_ready_time = self.current_time + 1
                        
                        # 하위 큐로 강등
                        if self.current_process_level == 1:
                            self.ready_queue_q2.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} -> Q2로 강등")
                        elif self.current_process_level == 2:
                            self.ready_queue_q3.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} -> Q3로 강등")

                        self.running_process = None
                        self.current_time_slice = 0

                # 5-c. 'IO' (0-tick)
                elif current_burst[0] == 'IO':
                    io_duration = current_burst[1]
                    proc.state = Process.WAITING
                    io_finish_time = self.current_time + io_duration
                    heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")

                    proc.advance_to_next_burst()
                    self.running_process = None # CPU 반납

                # 5-d. 'LOCK' (0-tick)
                elif current_burst[0] == 'LOCK':
                    resource_name = current_burst[1]
                    resource = get_resource(resource_name)
                    
                    if not resource:
                        print(f"!!! [Time {self.current_time:3d}] 오류: P{proc.pid}가 존재하지 않는 자원 '{resource_name}'을(를) 요청했습니다.")
                        proc.advance_to_next_burst()
                    else:
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid}이(가) '{resource_name}' Lock 시도...")
                        if resource.lock(proc, self.current_time):
                            print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid}이(가) '{resource_name}' Lock 획득")
                            proc.advance_to_next_burst()
                        else:
                            print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid}이(가) '{resource_name}' Lock 실패. (자원 대기)")
                            proc.state = Process.WAITING
                            self.running_process = None 

                # 5-e. 'UNLOCK' (0-tick)
                elif current_burst[0] == 'UNLOCK':
                    resource_name = current_burst[1]
                    resource = get_resource(resource_name)
                    
                    if not resource:
                        print(f"!!! [Time {self.current_time:3d}] 오류: P{proc.pid}가 존재하지 않는 자원 '{resource_name}'을(를) Unlock하려 합니다.")
                        proc.advance_to_next_burst()
                    else:
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid}이(가) '{resource_name}' Unlock 시도...")
                        woken_process = resource.unlock(proc, self.current_time)
                        
                        if woken_process:
                            woken_process.state = Process.READY
                            woken_process.last_ready_time = self.current_time
                            self.ready_queue_q1.append(woken_process) # 👈 [MLFQ] 깨어난 프로세스는 Q1으로
                            print(f"[Time {self.current_time:3d}] 프로세스 {woken_process.pid}이(가) '{resource_name}' 획득 (Q1 진입)")

                        proc.advance_to_next_burst()

            # --- 6. 큐 상태 로깅 ---
            ready_q1_pids = [p.pid for p in self.ready_queue_q1]
            ready_q2_pids = [p.pid for p in self.ready_queue_q2]
            ready_q3_pids = [p.pid for p in self.ready_queue_q3]
            ready_pids = ready_q1_pids + ready_q2_pids + ready_q3_pids  # 모든 큐 합침
            waiting_pids = [item[1] for item in self.waiting_queue]
            self.queue_log.append((self.current_time, ready_pids.copy(), waiting_pids.copy()))
            
            self.current_time += 1
        
        total_simulation_time = self.current_time
        total_cpu_busy_time = 0
        idle_time_start = 0
        
        self.gantt_chart = [entry for entry in self.gantt_chart if len(entry) == 3] 

        for pid, start, end in self.gantt_chart:
            idle_duration = start - idle_time_start
            if idle_duration > 0:
                self.total_cpu_idle_time += idle_duration
            total_cpu_busy_time += (end - start)
            idle_time_start = end
        if total_simulation_time > idle_time_start:
             self.total_cpu_idle_time += (total_simulation_time - idle_time_start)

        print(f"--- 다단계 피드백 큐 (MLFQ) 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    def print_results(self, total_time, total_busy_time):
        print(f"\n--- 📊 다단계 피드백 큐 (MLFQ) 최종 결과 ---")
        
        if not self.completed_processes:
            print("오류: 완료된 프로세스가 없습니다.")
            return

        self.completed_processes.sort(key=lambda x: x.pid)
        
        total_tt = 0
        total_wt = 0
        print("PID\t| 도착\t| 종료\t| 반환시간(TT)\t| 대기시간(WT)")
        print("---------------------------------------------------------")
        for proc in self.completed_processes:
            print(f"{proc.pid}\t| {proc.arrival_time}\t| {proc.completion_time}\t| {proc.turnaround_time}\t\t| {proc.wait_time}")
            total_tt += proc.turnaround_time
            total_wt += proc.wait_time

        n = len(self.completed_processes)
        avg_tt = total_tt / n
        avg_wt = total_wt / n
        
        effective_cpu_time = total_busy_time - self.total_overhead_time
        cpu_utilization = (total_busy_time / total_time) * 100 if total_time > 0 else 0
        effective_cpu_utilization = (effective_cpu_time / total_time) * 100 if total_time > 0 else 0
        
        print("\n--- 요약 ---")
        print(f"평균 반환 시간 (Avg TT) : {avg_tt:.2f}")
        print(f"평균 대기 시간 (Avg WT) : {avg_wt:.2f}")
        print(f"총 실행 시간          : {total_time}")
        print(f"CPU 총 유휴 시간      : {self.total_cpu_idle_time}")
        print(f"CPU 총 사용 시간      : {total_busy_time}")
        print(f"문맥 교환 횟수        : {self.context_switches}")
        print(f"문맥 교환 오버헤드    : {self.total_overhead_time}ms")
        print(f"CPU 사용률 (명목)     : {cpu_utilization:.2f} %")
        print(f"CPU 사용률 (유효)     : {effective_cpu_utilization:.2f} %")

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")