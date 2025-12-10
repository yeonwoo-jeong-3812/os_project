import collections
import heapq  # I/O 대기 큐(우선순위 큐)를 위해 import
from process import Process, parse_input_file
from sync import get_resource

class SimulatorRR: # 👈 클래스 이름 변경
    """
    Round Robin (RR) 스케줄링 알고리즘을 위한 시뮬레이터 클래스
    """
    def __init__(self, process_list, time_quantum=4): # 👈 time_quantum 파라미터 추가
        # (processes_to_arrive, ready_queue, waiting_queue 등은 FCFS와 동일)
        self.processes_to_arrive = []
        for proc in process_list:
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))
        self.ready_queue = collections.deque()
        self.waiting_queue = []
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 
        
        # --- RR 수정/추가 부분 ---
        self.time_quantum = time_quantum # (4)
        self.current_time_slice = 0 # 

        # [문맥 전환 횟수 추가]
        self.context_switches = 0
        self.cpu_was_idle = True

   # simulator_rr.py의 run() 메소드 (덮어쓸 내용)

    def run(self):
        """
        시뮬레이션 메인 루프 (RR + 동기화 기능 추가됨)
        """
        print(f"\n--- RR (Quantum={self.time_quantum}) 시뮬레이션 시작 ---")

        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입)")

            # --- 2. I/O 완료 처리 ---
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입)")

            # --- 3. CPU 작업 처리 (Dispatcher) ---
            if not self.running_process:
                if self.ready_queue:
                    self.running_process = self.ready_queue.popleft() 
                    self.running_process.state = Process.RUNNING
                    
                    if not self.cpu_was_idle:
                        self.context_switches += 1
                    self.cpu_was_idle = False
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    self.current_time_slice = 0
                    
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선택됨 (대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")
                
                else:
                    self.cpu_was_idle = True
                    pass 

            # --- 3-2. 실행 로직 ---
            if self.running_process:
                proc = self.running_process
                current_burst = proc.get_current_burst()

                # 3-2-a. TERMINATED
                if not current_burst:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    self.running_process = None

                # 3-2-b. 'CPU'
                elif current_burst[0] == 'CPU':
                    if (not self.gantt_chart or 
                        self.gantt_chart[-1][0] != proc.pid or 
                        len(self.gantt_chart[-1]) == 3):
                        
                        self.gantt_chart.append((proc.pid, self.current_time))
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} CPU 작업 시작 (남은 시간: {proc.remaining_cpu_time}ms)")

                    proc.remaining_cpu_time -= 1
                    self.current_time_slice += 1 # 타임 슬라이스 사용

                    # (1) CPU 버스트가 끝났는지 검사
                    if proc.remaining_cpu_time == 0:
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                        
                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                        self.last_cpu_busy_time = self.current_time + 1
                        
                        proc.advance_to_next_burst()
                    
                    # (2) CPU 버스트가 남았는데, 타임 슬라이스를 다 썼는지 검사
                    elif self.current_time_slice == self.time_quantum:
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 타임 슬라이스 만료")

                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                        self.last_cpu_busy_time = self.current_time + 1
                        
                        proc.state = Process.READY
                        proc.last_ready_time = self.current_time + 1 
                        self.ready_queue.append(proc)
                        
                        self.running_process = None # CPU 반납

                # 3-2-c. 'IO'
                elif current_burst[0] == 'IO':
                    io_duration = current_burst[1]
                    proc.state = Process.WAITING
                    io_finish_time = self.current_time + io_duration # (버그 수정)
                    
                    heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")

                    proc.advance_to_next_burst()
                    self.running_process = None # CPU 반납

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
                            self.running_process = None # CPU 반납

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
                            self.ready_queue.append(woken_process)
                            print(f"[Time {self.current_time:3d}] 프로세스 {woken_process.pid}이(가) '{resource_name}' 획득 (Ready 큐 진입)")

                        proc.advance_to_next_burst()
            
            # --- 5. 시간 증가 ---
            self.current_time += 1
        
        # --- 시뮬레이션 종료 처리 ---
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

        print(f"--- RR (Quantum={self.time_quantum}) 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    # print_results 메소드 (FCFS와 거의 동일)
    def print_results(self, total_time, total_busy_time):
        """
        최종 통계 결과를 출력합니다.
        (RR용으로 제목만 수정)
        """
        print(f"\n--- 📊 RR (Q={self.time_quantum}) 최종 결과 ---") # 👈 이름 변경
        
        if not self.completed_processes:
            print("오류: 완료된 프로세스가 없습니다.")
            return

        # PID 순서대로 정렬하여 출력
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