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


def run_simulations_with_visualization():
    """
    Run all simulations and visualize results (display on screen)
    """
    
    # --- 1. 모드 선택 프롬프트 ---
    SIMULATION_MODE = ''
    while SIMULATION_MODE not in ['1', '2']:
        print("\n" + "=" * 50)
        print("          운영체제 스케줄러 시뮬레이션")
        print("=" * 50)
        print("모드를 선택하세요:")
        print("  [1] PERFORMANCE (알고리즘 성능 비교 - 랜덤 생성)")
        print("  [2] SYNC (동기화/교착상태 테스트 - 파일 입력)")
        SIMULATION_MODE = input("선택 (1 또는 2): ").strip()

    if SIMULATION_MODE == '1':
        SIMULATION_MODE = 'PERFORMANCE'
    elif SIMULATION_MODE == '2':
        SIMULATION_MODE = 'SYNC'

    master_process_list_normal = []
    master_process_list_realtime = []
    
    # --- 2. 모드에 따른 프로세스 데이터 로드 ---
    if SIMULATION_MODE == 'PERFORMANCE':
        print("--- 🚀 모드: 알고리즘 성능 비교 (랜덤 생성) ---")
        master_process_list_normal = generate_random_processes(num_processes=8, io_probability=0.5)
        master_process_list_realtime = generate_random_realtime_processes(num_processes=4, max_period=50)
        
    elif SIMULATION_MODE == 'SYNC':
        print("--- 🔬 모드: 동기화 기능 테스트 ---")
        
        # --- 👇 [ 1. 하위 메뉴 추가 ] 👇 ---
        sync_choice = ''
        while sync_choice not in ['1', '2']:
            print("\n동기화 테스트 시나리오를 선택하세요:")
            print("  [1] 고전적 동기화 문제 (우선순위 역전)")
            print("  [2] 교착상태 예방 (자원 순서 할당)")
            sync_choice = input("선택 (1 또는 2): ").strip()
        
        INPUT_FILENAME = ""
        if sync_choice == '1':
            INPUT_FILENAME = "producer_consumer.txt"
            print(f"--- [1] 우선순위 역전 시나리오 로드 ({INPUT_FILENAME}) ---")
        elif sync_choice == '2':
            INPUT_FILENAME = "deadlock_prevention.txt"
            print(f"--- [2] 교착상태 예방 시나리오 로드 ({INPUT_FILENAME}) ---")
        # --- 👆 [ 하위 메뉴 끝 ] 👆 ---
        
        # (모든 시나리오의 자원을 포함해야 함)
        RESOURCE_NAMES = ["R1", "R2", "Buffer", "Printer", "File"] 
        initialize_resources(RESOURCE_NAMES)
        
        master_process_list_normal = parse_input_file(INPUT_FILENAME) 
        if not master_process_list_normal:
            print(f"!!! 오류: '{INPUT_FILENAME}'을(를) 찾을 수 없거나 파일이 비어있습니다.")
            print("!!! 1단계, 2단계에 따라 파일을 생성했는지 확인하세요.")
            return
            
    # --- 3. [공통] 시각화 도구 생성 ---
    visualizer = SchedulingVisualizer()
    
    # --- 4. [분기] 모드별 시뮬레이션 실행 ---
    
    if SIMULATION_MODE == 'SYNC':
        
        print("\n--- (동기화 테스트는 '정적 우선순위'로 실행합니다) ---")
        print("[1/1] Priority (Sync Test)...", end=" ")
        
        sync_test_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_prio = SimulatorPriorityStatic(sync_test_processes)
        
        sim_prio.run() 
        print("✓")
        
        # (시나리오 이름에 맞게 그래프 제목 변경)
        scenario_name = "Priority (Sync: Priority Inversion)" if sync_choice == '1' else "Priority (Sync: Deadlock Prevention)"
        visualizer.visualize_algorithm_complete(sim_prio.gantt_chart, sim_prio.completed_processes, scenario_name)
        
        print("\n" + "=" * 70)
        print("✅ 동기화 시뮬레이션 완료! (로그 확인)")
        print("=" * 70)

    elif SIMULATION_MODE == 'PERFORMANCE':
        
        # PERFORMANCE 모드 전용 변수
        comparison_results = {}
        realtime_results = {}
        
        print("=" * 70)
        print("CPU Scheduling Simulation & Visualization (Performance Mode)")
        print("=" * 70)
        print("\nRunning simulations and displaying graphs...\n")
        
        import warnings
        warnings.filterwarnings('ignore')
    
        # ========== Non-Realtime Scheduling Algorithms ==========
    
        # 1. FCFS
        print("[1/8] FCFS...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_fcfs = SimulatorFCFS(non_rt_processes)
        sim_fcfs.run()
        
        fcfs_n = len(sim_fcfs.completed_processes)
        comparison_results['FCFS'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_fcfs.completed_processes) / fcfs_n) if fcfs_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_fcfs.completed_processes) / fcfs_n) if fcfs_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_fcfs.gantt_chart) / sim_fcfs.current_time) * 100 if sim_fcfs.current_time > 0 else 0
        }
        
        visualizer.visualize_algorithm_complete(sim_fcfs.gantt_chart, sim_fcfs.completed_processes, "FCFS")
        print("✓")
        
        # 2. RR (Q=4)
        print("[2/8] RR (Q=4)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_rr = SimulatorRR(non_rt_processes, time_quantum=4)
        sim_rr.run()
        
        rr_n = len(sim_rr.completed_processes)
        comparison_results['RR(Q=4)'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_rr.completed_processes) / rr_n) if rr_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_rr.completed_processes) / rr_n) if rr_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_rr.gantt_chart) / sim_rr.current_time) * 100 if sim_rr.current_time > 0 else 0
        }
        
        visualizer.visualize_algorithm_complete(sim_rr.gantt_chart, sim_rr.completed_processes, "RR (Q=4)")
        print("✓")
        
        # 3. SJF (SRTF)
        print("[3/8] SJF (SRTF)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_sjf = SimulatorSJF(non_rt_processes)
        sim_sjf.run()
        
        sjf_n = len(sim_sjf.completed_processes)
        comparison_results['SJF'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_sjf.completed_processes) / sjf_n) if sjf_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_sjf.completed_processes) / sjf_n) if sjf_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_sjf.gantt_chart) / sim_sjf.current_time) * 100 if sim_sjf.current_time > 0 else 0
        }
            
        visualizer.visualize_algorithm_complete(sim_sjf.gantt_chart, sim_sjf.completed_processes, "SJF (Preemptive)")
        print("✓")
        
        # 4. Static Priority
        print("[4/8] Priority (Static)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_prio = SimulatorPriorityStatic(non_rt_processes)
        sim_prio.run()
        
        prio_n = len(sim_prio.completed_processes)
        comparison_results['Priority(Static)'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_prio.completed_processes) / prio_n) if prio_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_prio.completed_processes) / prio_n) if prio_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_prio.gantt_chart) / sim_prio.current_time) * 100 if sim_prio.current_time > 0 else 0
        }
            
        visualizer.visualize_algorithm_complete(sim_prio.gantt_chart, sim_prio.completed_processes, "Priority (Static)")
        print("✓")
        
        # 5. Dynamic Priority (Aging)
        print("[5/8] Priority (Aging)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_prio_dyn = SimulatorPriorityDynamic(non_rt_processes, aging_factor=10)
        sim_prio_dyn.run()
        
        prio_dyn_n = len(sim_prio_dyn.completed_processes)
        comparison_results['Priority(Aging)'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_prio_dyn.completed_processes) / prio_dyn_n) if prio_dyn_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_prio_dyn.completed_processes) / prio_dyn_n) if prio_dyn_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_prio_dyn.gantt_chart) / sim_prio_dyn.current_time) * 100 if sim_prio_dyn.current_time > 0 else 0
        }
            
        visualizer.visualize_algorithm_complete(sim_prio_dyn.gantt_chart, sim_prio_dyn.completed_processes, "Priority (Aging)")
        print("✓")
        
        # 6. MLFQ
        print("[6/8] MLFQ...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_mlfq = SimulatorMLFQ(non_rt_processes)
        sim_mlfq.run()
        
        mlfq_n = len(sim_mlfq.completed_processes)
        comparison_results['MLFQ'] = {
            'avg_turnaround': (sum(p.turnaround_time for p in sim_mlfq.completed_processes) / mlfq_n) if mlfq_n > 0 else 0,
            'avg_waiting': (sum(p.wait_time for p in sim_mlfq.completed_processes) / mlfq_n) if mlfq_n > 0 else 0,
            'cpu_utilization': (sum(end - start for pid, start, end in sim_mlfq.gantt_chart) / sim_mlfq.current_time) * 100 if sim_mlfq.current_time > 0 else 0
        }
            
        visualizer.visualize_algorithm_complete(sim_mlfq.gantt_chart, sim_mlfq.completed_processes, "MLFQ")
        print("✓")
        
        # ========== Realtime Scheduling Algorithms ==========
        
        # 7. RM (Rate Monotonic)
        print("[7/8] RM (Realtime)...", end=" ")
        rt_processes_rm = copy.deepcopy(master_process_list_realtime)
        sim_rm = SimulatorRM(rt_processes_rm)
        sim_rm.run()
            
        if sim_rm.completed_processes:
            rm_n = len(sim_rm.completed_processes)
            realtime_results['RM'] = {
                'deadline_misses': sim_rm.deadline_misses,
                'avg_turnaround': (sum(p.turnaround_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
                'avg_waiting': (sum(p.wait_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
                'cpu_utilization': (sum(end - start for pid, start, end in sim_rm.gantt_chart) / sim_rm.current_time) * 100 if sim_rm.current_time > 0 else 0
            }
                
            visualizer.visualize_algorithm_complete(sim_rm.gantt_chart, sim_rm.completed_processes, "Rate Monotonic")
        print("✓")
        
        # 8. EDF (Earliest Deadline First)
        print("[8/8] EDF (Realtime)...", end=" ")
        rt_processes_edf = copy.deepcopy(master_process_list_realtime)
        sim_edf = SimulatorEDF(rt_processes_edf)
        sim_edf.run()
            
        if sim_edf.completed_processes:
            edf_n = len(sim_edf.completed_processes)
            realtime_results['EDF'] = {
                'deadline_misses': sim_edf.deadline_misses,
                'avg_turnaround': (sum(p.turnaround_time for p in sim_edf.completed_processes) / edf_n) if edf_n > 0 else 0,
                'avg_waiting': (sum(p.wait_time for p in sim_edf.completed_processes) / edf_n) if edf_n > 0 else 0,
                'cpu_utilization': (sum(end - start for pid, start, end in sim_edf.gantt_chart) / sim_edf.current_time) * 100 if sim_edf.current_time > 0 else 0
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

# (if __name__ == "__main__": 는 수정 없음)

if __name__ == "__main__":
    run_simulations_with_visualization()
