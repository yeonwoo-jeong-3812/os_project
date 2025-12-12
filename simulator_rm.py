import collections
import heapq 
from process import Process, parse_input_file
from sync import get_resource

class SimulatorRM: # 
    """
    Rate Monotonic (RM) (정적 우선순위 기반)
    - 실시간 프로세스(P5, P6)만 스케줄링합니다.
    - 우선순위 = Period (주기)
    """
    def __init__(self, process_list, context_switch_overhead=1, max_simulation_time=200):
        self.processes_to_arrive = []
        
        # --- 2. 실시간 프로세스만 필터링 ---
        rt_processes = [p for p in process_list if p.period > 0]
        
        # 원본 프로세스 정보 저장 (주기적 재생성용)
        self.original_processes = {}
        
        for proc in rt_processes:
            # --- 3. 우선순위를 'Period'로 설정 ---
            proc.static_priority = proc.period 
            
            # 원본 정보 저장
            self.original_processes[proc.pid] = {
                'burst_pattern': proc.burst_pattern.copy(),
                'period': proc.period,
                'deadline': proc.deadline,
                'static_priority': proc.static_priority
            }
            
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))
        
        self.max_simulation_time = max_simulation_time

        # (우선순위 큐)
        self.ready_queue = [] 
        
        self.waiting_queue = [] # (P5, P6는 I/O가 없어서 실제론 안 쓰임)
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
        
        # --- 4. 실시간 통계 ---
        self.deadline_misses = 0

    def run(self):
        print(f"\n--- 실시간 RM 시작 ---") 

        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            # [ 2. 수정된 부분 (우선순위 튜플 사용) ]
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                # 절대 마감시한 계산 (도착 시점에 1회)
                proc.absolute_deadline = proc.arrival_time + proc.deadline
                
                current_burst = proc.get_current_burst()
                if current_burst and current_burst[0] == 'CPU':
                    # (1, 주기(우선순위), PID, proc)
                    heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, 주기: {proc.static_priority})")
                elif current_burst: # LOCK, UNLOCK (0-tick)
                    # (0, 주기(우선순위), PID, proc) -> 최우선
                    heapq.heappush(self.ready_queue, (0, proc.static_priority, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, 명령: {current_burst[0]})")


            # --- 2. I/O 완료 처리 ---
            # [ 2. 수정된 부분 (우선순위 튜플 사용) ]
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                current_burst = proc.get_current_burst()
                if current_burst and current_burst[0] == 'CPU':
                    heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, 주기: {proc.static_priority})")
                elif current_burst: # LOCK, UNLOCK
                    heapq.heappush(self.ready_queue, (0, proc.static_priority, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, 명령: {current_burst[0]})")

            # --- 3. 선점(Preemption) 로직 (우선순위 = Period) ---
            # [ 3. 수정된 부분 (튜플 비교) ]
            if (self.running_process and 
                self.running_process.get_current_burst() and
                self.running_process.get_current_burst()[0] == 'CPU' and 
                self.ready_queue):
                
                best_prio_tuple = self.ready_queue[0][:2] # (cmd_prio, static_prio)
                best_pid = self.ready_queue[0][2]
                running_prio_tuple = (1, self.running_process.static_priority)
                
                if best_prio_tuple < running_prio_tuple:
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (새 작업 P{best_pid} 주기가 더 짧음)")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time

                    proc = self.running_process
                    proc.state = Process.READY
                    proc.last_ready_time = self.current_time
                    heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                    
                    self.running_process = None
            
            # --- 3-1. CPU 작업 처리 (Dispatcher) ---
            if not self.running_process:
                if self.ready_queue:
                    cmd_prio, priority, pid, self.running_process = heapq.heappop(self.ready_queue)
                    
                    self.running_process.state = Process.RUNNING
                    
                    if not self.cpu_was_idle:
                        self.context_switches += 1
                    self.cpu_was_idle = False
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    # (기존 RM 코드에서 마감시한 계산 부분을 도착 시점으로 이동시킴)
                    
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선택됨 (주기: {priority}, 마감: {self.running_process.absolute_deadline}, 대기: {wait}ms)")
                
                else:
                    self.cpu_was_idle = True
                    pass 

            # --- 3-2. CPU 실행 ---
            # [ 4. 수정된 부분 (Static Priority와 동일한 로직) ]
            if self.running_process:
                proc = self.running_process
                current_burst = proc.get_current_burst()

                # 3-2-a. TERMINATED
                if not current_burst:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    
                    # --- 마감시한 준수 여부 확인 ---
                    if proc.completion_time > proc.absolute_deadline:
                        self.deadline_misses += 1
                        print(f"!!! [Time {self.current_time:3d}] 프로세스 {proc.pid} 마감시한 초과 !!! (종료: {proc.completion_time}, 마감: {proc.absolute_deadline})")
                    
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    
                    # 주기적 재스케줄링
                    next_arrival = proc.arrival_time + proc.period
                    if next_arrival < self.max_simulation_time:
                        original = self.original_processes[proc.pid]
                        new_proc = Process(
                            proc.pid,
                            next_arrival,
                            0,
                            ",".join(f"{cmd}:{val}" for cmd, val in original['burst_pattern']),
                            original['period'],
                            original['deadline']
                        )
                        new_proc.static_priority = original['static_priority']
                        heapq.heappush(self.processes_to_arrive, (next_arrival, new_proc.pid, new_proc))
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 다음 주기 {next_arrival}에 재도착 예정")
                    
                    self.running_process = None

                # 3-2-b. 'CPU'
                elif current_burst[0] == 'CPU':
                    if (not self.gantt_chart or 
                        self.gantt_chart[-1][0] != proc.pid or 
                        len(self.gantt_chart[-1]) == 3):
                        
                        self.gantt_chart.append((proc.pid, self.current_time))
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} CPU 작업 시작 (남은 시간: {proc.remaining_cpu_time}ms)")

                    proc.remaining_cpu_time -= 1
                    
                    if proc.remaining_cpu_time == 0:
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                        
                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                        self.last_cpu_busy_time = self.current_time + 1
                        
                        proc.advance_to_next_burst()
                        
                        next_burst = proc.get_current_burst()
                        if next_burst:
                            # [다음 작업이 있음] Ready 큐로 복귀
                            proc.state = Process.READY
                            proc.last_ready_time = self.current_time + 1
                            if next_burst[0] == 'CPU':
                                heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                            else: # LOCK, UNLOCK
                                heapq.heappush(self.ready_queue, (0, proc.static_priority, proc.pid, proc))
                            self.running_process = None
                        else:
                            # --- [버그 수정] ---
                            # [다음 작업이 없음] 종료 처리
                            proc.state = Process.TERMINATED
                            proc.completion_time = self.current_time + 1
                            proc.turnaround_time = proc.completion_time - proc.arrival_time
                            
                            # (마감시한 체크)
                            if proc.completion_time > proc.absolute_deadline:
                                self.deadline_misses += 1
                                print(f"!!! [Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 마감시한 초과 !!! (종료: {proc.completion_time}, 마감: {proc.absolute_deadline})")

                            self.completed_processes.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")
                            
                            # 주기적 재스케줄링
                            next_arrival = proc.arrival_time + proc.period
                            if next_arrival < self.max_simulation_time:
                                original = self.original_processes[proc.pid]
                                new_proc = Process(
                                    proc.pid,
                                    next_arrival,
                                    0,
                                    ",".join(f"{cmd}:{val}" for cmd, val in original['burst_pattern']),
                                    original['period'],
                                    original['deadline']
                                )
                                new_proc.static_priority = original['static_priority']
                                heapq.heappush(self.processes_to_arrive, (next_arrival, new_proc.pid, new_proc))
                                print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 다음 주기 {next_arrival}에 재도착 예정")
                            
                            self.running_process = None
                            # --- [버그 수정 끝] ---
                    
                # 3-2-c. 'IO'
                elif current_burst[0] == 'IO':
                    io_duration = current_burst[1]
                    proc.state = Process.WAITING
                    io_finish_time = self.current_time + io_duration
                    heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")

                    proc.advance_to_next_burst()
                    self.running_process = None

                # 3-2-d. 'LOCK'
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
                            
                    if self.running_process: 
                        next_burst = proc.get_current_burst()
                        if next_burst:
                            proc.state = Process.READY
                            proc.last_ready_time = self.current_time
                            if next_burst[0] == 'CPU':
                                heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                            else:
                                heapq.heappush(self.ready_queue, (0, proc.static_priority, proc.pid, proc))
                        self.running_process = None

                # 3-2-e. 'UNLOCK'
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
                            
                            woken_burst = woken_process.get_current_burst()
                            if woken_burst and woken_burst[0] == 'CPU':
                                heapq.heappush(self.ready_queue, (1, woken_process.static_priority, woken_process.pid, woken_process))
                            elif woken_burst:
                                heapq.heappush(self.ready_queue, (0, woken_process.static_priority, woken_process.pid, woken_process))
                            print(f"[Time {self.current_time:3d}] 프로세스 {woken_process.pid}이(가) '{resource_name}' 획득 (Ready 큐 진입)")

                        proc.advance_to_next_burst()

                    next_burst = proc.get_current_burst()
                    if next_burst:
                        proc.state = Process.READY
                        proc.last_ready_time = self.current_time
                        if next_burst[0] == 'CPU':
                            heapq.heappush(self.ready_queue, (1, proc.static_priority, proc.pid, proc))
                        else:
                            heapq.heappush(self.ready_queue, (0, proc.static_priority, proc.pid, proc))
                    self.running_process = None
            
            # --- 4. 큐 상태 로깅 ---
            ready_pids = [item[2] for item in self.ready_queue]  # (cmd_prio, priority, pid, proc)
            waiting_pids = [item[1] for item in self.waiting_queue]  # (time, pid, proc)
            self.queue_log.append((self.current_time, ready_pids.copy(), waiting_pids.copy()))
            
            self.current_time += 1
        
        # --- 시뮬레이션 종료 처리 ---
        # (이하 print_results는 정적 우선순위와 거의 동일)
        total_simulation_time = self.current_time
        total_cpu_busy_time = 0
        idle_time_start = 0
        self.gantt_chart = [entry for entry in self.gantt_chart if len(entry) == 3] 
        for pid, start, end in self.gantt_chart:
            idle_duration = start - idle_time_start
            if idle_duration > 0: self.total_cpu_idle_time += idle_duration
            total_cpu_busy_time += (end - start)
            idle_time_start = end
        if total_simulation_time > idle_time_start:
             self.total_cpu_idle_time += (total_simulation_time - idle_time_start)

        print(f"--- 실시간 RM 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    def print_results(self, total_time, total_busy_time):
        print(f"\n--- 📊 실시간 RM 최종 결과 ---")
        
        if not self.completed_processes:
            print("오류: 완료된 프로세스가 없습니다.")
            return

        self.completed_processes.sort(key=lambda x: x.pid)
        total_tt = 0; total_wt = 0
        print("PID\t| 도착\t| 종료\t| 반환시간(TT)\t| 대기시간(WT)")
        print("---------------------------------------------------------")
        for proc in self.completed_processes:
            print(f"{proc.pid}\t| {proc.arrival_time}\t| {proc.completion_time}\t| {proc.turnaround_time}\t\t| {proc.wait_time}")
            total_tt += proc.turnaround_time; total_wt += proc.wait_time

        n = len(self.completed_processes)
        avg_tt = total_tt / n if n > 0 else 0
        avg_wt = total_wt / n if n > 0 else 0
        
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
        print(f"마감시한 초과 횟수    : {self.deadline_misses}") # 👈 RM 통계 추가

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")