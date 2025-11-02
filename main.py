# 1단계의 파싱 함수
from process import parse_input_file 
# 2단계의 FCFS 시뮬레이터
from simulator_fcfs import SimulatorFCFS
# 3단계의 RR 시뮬레이터 
from simulator_rr import SimulatorRR
# 4단계의 SJF(SRTF) 시뮬레이터
from simulator_sjf import SimulatorSJF
# 5단계의 정적 우선순위 시뮬레이터
from simulator_priority_static import SimulatorPriorityStatic
# 6단계의 동적 우선순위 시뮬레이터
from simulator_priority_dynamic import SimulatorPriorityDynamic
# 7단계의 MLFQ 시뮬레이터
from simulator_mlfq import SimulatorMLFQ
# 8단계의 실시간 시뮬레이터
from simulator_rm import SimulatorRM     # 👈 [RM] 추가
from simulator_edf import SimulatorEDF    # 👈 [EDF] 추가

def main():
    # --- FCFS 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_fcfs = SimulatorFCFS(non_rt_processes)
    sim_fcfs.run()

    # --- RR 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_rr_4 = SimulatorRR(non_rt_processes, time_quantum=4)
    sim_rr_4.run()
    
    # --- SJF(SRTF) 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_sjf = SimulatorSJF(non_rt_processes)
    sim_sjf.run()

    # --- 정적 우선순위 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_prio = SimulatorPriorityStatic(non_rt_processes)
    sim_prio.run()

    # --- 동적 우선순위(Aging) 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_prio_dyn = SimulatorPriorityDynamic(non_rt_processes, aging_factor=10)
    sim_prio_dyn.run()
    
    # --- 다단계 피드백 큐(MLFQ) 실행 (비-실시간 프로세스) ---
    non_rt_processes = [p for p in parse_input_file("sample_input.txt") if p.period == 0]
    sim_mlfq = SimulatorMLFQ(non_rt_processes)
    sim_mlfq.run()
    
    # --- 💡 실시간 스케줄링 실행 (실시간 프로세스 P5, P6만) ---
    
    # --- RM 실행 ---
    rt_processes_rm = parse_input_file("sample_input.txt") # 실시간+비실시간 모두 로드
    sim_rm = SimulatorRM(rt_processes_rm) # 시뮬레이터가 내부에서 필터링
    sim_rm.run()
    
    # --- EDF 실행 ---
    rt_processes_edf = parse_input_file("sample_input.txt")
    sim_edf = SimulatorEDF(rt_processes_edf) # 시뮬레이터가 내부에서 필터링
    sim_edf.run()


if __name__ == "__main__":
    main()