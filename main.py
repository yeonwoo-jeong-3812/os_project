# 기존 시뮬레이터들 import
from process import parse_input_file 
from simulator_fcfs import SimulatorFCFS
from simulator_rr import SimulatorRR
from simulator_sjf import SimulatorSJF
from simulator_priority_static import SimulatorPriorityStatic
from simulator_priority_dynamic import SimulatorPriorityDynamic
from simulator_mlfq import SimulatorMLFQ
from simulator_rm import SimulatorRM
from simulator_edf import SimulatorEDF
from sync import initialize_resources

# 시각화 도구 import
from visualizer import SchedulingVisualizer
import os

import copy  # 깊은 복사(deep copy)를 위해 추가
from generator import generate_random_processes, generate_random_realtime_processes # 방금 만든 generator import

SIMULATION_MODE = 'PERFORMANCE'

def run_simulations_with_visualization():
    """
    Run all simulations and visualize results (display on screen)
    """
    master_process_list = [] # 모든 시뮬레이션이 공유할 마스터 리스트
    
    # --- 1. [공통] 프로세스 로드/생성 ---
    if SIMULATION_MODE == 'PERFORMANCE':
        print("--- 🚀 모드: 알고리즘 성능 비교 (랜덤 생성) ---")
        # 1. 비-실시간 프로세스 리스트 (FCFS, RR, SJF...)
        master_process_list_normal = generate_random_processes(num_processes=8, io_probability=0.5)
        # 2. 실시간 프로세스 리스트 (RM, EDF 용)
        master_process_list_realtime = generate_random_realtime_processes(num_processes=4, max_period=50)
        
    elif SIMULATION_MODE == 'SYNC':
        print("--- 🔬 모드: 동기화 기능 테스트 (파일 입력) ---")
        RESOURCE_NAMES = ["R1", "R2", "Printer", "File"] 
        initialize_resources(RESOURCE_NAMES)
        INPUT_FILENAME = "sample_input.txt" 
        master_process_list = parse_input_file(INPUT_FILENAME)
        if not master_process_list:
            print(f"'{INPUT_FILENAME}'을 읽는 데 실패했습니다.")
            return
            
    else:
        print("오류: SIMULATION_MODE가 잘못 설정되었습니다.")
        return
            
    # --- 2. [공통] 시각화 도구 생성 ---
    # (if/elif 바깥에 딱 한 번만 있어야 합니다)
    visualizer = SchedulingVisualizer()
    
    # --- 3. [분기] 모드별 실행 ---
    
    if SIMULATION_MODE == 'SYNC':
        
        # 'SYNC' 모드에서는 로그를 봐야 하므로 stdout 차단을 절대 사용하면 안 됩니다.
        
        print("\n--- (동기화 테스트는 FCFS만 실행합니다) ---")
        print("[1/1] FCFS (Sync Test)...", end=" ")
        
        # 'SYNC' 모드는 비-실시간 프로세스만 테스트한다고 가정
        sync_test_processes = [p for p in copy.deepcopy(master_process_list) if p.period == 0]
        sim_fcfs = SimulatorFCFS(sync_test_processes)
        
        # 로그 출력을 위해 바로 run() 호출
        sim_fcfs.run() 
        print("✓")
        
        # FCFS에 대한 시각화만 실행
        visualizer.visualize_algorithm_complete(sim_fcfs.gantt_chart, sim_fcfs.completed_processes, "FCFS (Sync Test)")
        
        print("\n" + "=" * 70)
        print("✅ 동기화 시뮬레이션 완료! (로그 확인)")
        print("=" * 70)

    elif SIMULATION_MODE == 'PERFORMANCE':
        
        # (***여기가 중요***)
        # (PERFORMANCE 모드 전용 변수 및 출력)
        
        # Storage for comparison results
        comparison_results = {}
        realtime_results = {}
        
        print("=" * 70)
        print("CPU Scheduling Simulation & Visualization (Performance Mode)")
        print("=" * 70)
        print("\nRunning simulations and displaying graphs...\n")
        
        # Suppress matplotlib warnings
        import warnings
        warnings.filterwarnings('ignore')
    
    # ========== Non-Realtime Scheduling Algorithms ==========
    
    # 1. FCFS
    print("[1/8] FCFS...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_fcfs = SimulatorFCFS(non_rt_processes)
    sim_fcfs.run() # (로그 차단 코드 없음)
        
    comparison_results['FCFS'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_fcfs.completed_processes) / len(sim_fcfs.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_fcfs.completed_processes) / len(sim_fcfs.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_fcfs.gantt_chart) / sim_fcfs.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_fcfs.gantt_chart, sim_fcfs.completed_processes, "FCFS")
    print("✓")
    
    # 2. RR (Q=4)
    print("[2/8] RR (Q=4)...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_rr = SimulatorRR(non_rt_processes, time_quantum=4)
    sim_rr.run() # (로그 차단 코드 없음)
        
    comparison_results['RR(Q=4)'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_rr.completed_processes) / len(sim_rr.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_rr.completed_processes) / len(sim_rr.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_rr.gantt_chart) / sim_rr.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_rr.gantt_chart, sim_rr.completed_processes, "RR (Q=4)")
    print("✓")
    
    # 3. SJF (SRTF)
    print("[3/8] SJF (SRTF)...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_sjf = SimulatorSJF(non_rt_processes)
    sim_sjf.run() # (로그 차단 코드 없음)
        
    comparison_results['SJF'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_sjf.completed_processes) / len(sim_sjf.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_sjf.completed_processes) / len(sim_sjf.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_sjf.gantt_chart) / sim_sjf.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_sjf.gantt_chart, sim_sjf.completed_processes, "SJF (Preemptive)")
    print("✓")
    
    # 4. Static Priority
    print("[4/8] Priority (Static)...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_prio = SimulatorPriorityStatic(non_rt_processes)
    sim_prio.run() # (로그 차단 코드 없음)
        
    comparison_results['Priority(Static)'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_prio.completed_processes) / len(sim_prio.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_prio.completed_processes) / len(sim_prio.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_prio.gantt_chart) / sim_prio.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_prio.gantt_chart, sim_prio.completed_processes, "Priority (Static)")
    print("✓")
    
    # 5. Dynamic Priority (Aging)
    print("[5/8] Priority (Aging)...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_prio_dyn = SimulatorPriorityDynamic(non_rt_processes, aging_factor=10)
    sim_prio_dyn.run() # (로그 차단 코드 없음)
        
    comparison_results['Priority(Aging)'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_prio_dyn.completed_processes) / len(sim_prio_dyn.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_prio_dyn.completed_processes) / len(sim_prio_dyn.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_prio_dyn.gantt_chart) / sim_prio_dyn.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_prio_dyn.gantt_chart, sim_prio_dyn.completed_processes, "Priority (Aging)")
    print("✓")
    
    # 6. MLFQ
    print("[6/8] MLFQ...", end=" ")
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_mlfq = SimulatorMLFQ(non_rt_processes)
    sim_mlfq.run() # (로그 차단 코드 없음)
        
    comparison_results['MLFQ'] = {
        'avg_turnaround': sum(p.turnaround_time for p in sim_mlfq.completed_processes) / len(sim_mlfq.completed_processes),
        'avg_waiting': sum(p.wait_time for p in sim_mlfq.completed_processes) / len(sim_mlfq.completed_processes),
        'cpu_utilization': (sum(end - start for pid, start, end in sim_mlfq.gantt_chart) / sim_mlfq.current_time) * 100
    }
        
    visualizer.visualize_algorithm_complete(sim_mlfq.gantt_chart, sim_mlfq.completed_processes, "MLFQ")
    print("✓")
    
    # ========== Realtime Scheduling Algorithms ==========
    
    # 7. RM (Rate Monotonic)
    print("[7/8] RM (Realtime)...", end=" ")
    rt_processes_rm = copy.deepcopy(master_process_list_realtime)
    sim_rm = SimulatorRM(rt_processes_rm)
    sim_rm.run() # (로그 차단 코드 없음)
        
    if sim_rm.completed_processes:
        # [수정됨] ZeroDivision 방지 코드
        rm_n = len(sim_rm.completed_processes)
        realtime_results['RM'] = {
            'deadline_misses': sim_rm.deadline_misses,
            'avg_turnaround': (sum(p.turnaround_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_rm.gantt_chart) / sim_rm.current_time) * 100 if sim_rm.current_time > 0 else 0
        }
        
        # --- 👇 [버그 수정] ---
        # (visualizer 호출을 if 블록 안으로 이동)
        visualizer.visualize_algorithm_complete(sim_rm.gantt_chart, sim_rm.completed_processes, "Rate Monotonic")
    
    print("✓") # (print("✓")는 if 블록 바깥에 둬도 됩니다)
    # --- 👆 [버그 수정 끝] ---
    
    # 8. EDF (Earliest Deadline First)
    print("[8/8] EDF (Realtime)...", end=" ")
    rt_processes_edf = copy.deepcopy(master_process_list_realtime)
    sim_edf = SimulatorEDF(rt_processes_edf)
    sim_edf.run() # (로그 차단 코드 없음)
        
        # [수정됨] sim_edf.completed_projects  -> sim_edf.completed_processes
    if sim_edf.completed_processes:
        realtime_results['EDF'] = {
            'deadline_misses': sim_edf.deadline_misses,
            'avg_turnaround': sum(p.turnaround_time for p in sim_edf.completed_processes) / len(sim_edf.completed_processes),
            'avg_waiting': sum(p.wait_time for p in sim_edf.completed_processes) / len(sim_edf.completed_processes),
            'cpu_utilization': (sum(end - start for pid, start, end in sim_edf.gantt_chart) / sim_edf.current_time) * 100
        }
            
        visualizer.visualize_algorithm_complete(sim_edf.gantt_chart, sim_edf.completed_processes, "EDF")
        print("✓")
    
    # ========== Generate Comparison Charts ==========
    
    print("\nGenerating comparison charts...", end=" ")
    
    # Non-realtime algorithm comparison
    visualizer.compare_algorithms(comparison_results)
    
    # Realtime algorithm comparison
    if realtime_results:
        visualizer.create_realtime_analysis(realtime_results)
    
    # All Gantt Charts in one figure
    all_gantt_charts = {
        'FCFS': sim_fcfs.gantt_chart,
        'RR(Q=4)': sim_rr.gantt_chart,
        'SJF': sim_sjf.gantt_chart,
        'Priority(Static)': sim_prio.gantt_chart,
        'Priority(Aging)': sim_prio_dyn.gantt_chart,
        'MLFQ': sim_mlfq.gantt_chart,
    }
    visualizer.visualize_all_gantt_charts(all_gantt_charts)
    
    print("✓")
    
    print("\n" + "=" * 70)
    print("✅ All simulations complete! Graphs displayed on screen.")
    print("=" * 70)
    
    # Summary statistics
    print("\n📊 Algorithm Performance Summary:")
    print("-" * 70)
    print(f"{'Algorithm':<20} {'Avg Turnaround':>15} {'Avg Waiting':>15} {'CPU Util':>15}")
    print("-" * 70)
    for alg, stats in comparison_results.items():
        print(f"{alg:<20} {stats['avg_turnaround']:>14.2f}ms {stats['avg_waiting']:>14.2f}ms {stats['cpu_utilization']:>14.2f}%")
    
    if realtime_results:
        print("\n📊 Realtime Scheduling Summary:")
        print("-" * 70)
        print(f"{'Algorithm':<20} {'Deadline Misses':>20} {'Avg Turnaround':>15}")
        print("-" * 70)
        for alg, stats in realtime_results.items():
            print(f"{alg:<20} {stats['deadline_misses']:>20} {stats['avg_turnaround']:>14.2f}ms")
    
    print("\n" + "=" * 70)

if __name__ == "__main__":
    run_simulations_with_visualization()
