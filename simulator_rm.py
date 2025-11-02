import collections
import heapq 
from process import Process, parse_input_file

class SimulatorRM: # 👈 1. 클래스 이름 변경
    """
    Rate Monotonic (RM) 시뮬레이터 (정적 우선순위 기반)
    - 실시간 프로세스(P5, P6)만 스케줄링합니다.
    - 우선순위 = Period (주기)
    """
    def __init__(self, process_list):
        self.processes_to_arrive = []
        
        # --- 💡 2. 실시간 프로세스만 필터링 ---
        rt_processes = [p for p in process_list if p.period > 0]
        
        for proc in rt_processes:
            # --- 💡 3. 우선순위를 'Period'로 설정 ---
            proc.static_priority = proc.period 
            
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # (우선순위 큐)
        self.ready_queue = [] 
        
        self.waiting_queue = [] # (P5, P6는 I/O가 없어서 실제론 안 쓰임)
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 
        
        # --- 💡 4. 실시간 통계 ---
        self.deadline_misses = 0

    def run(self):
        print(f"\n--- 실시간 RM 시뮬레이션 시작 ---") 

        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                # 힙 정렬 기준: 'static_priority' (즉, Period)
                heapq.heappush(self.ready_queue, (proc.static_priority, proc.pid, proc))
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, 주기: {proc.static_priority})")

            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                heapq.heappush(self.ready_queue, (proc.static_priority, proc.pid, proc))
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, 주기: {proc.static_priority})")

            # 선점(Preemption) 로직 (우선순위 = Period)
            if self.running_process and self.ready_queue:
                highest_priority, highest_pid, _ = self.ready_queue[0] 
                
                if highest_priority < self.running_process.static_priority:
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (새 작업 P{highest_pid} 주기가 더 짧음)")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time

                    proc = self.running_process
                    proc.state = Process.READY
                    proc.last_ready_time = self.current_time
                    heapq.heappush(self.ready_queue, (proc.static_priority, proc.pid, proc))
                    
                    self.running_process = None
            
            if not self.running_process:
                if self.ready_queue:
                    priority, pid, self.running_process = heapq.heappop(self.ready_queue)
                    
                    self.running_process.state = Process.RUNNING
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    # 💡 5. 절대 마감시한 계산
                    self.running_process.absolute_deadline = self.running_process.arrival_time + self.running_process.deadline
                    
                    self.gantt_chart.append((self.running_process.pid, self.current_time))
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (주기: {priority}, 마감: {self.running_process.absolute_deadline})")
                
                else:
                    pass 

            if self.running_process:
                proc = self.running_process
                proc.remaining_cpu_time -= 1
                
                if proc.remaining_cpu_time == 0:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                    
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
                    
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time + 1
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    
                    # --- 💡 6. 마감시한 준수 여부 확인 ---
                    if proc.completion_time > proc.absolute_deadline:
                        self.deadline_misses += 1
                        print(f"!!! [Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 마감시한 초과 !!! (종료: {proc.completion_time}, 마감: {proc.absolute_deadline})")

                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")

                    self.running_process = None
            
            # (P5, P6는 입력 데이터상 I/O가 없으므로 해당 로직은 실행되지 않음)

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
        
        cpu_utilization = (total_busy_time / total_time) * 100 if total_time > 0 else 0
        
        print("\n--- 요약 ---")
        print(f"평균 반환 시간 (Avg TT) : {avg_tt:.2f}")
        print(f"평균 대기 시간 (Avg WT) : {avg_wt:.2f}")
        print(f"총 실행 시간          : {total_time}")
        print(f"CPU 총 유휴 시간      : {self.total_cpu_idle_time}")
        print(f"CPU 총 사용 시간      : {total_busy_time}")
        print(f"CPU 사용률 (Util)   : {cpu_utilization:.2f} %")
        print(f"마감시한 초과 횟수    : {self.deadline_misses}") # 👈 RM 통계 추가

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")