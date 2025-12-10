import collections
import heapq 
from process import Process, parse_input_file
from sync import get_resource

# 👇👇👇 1. 클래스 이름이 'SimulatorPriorityDynamic'인지 확인!
class SimulatorPriorityDynamic:
    """
    선점형 동적 우선순위(Aging) 시뮬레이터
    """
    def __init__(self, process_list, aging_factor=10):
        self.processes_to_arrive = []
        for proc in process_list:
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # --- Ready 큐: 일반 리스트로 변경 ---
        self.ready_queue = [] 
        
        self.waiting_queue = []
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 
        
        # [문맥 전환 횟수 추가]
        self.context_switches = 0
        self.cpu_was_idle = True
self.aging_factor = aging_factor

    def run(self):
        print(f"\n--- 동적 우선순위 (Aging) 시뮬레이션 시작 (Factor={self.aging_factor}) ---")

        # [ 2. 우선순위 계산을 위한 헬퍼(helper) 함수 정의 ]
        def get_dynamic_priority_key(proc):
            """
            프로세스의 현재 동적 우선순위 튜플을 반환합니다.
            (0-tick 명령어 최우선)
            """
            burst = proc.get_current_burst()
            cmd_prio = 1 # 기본값 (CPU)
            
            if burst and burst[0] != 'CPU':
                cmd_prio = 0 # 0-tick (LOCK, UNLOCK)
            
            # (명령어 우선순위, 동적 우선순위, PID)
            return (cmd_prio, proc.dynamic_priority, proc.pid)


        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 --- (단순 append)
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                proc.dynamic_priority = proc.static_priority # 동적 우선순위 초기화
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, Prio: {proc.static_priority})")

            # --- 2. I/O 완료 처리 --- (단순 append)
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                proc.dynamic_priority = proc.static_priority # I/O 완료 시 우선순위 초기화
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, Prio: {proc.static_priority})")

            
            # --- 3. Aging 및 스케줄러 로직 ---
            # [ 3. 수정된 부분 (Aging + Dispatch + Preemption) ]
            
            # 3-1. Aging (매시간 Ready 큐 전체를 갱신)
            for proc in self.ready_queue:
                wait_time = self.current_time - proc.last_ready_time
                # (가이드라인 공식)
                proc.dynamic_priority = proc.static_priority - (wait_time // self.aging_factor)

            # 3-2. Dispatcher 및 선점
            best_proc_in_queue = None
            if self.ready_queue:
                # 0-tick 명령어를 포함한 최고 우선순위 프로세스를 찾음
                best_proc_in_queue = min(self.ready_queue, key=get_dynamic_priority_key)

            if (self.running_process and 
                self.running_process.get_current_burst() and
                self.running_process.get_current_burst()[0] == 'CPU'):
                
                # (CPU 실행 중일 때만 선점 가능)
                if best_proc_in_queue and get_dynamic_priority_key(best_proc_in_queue) < get_dynamic_priority_key(self.running_process):
                    # --- 선점 발생! ---
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (P{best_proc_in_queue.pid} 우선순위 높음)")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time
                    
                    self.running_process.state = Process.READY
                    self.running_process.last_ready_time = self.current_time
                    self.ready_queue.append(self.running_process)
                    
                    self.running_process = best_proc_in_queue
                    self.ready_queue.remove(best_proc_in_queue)
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    # (로그 및 간트차트는 3-3 실행 로직에서 처리)
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (동적P: {self.running_process.dynamic_priority}, 대기: {wait}ms)")
                
                else:
                    self.cpu_was_idle = True
                    pass # 계속 실행

            elif not self.running_process and best_proc_in_queue:
                # --- Dispatch ---
                self.running_process = best_proc_in_queue
                self.ready_queue.remove(best_proc_in_queue)
                self.running_process.state = Process.RUNNING

                    
                    if not self.cpu_was_idle:
                        self.context_switches += 1
                    self.cpu_was_idle = False
                wait = self.current_time - self.running_process.last_ready_time
                self.running_process.wait_time += wait
                # (로그 및 간트차트는 3-3 실행 로직에서 처리)
                print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (동적P: {self.running_process.dynamic_priority}, 대기: {wait}ms)")

            # --- 3-3. CPU 실행 ---
            # [ 4. 수정된 부분 (Static Priority와 동일한 실행 로직) ]
            if self.running_process:
                proc = self.running_process
                current_burst = proc.get_current_burst()

                # 3-3-a. TERMINATED
                if not current_burst:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    self.running_process = None

                # 3-3-b. 'CPU'
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
                            self.ready_queue.append(proc) 
                            self.running_process = None
                        else:
                            # --- 👇 [버그 수정] ---
                            # [다음 작업이 없음] 종료 처리
                            proc.state = Process.TERMINATED
                            proc.completion_time = self.current_time + 1
                            proc.turnaround_time = proc.completion_time - proc.arrival_time
                            self.completed_processes.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")
                            self.running_process = None
                            # --- 👆 [버그 수정 끝] ---

                # 3-3-c. 'IO'
                elif current_burst[0] == 'IO':
                    io_duration = current_burst[1]
                    proc.state = Process.WAITING
                    io_finish_time = self.current_time + io_duration
                    heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")

                    proc.advance_to_next_burst()
                    self.running_process = None # CPU 반납

                # 3-3-d. 'LOCK'
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
                            
                    if self.running_process: # (Lock 실패 시는 이미 None이 됨)
                        next_burst = proc.get_current_burst()
                        if next_burst:
                            proc.state = Process.READY
                            proc.last_ready_time = self.current_time
                            self.ready_queue.append(proc) # 👈 Ready 큐 (리스트)에 추가
                        self.running_process = None

                # 3-3-e. 'UNLOCK'
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
                            self.ready_queue.append(woken_process) # 👈 Ready 큐 (리스트)에 추가
                            print(f"[Time {self.current_time:3d}] 프로세스 {woken_process.pid}이(가) '{resource_name}' 획득 (Ready 큐 진입)")

                        proc.advance_to_next_burst()

                    next_burst = proc.get_current_burst()
                    if next_burst:
                        proc.state = Process.READY
                        proc.last_ready_time = self.current_time
                        self.ready_queue.append(proc) # 👈 Ready 큐 (리스트)에 추가
                    self.running_process = None

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

        print(f"--- 동적 우선순위 (Aging) 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    def print_results(self, total_time, total_busy_time):
        print(f"\n--- 📊 동적 우선순위 (Aging, Factor={self.aging_factor}) 최종 결과 ---")
        
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
        
        cpu_utilization = (total_busy_time / total_time) * 100 if total_time > 0 else 0
        
        print("\n--- 요약 ---")
        print(f"평균 반환 시간 (Avg TT) : {avg_tt:.2f}")
        print(f"평균 대기 시간 (Avg WT) : {avg_wt:.2f}")
        print(f"총 실행 시간          : {total_time}")
        print(f"CPU 총 유휴 시간      : {self.total_cpu_idle_time}")
        print(f"CPU 총 사용 시간      : {total_busy_time}")
        print(f"CPU 사용률 (Util)   : {cpu_utilization:.2f} %")
        print(f"총 문맥 전환 횟수     : {self.context_switches}")

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")