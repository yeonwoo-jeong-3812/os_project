import collections
import heapq  # I/O 대기 큐(우선순위 큐)를 위해 import

# 1단계에서 만든 process.py 파일에서 Process 클래스와 parse_input_file 함수를 가져옵니다.
from process import Process, parse_input_file

class SimulatorFCFS:
    """
    FCFS 스케줄링 알고리즘을 위한 시뮬레이터 클래스
    """
    def __init__(self, process_list):
        # 1. 프로세스 목록을 '도착 시간(arrival_time)' 기준으로
        #    최소 힙(min-heap)에 저장합니다. (도착 순서대로 꺼내기 위함)
        #    - 힙에는 (도착시간, PID, 프로세스) 튜플을 저장 (PID는 고유성 보장용)
        self.processes_to_arrive = []
        for proc in process_list:
            # 💡 주의: process_list를 재사용하려면 깊은 복사(deep copy)가 필요하지만,
            # 지금은 main.py에서 매번 parse_input_file()을 호출한다고 가정합니다.
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # 2. Ready 큐: FCFS이므로 간단한 FIFO 큐 (deque) 사용
        self.ready_queue = collections.deque()
        
        # 3. Waiting 큐: I/O 작업 중인 프로세스 관리
        #    (IO_완료시간, PID, 프로세스) 튜플을 저장하는 최소 힙
        self.waiting_queue = []
        
        # 4. 기타 상태 변수
        self.current_time = 0
        self.running_process = None
        self.completed_processes = [] # 통계용
        
        # 5. 통계 및 로깅
        self.gantt_chart = [] # (PID, 시작, 종료) 기록
        self.total_cpu_idle_time = 0 # (CPU 사용률 계산용)
        self.last_cpu_busy_time = 0 

    def run(self):
        """
        시뮬레이션 메인 루프
        """
        print("--- FCFS 시뮬레이션 시작 ---")

        # 모든 프로세스가 도착하고, Ready/Waiting 큐가 비고, 실행 중인 프로세스가 없을 때까지
        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            # 현재 시간에 도착한 프로세스가 있는지 확인
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time # 👈 (정확) Ready 큐 진입 시간 기록
                self.ready_queue.append(proc) # FCFS 큐의 맨 뒤에 추가
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입)")

            # --- 2. I/O 완료 처리 (I/O 인터럽트) ---
            # I/O 작업이 끝난 프로세스가 있는지 확인
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time # 👈 (정확) Ready 큐 재진입 시간 기록
                self.ready_queue.append(proc) # FCFS 큐의 맨 뒤에 추가
                print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입)")

            # --- 3. CPU 작업 처리 (Dispatcher 및 실행) ---
            
            # 3-1. 현재 실행 중인 프로세스가 없다면 (CPU가 비었다면)
            if not self.running_process:
                # Ready 큐에서 다음 프로세스를 가져옴 (FCFS)
                if self.ready_queue:
                    self.running_process = self.ready_queue.popleft() # 큐의 맨 앞을 꺼냄
                    self.running_process.state = Process.RUNNING
                    
                    # 💡 (정확) 대기 시간 통계 업데이트
                    # (현재 시간 - Ready 큐에 들어온 시간)
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait # 👈 누적 대기 시간에 합산
                    
                    # 간트 차트 기록
                    self.gantt_chart.append((self.running_process.pid, self.current_time)) # (PID, 시작시간)
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 실행 시작 (대기: {wait}ms, 총 대기: {self.running_process.wait_time}ms)")
                
                # CPU 유휴 상태 (Ready 큐에도 프로세스가 없음)
                else:
                    # 이번 타임 슬롯은 아무도 실행하지 않음
                    pass 

            # 3-2. 현재 실행 중인 프로세스가 있다면
            if self.running_process:
                proc = self.running_process
                
                # 3-2-a. CPU 버스트 1 감소
                proc.remaining_cpu_time -= 1
                
                # 3-2-b. CPU 버스트가 끝났는지 검사
                if proc.remaining_cpu_time == 0:
                    print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} CPU 버스트 완료")
                    
                    # 간트 차트 종료 시간 기록
                    start_time = self.gantt_chart[-1][1]
                    self.gantt_chart[-1] = (proc.pid, start_time, self.current_time + 1)
                    self.last_cpu_busy_time = self.current_time + 1
                    
                    # 다음 작업으로 인덱스 이동
                    proc.current_burst_index += 1

                    # 3-2-c. 다음 작업(I/O)이 있는지?
                    if proc.current_burst_index < len(proc.burst_pattern):
                        proc.state = Process.WAITING
                        io_duration = proc.burst_pattern[proc.current_burst_index]
                        
                        # I/O 완료 시간 계산하여 waiting_queue에 삽입
                        io_finish_time = self.current_time + 1 + io_duration
                        heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} I/O 시작 (대기 {io_duration}ms)")

                        # 다음 CPU 버스트 준비
                        proc.current_burst_index += 1
                        if proc.current_burst_index < len(proc.burst_pattern):
                            proc.remaining_cpu_time = proc.burst_pattern[proc.current_burst_index]

                    # 3-2-d. 모든 작업이 끝났는지? (종료)
                    else:
                        proc.state = Process.TERMINATED
                        proc.completion_time = self.current_time + 1
                        proc.turnaround_time = proc.completion_time - proc.arrival_time
                        self.completed_processes.append(proc)
                        print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")

                    # CPU 비우기
                    self.running_process = None

            # --- 4. 통계 업데이트 (CPU 유휴 시간) ---
            # (버그 코드 삭제됨 - 정확)
            if not self.running_process and not self.ready_queue and self.waiting_queue:
                pass 
            elif not self.running_process and not self.ready_queue and not self.waiting_queue:
                if self.processes_to_arrive:
                    pass 
            

            # --- 5. 시간 증가 ---
            self.current_time += 1
        
        # 시뮬레이션 종료 후 총 시간 기록
        total_simulation_time = self.current_time
        
        # (CPU 사용률 계산이 더 정확해졌습니다)
        total_cpu_busy_time = 0
        idle_time_start = 0
        for pid, start, end in self.gantt_chart:
            # 간트 차트의 '빈 시간'을 계산
            idle_duration = start - idle_time_start
            if idle_duration > 0:
                self.total_cpu_idle_time += idle_duration
            
            total_cpu_busy_time += (end - start)
            idle_time_start = end # 다음 유휴 시간 계산을 위해 시작점 갱신

        # 마지막 작업이 끝난 후 총 시간까지의 유휴 시간
        if total_simulation_time > idle_time_start:
             self.total_cpu_idle_time += (total_simulation_time - idle_time_start)

        print("--- FCFS 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)

    def print_results(self, total_time, total_busy_time):
        """
        최종 통계 결과를 출력합니다.
        (CPU 사용률 계산을 위해 매개변수 추가)
        """
        print("\n--- 📊 FCFS 최종 결과 ---")
        
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
        
        # CPU 사용률 (교수님 공식: (총 시간 - CPU 유휴 시간) / 총 시간)
        # (total_busy_time / total_time) 과 동일
        cpu_utilization = (total_busy_time / total_time) * 100 if total_time > 0 else 0
        
        print("\n--- 요약 ---")
        print(f"평균 반환 시간 (Avg TT) : {avg_tt:.2f}")
        print(f"평균 대기 시간 (Avg WT) : {avg_wt:.2f}")
        print(f"총 실행 시간          : {total_time}")
        print(f"CPU 총 유휴 시간      : {self.total_cpu_idle_time}")
        print(f"CPU 총 사용 시간      : {total_busy_time}")
        print(f"CPU 사용률 (Util)   : {cpu_utilization:.2f} %")

        print("\n--- 간트 차트 (Gantt Chart) ---")
        # (pid, start, end)
        print("PID | 시작 -> 종료")
        print("-------------------")
        for pid, start, end in self.gantt_chart:
            print(f"{pid: <3} | {start: >3} -> {end: >3} (수행: {end-start}ms)")