import collections
import heapq 
from process import Process, parse_input_file

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
        self.aging_factor = aging_factor

    def run(self):
        print(f"\n--- 동적 우선순위 (Aging) 시뮬레이션 시작 (Factor={self.aging_factor}) ---")

        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                proc.dynamic_priority = proc.static_priority
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, 우선순위: {proc.static_priority})")

            # --- 2. I/O 완료 처리 ---
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                proc.dynamic_priority = proc.static_priority
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, 우선순위: {proc.static_priority})")

            
            # --- 4. 새로운 스케줄러 로직 (Aging + Dispatch + Preemption) ---
            
            # 4-1. Aging
            for proc in self.ready_queue:
                wait_time = self.current_time - proc.last_ready_time
                proc.dynamic_priority = proc.static_priority - (wait_time // self.aging_factor)

            # 4-2. Dispatcher 및 선점
            best_proc_in_queue = None
            if self.ready_queue:
                best_proc_in_queue = min(self.ready_queue, key=lambda p: (p.dynamic_priority, p.pid))

            if self.running_process:
                if best_proc_in_queue and best_proc_in_queue.dynamic_priority < self.running_process.dynamic_priority:
                    # --- 선점 발생! ---
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (P{best_proc_in_queue.pid} 동적P: {best_proc_in_queue.dynamic_priority})")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time
                    
                    self.running_process.state = Process.READY
                    self.running_process.last_ready_time = self.current_time
                    self.ready_queue.append(self.running_process)
                    
                    self.running_process = best_proc_in_queue
                    self.ready_queue.remove(best_proc_in_queue)
                    self.running_process.state = Process.RUNNING
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    self.gantt_chart.append((self.running_process.pid, self.current_time))
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (동적P: {self.running_process.dynamic_priority}, 대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")
                
                else:
                    pass

            elif best_proc_in_queue:
                self.running_process = best_proc_in_queue
                self.ready_queue.remove(best_proc_in_queue)
                self.running_process.state = Process.RUNNING

                wait = self.current_time - self.running_process.last_ready_time
                self.running_process.wait_time += wait
                self.gantt_chart.append((self.running_process.pid, self.current_time))
                print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (동적P: {self.running_process.dynamic_priority}, 대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")

            if self.running_process:
                proc = self.running_process
                proc.remaining_cpu_time -= 1
                
                if proc.remaining_cpu_time == 0:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                    
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
                    
                    proc.dynamic_priority = proc.static_priority 
                    
                    proc.current_burst_index += 1
                    if proc.current_burst_index < len(proc.burst_pattern):
                        proc.state = Process.WAITING
                        io_duration = proc.burst_pattern[proc.current_burst_index]
                        io_finish_time = self.current_time + 1 + io_duration
                        heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")
                        
                        proc.current_burst_index += 1
                        if proc.current_burst_index < len(proc.burst_pattern):
                            proc.remaining_cpu_time = proc.burst_pattern[proc.current_burst_index]
                    else:
                        proc.state = Process.TERMINATED
                        proc.completion_time = self.current_time + 1
                        proc.turnaround_time = proc.completion_time - proc.arrival_time
                        self.completed_processes.append(proc)
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")

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

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")