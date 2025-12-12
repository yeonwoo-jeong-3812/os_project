import collections
import heapq 
from process import Process, parse_input_file
from sync import get_resource, get_deadlock_strategy, check_safe_state, detect_deadlock

class SimulatorPriorityStatic: # 👈 1. 클래스 이름 변경
    """
    선점형 정적 우선순위(Preemptive Priority) 시뮬레이터
    """
    def __init__(self, process_list, context_switch_overhead=1):
        self.processes_to_arrive = []
        for proc in process_list:
            heapq.heappush(self.processes_to_arrive, (proc.arrival_time, proc.pid, proc))

        # --- 💡 2. Ready 큐: 우선순위 기준 최소 힙 ---
        # (우선순위, PID, 프로세스) 튜플을 저장
        self.ready_queue = [] 
        
        self.waiting_queue = []
        self.current_time = 0
        self.running_process = None
        self.completed_processes = []
        self.gantt_chart = []
        self.total_cpu_idle_time = 0
        self.last_cpu_busy_time = 0 

    
        # [ ]
        self.context_switches = 0
        self.context_switch_overhead = context_switch_overhead
        self.total_overhead_time = 0
        self.cpu_was_idle = True
        self.overhead_remaining = 0
        
        # [ ]
        self.queue_log = []

    def run(self):
        print(f"\n---  ---") 

        # [ ]
        def get_priority_key(proc):
            """
            프로세스의 현재 동적 우선순위 튜플을 반환합니다.
            (0-tick 명령어 최우선)
            """
            burst = proc.get_current_burst()
            cmd_prio = 1 # 기본값 (CPU)
            
            if burst and burst[0] != 'CPU':
                cmd_prio = 0 # 0-tick (LOCK, UNLOCK)
            
            # (명령어 우선순위, 정적 우선순위, PID)
            return (cmd_prio, proc.static_priority, proc.pid)


        while self.processes_to_arrive or self.ready_queue or self.waiting_queue or self.running_process:
            
            # --- 1. 신규 프로세스 도착 처리 ---
            while self.processes_to_arrive and self.processes_to_arrive[0][0] <= self.current_time:
                arrival, pid, proc = heapq.heappop(self.processes_to_arrive)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                current_burst = proc.get_current_burst()
                if current_burst:
                    # (튜플, 프로세스)로 힙에 저장
                    heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 (Ready 큐 진입, Prio: {proc.static_priority})")
                else:
                    # 도착하자마자 할 일이 없는 프로세스 (즉시 종료)
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} 도착 즉시 종료")

            # --- 2. I/O 완료 처리 ---
            while self.waiting_queue and self.waiting_queue[0][0] <= self.current_time:
                io_finish_time, pid, proc = heapq.heappop(self.waiting_queue)
                proc.state = Process.READY
                proc.last_ready_time = self.current_time
                
                current_burst = proc.get_current_burst()
                if current_burst:
                    heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 (Ready 큐 진입, Prio: {proc.static_priority})")
                else:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {pid} I/O 완료 후 종료")

            # --- 3. 선점(Preemption) 로직 (우선순위 기준) ---
            if (self.running_process and 
                self.running_process.get_current_burst() and
                self.running_process.get_current_burst()[0] == 'CPU' and 
                self.ready_queue):
                
                best_prio_tuple, best_proc = self.ready_queue[0]
                running_prio_tuple = get_priority_key(self.running_process)
                
                if best_prio_tuple < running_prio_tuple:
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선점됨 (새 작업 P{best_proc.pid} 우선순위 높음)")
                    
                    if self.gantt_chart and self.gantt_chart[-1][0] == self.running_process.pid and len(self.gantt_chart[-1]) == 2:
                        self.gantt_chart[-1] = (self.running_process.pid, self.gantt_chart[-1][1], self.current_time)
                        self.last_cpu_busy_time = self.current_time

                    proc = self.running_process
                    proc.state = Process.READY
                    proc.last_ready_time = self.current_time
                    heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                    
                    self.running_process = None
            
            # --- 3-1. CPU 작업 처리 (Dispatcher) ---
            if not self.running_process:
                if self.ready_queue:
                    prio_key, self.running_process = heapq.heappop(self.ready_queue)
                    
                    self.running_process.state = Process.RUNNING
                    
                    if not self.cpu_was_idle:
                        self.context_switches += 1
                    self.cpu_was_idle = False
                    wait = self.current_time - self.running_process.last_ready_time
                    self.running_process.wait_time += wait
                    
                    print(f"[Time {self.current_time:3d}] 프로세스 {self.running_process.pid} 선택됨 (Prio: {prio_key[1]}, Cmd: {'0-tick' if prio_key[0]==0 else 'CPU'}, 대기: {wait}ms)")
                
                else:
                    self.cpu_was_idle = True
                    pass 

            # --- 3-2. CPU 실행 ---
            if self.running_process:
                proc = self.running_process
                current_burst = proc.get_current_burst()
                
                if not current_burst:
                    proc.state = Process.TERMINATED
                    proc.completion_time = self.current_time
                    proc.turnaround_time = proc.completion_time - proc.arrival_time
                    self.completed_processes.append(proc)
                    print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    self.running_process = None

                # 'CPU'
                elif current_burst[0] == 'CPU':
                    if (not self.gantt_chart or self.gantt_chart[-1][0] != proc.pid or len(self.gantt_chart[-1]) == 3):
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
                            proc.state = Process.READY
                            proc.last_ready_time = self.current_time + 1
                            heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                        else:
                            proc.state = Process.TERMINATED
                            proc.completion_time = self.current_time + 1
                            proc.turnaround_time = proc.completion_time - proc.arrival_time
                            self.completed_processes.append(proc)
                            print(f"[Time {self.current_time + 1:3d}] 프로세스 {proc.pid} 종료")
                        
                        self.running_process = None
                    
                # 'IO'
                elif current_burst[0] == 'IO':
                    io_duration = current_burst[1]
                    proc.state = Process.WAITING
                    io_finish_time = self.current_time + io_duration
                    heapq.heappush(self.waiting_queue, (io_finish_time, proc.pid, proc))
                    print(f"[Time {self.current_time:3d}]  {proc.pid} I/O ( {io_duration}ms)")

                    proc.advance_to_next_burst()
                    self.running_process = None

                # 'LOCK'
                elif current_burst[0] == 'LOCK':
                    resource_name = current_burst[1]
                    resource = get_resource(resource_name)
                    
                    if not resource:
                        proc.advance_to_next_burst()
                    else:
                        strategy = get_deadlock_strategy()
                        
                        # === . ===
                        if strategy == 'prevention':
                            # --- 1. . ---
                            max_held_id = -1
                            if proc.held_resources:
                                max_held_id = max(res.id for res in proc.held_resources)
                            
                            if resource.id < max_held_id:
                                print(f"!!! [Time {self.current_time:3d}] : P{proc.pid} (R_ID: {max_held_id}) R_ID {resource.id} . ")
                                
                                for res in proc.held_resources:
                                    woken_process = res.unlock(proc, self.current_time)
                                    if woken_process:
                                        woken_process.state = Process.READY
                                        woken_process.last_ready_time = self.current_time
                                        woken_process.advance_to_next_burst()
                                        heapq.heappush(self.ready_queue, (get_priority_key(woken_process), woken_process))
                                        print(f"[Time {self.current_time:3d}] P{woken_process.pid} '{res.name}' (Ready ")
                                
                                proc.state = Process.TERMINATED
                                proc.completion_time = self.current_time
                                proc.turnaround_time = proc.completion_time - proc.arrival_time
                                self.completed_processes.append(proc)
                                self.running_process = None
                            else:
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ...")
                                if resource.lock(proc, self.current_time):
                                    print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ")
                                    proc.held_resources.append(resource)
                                    proc.advance_to_next_burst()
                                else:
                                    print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' . ( ")
                                    proc.state = Process.WAITING
                                    self.running_process = None
                        
                        elif strategy == 'avoidance':
                            # --- 2. . ---
                            all_procs = [proc] + [p for _, _, p in self.ready_queue] + [p for _, _, p in self.waiting_queue]
                            if self.running_process:
                                all_procs.append(self.running_process)
                            
                            if check_safe_state(proc, resource, all_procs):
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ... ( ")
                                if resource.lock(proc, self.current_time):
                                    print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ")
                                    proc.held_resources.append(resource)
                                    proc.advance_to_next_burst()
                                else:
                                    print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' . ( ")
                                    proc.state = Process.WAITING
                                    self.running_process = None
                            else:
                                print(f"!!! [Time {self.current_time:3d}] : P{proc.pid} '{resource_name}' . ")
                                proc.state = Process.WAITING
                                self.running_process = None
                        
                        elif strategy == 'detection':
                            # --- 3. . ---
                            print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ...")
                            if resource.lock(proc, self.current_time):
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ")
                                proc.held_resources.append(resource)
                                proc.advance_to_next_burst()
                            else:
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' . ( ")
                                proc.state = Process.WAITING
                                self.running_process = None
                                
                                # 
                                all_procs = [p for _, _, p in self.ready_queue] + [p for _, _, p in self.waiting_queue]
                                if self.running_process:
                                    all_procs.append(self.running_process)
                                all_procs.append(proc)
                                
                                deadlocked_pids = detect_deadlock(all_procs)
                                if deadlocked_pids:
                                    print(f"!!! [Time {self.current_time:3d}] : P{deadlocked_pids} ")
                                    
                                    # 
                                    victim = None
                                    max_priority = -1
                                    for p in all_procs:
                                        if p.pid in deadlocked_pids and p.static_priority > max_priority:
                                            max_priority = p.static_priority
                                            victim = p
                                    
                                    if victim:
                                        print(f"!!! [Time {self.current_time:3d}] : P{victim.pid} ( : {victim.static_priority})")
                                        
                                        # 
                                        for res in victim.held_resources[:]:
                                            woken_process = res.unlock(victim, self.current_time)
                                            if woken_process:
                                                woken_process.state = Process.READY
                                                woken_process.last_ready_time = self.current_time
                                                woken_process.advance_to_next_burst()
                                                heapq.heappush(self.ready_queue, (get_priority_key(woken_process), woken_process))
                                                print(f"[Time {self.current_time:3d}] P{woken_process.pid} '{res.name}' (Ready ")
                                        
                                        # 
                                        victim.state = Process.TERMINATED
                                        victim.completion_time = self.current_time
                                        victim.turnaround_time = victim.completion_time - victim.arrival_time
                                        self.completed_processes.append(victim)
                                        
                                        # waiting_queue
                                        self.waiting_queue = [(t, p, pr) for t, p, pr in self.waiting_queue if pr.pid != victim.pid]
                                        heapq.heapify(self.waiting_queue)
                        
                        else:
                            # ( )
                            print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ...")
                            if resource.lock(proc, self.current_time):
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' ")
                                proc.held_resources.append(resource)
                                proc.advance_to_next_burst()
                            else:
                                print(f"[Time {self.current_time:3d}]  {proc.pid} '{resource_name}' . ( ")
                                proc.state = Process.WAITING
                                self.running_process = None
                            

                    if self.running_process:
                        next_burst = proc.get_current_burst()
                        if next_burst:
                            proc.state = Process.READY
                            proc.last_ready_time = self.current_time
                            heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                        else:
                            proc.state = Process.TERMINATED
                            proc.completion_time = self.current_time
                            proc.turnaround_time = proc.completion_time - proc.arrival_time
                            self.completed_processes.append(proc)
                            print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                        self.running_process = None

                # 'UNLOCK'
                elif current_burst[0] == 'UNLOCK':
                    resource_name = current_burst[1]
                    resource = get_resource(resource_name)
                    
                    if not resource:
                        print(f"!!! [Time {self.current_time:3d}] 오류: P{proc.pid}가 존재하지 않는 자원 '{resource_name}'을(를) Unlock하려 합니다.")
                        proc.advance_to_next_burst()
                    else:
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid}이(가) '{resource_name}' Unlock 시도...")
                        
                        # [버그 수정 로직 시작]
                        if resource in proc.held_resources:
                            proc.held_resources.remove(resource)
                        # [버그 수정 로직 끝]

                        woken_process = resource.unlock(proc, self.current_time)
                        
                        if woken_process:
                            woken_process.state = Process.READY
                            woken_process.last_ready_time = self.current_time
                            
                            woken_process.advance_to_next_burst() 
                            
                            heapq.heappush(self.ready_queue, (get_priority_key(woken_process), woken_process))
                            print(f"[Time {self.current_time:3d}] 프로세스 {woken_process.pid}이(가) '{resource_name}' 획득 (Ready 큐 진입)")
                        
                        proc.advance_to_next_burst()

                    # --- 👇 [ 243행 주변의 최종 복귀/종료 로직 ] ---
                    next_burst = proc.get_current_burst()
                    if next_burst:
                        proc.state = Process.READY
                        proc.last_ready_time = self.current_time
                        heapq.heappush(self.ready_queue, (get_priority_key(proc), proc))
                    else:
                        proc.state = Process.TERMINATED
                        proc.completion_time = self.current_time
                        proc.turnaround_time = proc.completion_time - proc.arrival_time
                        self.completed_processes.append(proc)
                        print(f"[Time {self.current_time:3d}] 프로세스 {proc.pid} 종료")
                    self.running_process = None
                    # --- 👆 [ 수정 끝 ] ---

            # --- 4. 큐 상태 로깅 ---
            ready_pids = [item[1].pid for item in self.ready_queue]  # (priority_tuple, proc)
            waiting_pids = [item[1] for item in self.waiting_queue]  # (time, pid, proc)
            self.queue_log.append((self.current_time, ready_pids.copy(), waiting_pids.copy()))

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

        print(f"--- 정적 우선순위 시뮬레이션 종료 ---")
        self.print_results(total_simulation_time, total_cpu_busy_time)
        
    
    def print_results(self, total_time, total_busy_time):
        """
        최종 통계 결과를 출력합니다. (정적 우선순위)
        """
        print(f"\n--- 📊 정적 우선순위 최종 결과 ---")

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