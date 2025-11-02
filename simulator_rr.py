import collections
import heapq  # I/O 대기 큐(우선순위 큐)를 위해 import
from process import Process, parse_input_file

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
        
        # --- 💡 RR 수정/추가 부분 ---
        self.time_quantum = time_quantum # 타임 슬라이스 (기본값 4)
        self.current_time_slice = 0 # 현재 프로세스가 사용한 시간

    def run(self):
        """
        시뮬레이션 메인 루프 (RR 버전)
        """
        print(f"\n--- RR (Quantum={self.time_quantum}) 시뮬레이션 시작 ---") # 👈 이름 변경

        # 모든 프로세스가 도착하고, Ready/Waiting 큐가 비고, 실행 중인 프로세스가 없을 때까지
        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 --- (FCFS와 동일)
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입)")

            # --- 2. I/O 완료 처리 (I/O 인터럽트) --- (FCFS와 동일)
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                self.ready_queue.append(proc) 
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입)")

            # --- 3. CPU 작업 처리 (Dispatcher 및 실행) ---
            
            # 3-1. 현재 실행 중인 프로세스가 없다면 (CPU가 비었다면)
            if not self.running_process:
                if self.ready_queue:
                    # (FCFS와 동일한 로직)
                    self.running_process = self.ready_queue.popleft() 
                    self.running_process.state = Process.RUNNING
                    
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    self.gantt_chart.append((self.running_process.pid, self.current_time))
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")
                
                else:
                    pass 

            # 3-2. 현재 실행 중인 프로세스가 있다면 (💥 FCFS와 로직이 달라지는 부분)
            if self.running_process:
                proc = self.running_process
                
                # 3-2-a. CPU 버스트 1 감소 / 타임 슬라이스 1 소모
                proc.remaining_cpu_time -= 1
                self.current_time_slice += 1 # 👈 [RR] 타임 슬라이스 사용

                # 3-2-b. CPU 버스트가 끝났는지 검사
                if proc.remaining_cpu_time == 0:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                    
                    # (간트 차트 기록, I/O 처리, 종료 처리는 FCFS와 완벽히 동일)
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
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

                    # 작업이 끝났으므로 CPU 비우기
                    self.running_process = None
                    self.current_time_slice = 0 # 👈 [RR] 타임 슬라이스 리셋
                
                # --- 💡 [RR] 여기가 2번 수정사항의 핵심입니다 ---
                # 3-2-c. CPU 버스트가 아직 남았는데, 타임 슬라이스를 다 썼다면
                elif self.current_time_slice == self.time_quantum:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 타임 슬라이스 만료")

                    # 간트 차트 기록 (중단)
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
                    
                    # Ready 큐의 맨 뒤로 보냄 (문맥 전환)
                    proc.state = Process.READY
                    # 💡주의: +1을 하여 다음 시간(Time unit)에 Ready 큐에 들어가는 것으로 처리
                    proc.last_ready_time = self.current_time + 1 
                    self.ready_queue.append(proc)
                    
                    # CPU 비우기
                    self.running_process = None
                    self.current_time_slice = 0 # 👈 [RR] 타임 슬라이스 리셋
                
                # (3-2-d. 버스트도 남았고, 타임 슬라이스도 남음 -> 다음 1ms 계속 실행)
                
            # --- 4. 통계 업데이트 ---
            # (버그 수정된 상태 유지 - FCFS와 동일)

            # --- 5. 시간 증가 ---
            self.current_time += 1
        
        # --- 시뮬레이션 종료 처리 ---
        total_simulation_time = self.current_time
        
        total_cpu_busy_time = 0
        idle_time_start = 0
        for pid, start, end in self.gantt_chart:
            idle_duration = start - idle_time_start
            if idle_duration > 0:
                self.total_cpu_idle_time += idle_duration
            total_cpu_busy_time += (end - start)
            idle_time_start = end
        if total_simulation_time > idle_time_start:
             self.total_cpu_idle_time += (total_simulation_time - idle_time_start)

        print(f"--- RR (Quantum={self.time_quantum}) 시뮬레이션 종료 ---") # 👈 이름 변경
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

        print("\n--- 간트 차트 (Gantt Chart) ---")
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")