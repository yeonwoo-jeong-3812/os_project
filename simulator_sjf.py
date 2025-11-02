import collections
import heapq 
from process import Process, parse_input_file

class SimulatorSJF: #  클래스 이름 변경 (SRTF)
    """
    선점형 SJF (Shortest Remaining Time First - SRTF) 시뮬레이터
    """
    def __init__(self, process_list):
        self.processes_to_arrive = []
        for proc in process_list:
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # --- 💡 1. Ready 큐 변경 ---
        # deque가 아니라 '최소 힙' (priority queue)으로 변경
        # (남은시간, PID, 프로세스) 튜플을 저장
        self.ready_queue = [] 
        
        self.waiting_queue = []
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 

    def run(self):
        print(f"\n--- 선점형 SJF (SRTF) 시뮬레이션 시작 ---")

        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                # --- 💡 2. 힙 정렬 기준: '남은 CPU 시간' ---
                heapq.heappush(self.ready_queue, (proc.remaining_cpu_time, proc.pid, proc))
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, 남은 시간: {proc.remaining_cpu_time})")

            # --- 2. I/O 완료 처리 ---
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                # --- 💡 2. 힙 정렬 기준: '남은 CPU 시간' ---
                heapq.heappush(self.ready_queue, (proc.remaining_cpu_time, proc.pid, proc))
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, 남은 시간: {proc.remaining_cpu_time})")

            # --- 💡 3. 선점(Preemption) 로직 ---
            # (1, 2 단계에서 새 프로세스가 Ready 큐에 들어온 직후)
            if self.running_process and self.ready_queue:
                # 힙의 top (가장 짧은 작업) 확인
                shortest_remaining_time, shortest_pid, _ = self.ready_queue[0] 
                
                # 현재 실행 중인 작업보다 힙에 있는 작업이 더 짧으면 선점
                if shortest_remaining_time < self.running_process.remaining_cpu_time:
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (새 작업 P{shortest_pid}이 더 짧음)")
                    
                    # 간트 차트 기록 (중단)
                    # (gantt_chart가 비어있지 않고, 마지막 pid가 현재 pid와 같을 때만 종료 시간 기록)
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        start_time = self.gantt_chart[-1][1]
                        self.gantt_chart[-1] = (self.running_process.pid, start_time, self.current_time)
                        self.last_cpu_busy_time = self.current_time

                    # 실행 중인 프로세스를 다시 Ready 큐(힙)에 넣음
                    proc = self.running_process
                    proc.state = Process.READY
                    proc.last_ready_time = self.current_time
                    # 힙에 넣을 땐 '남은 시간' 기준으로
                    heapq.heappush(self.ready_queue, (proc.remaining_cpu_time, proc.pid, proc))
                    
                    # CPU 비우기 (곧바로 3-1에서 새 프로세스가 선택될 것임)
                    self.running_process = None
            
            # --- 3-1. CPU 작업 처리 (Dispatcher) ---
            if not self.running_process:
                if self.ready_queue:
                    # --- 💡 1. 힙에서 pop ---
                    # 힙에서 '남은 시간이 가장 짧은' 프로세스를 꺼냄
                    remaining_time, pid, self.running_process = heapq.heappop(self.ready_queue)
                    
                    self.running_process.state = Process.RUNNING
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    # 간트 차트 기록 (새로 시작하거나, 이어붙임)
                    self.gantt_chart.append((self.running_process.pid, self.current_time))
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (남은 시간: {remaining_time}ms, 대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")
                
                else:
                    pass 

            # --- 3-2. CPU 실행 ---
            if self.running_process:
                proc = self.running_process
                
                # CPU 버스트 1 감소
                proc.remaining_cpu_time -= 1
                
                # CPU 버스트가 끝났는지 검사
                if proc.remaining_cpu_time == 0:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                    
                    # 간트 차트 종료 시간 기록
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
                    
                    # (I/O 또는 종료 처리는 FCFS와 동일)
                    proc.current_burst_index += 1
                    if proc.current_burst_index < len(proc.burst_pattern):
                        proc.state = Process.WAITING
                        io_duration = proc.burst_pattern[proc.current_burst_index]
                        io_finish_time = self.current_time + 1 + io_duration
                        heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")
                        
                        proc.current_burst_index += 1
                        if proc.current_burst_index < len(proc.burst_pattern):
                            # 💡 다음 CPU 버스트 시간을 '남은 시간'으로 설정
                            proc.remaining_cpu_time = proc.burst_pattern[proc.current_burst_index]
                    else:
                        proc.state = Process.TERMINATED
                        proc.completion_time = self.current_time + 1
                        proc.turnaround_time = proc.completion_time - proc.arrival_time
                        self.completed_processes.append(proc)
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")

                    self.running_process = None
                
                # (RR과 달리 타임 슬라이스 만료 로직이 없음)

            # --- 4. 통계 업데이트 --- (FCFS/RR과 동일)
            # --- 5. 시간 증가 ---
            self.current_time += 1
        
        # --- 시뮬레이션 종료 처리 ---
        total_simulation_time = self.current_time
        
        total_cpu_busy_time = 0
        idle_time_start = 0
        # (간트 차트가 (pid, start, end) 형식이 아닌 (pid, start)만 있을 수 있으므로 보강)
        processed_gantt_chart = []
        for i, entry in enumerate(self.gantt_chart):
            if len(entry) == 3: # (pid, start, end)
                processed_gantt_chart.append(entry)
            elif len(entry) == 2: # (pid, start) - 선점되어 끝을 못 만남
                # 다음 항목을 보거나, 마지막 항목인지 확인
                pid, start = entry
                end = -1
                if i + 1 < len(self.gantt_chart) and self.gantt_chart[i+1][0] != pid:
                     end = self.gantt_chart[i+1][1] # 다음 작업 시작 시간이 나의 종료 시간
                elif i + 1 == len(self.gantt_chart): # 마지막 항목
                     end = self.last_cpu_busy_time 
                
                if end != -1:
                    processed_gantt_chart.append((pid, start, end))
                    # (이 부분은 로직이 복잡해질 수 있으니, 선점 시 종료시간을 명확히 기록하는 위 3번 로직이 중요)
        
        self.gantt_chart = [entry for entry in self.gantt_chart if len(entry) == 3] # (start, end)가 완성된 것만 사용

        for pid, start, end in self.gantt_chart:
            idle_duration = start - idle_time_start
            if idle_duration > 0:
                self.total_cpu_idle_time += idle_duration
            total_cpu_busy_time += (end - start)
            idle_time_start = end
        if total_simulation_time > idle_time_start:
             self.total_cpu_idle_time += (total_simulation_time - idle_time_start)

        print(f"--- 선점형 SJF (SRTF) 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    def print_results(self, total_time, total_busy_time):
        """
        최종 통계 결과를 출력합니다. (SJF/SRTF)
        """
        print(f"\n--- 📊 선점형 SJF (SRTF) 최종 결과 ---")
        
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
        # (SJF 간트 차트는 조각날 수 있으므로, 종료 시간 기록 로직이 매우 중요)
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")