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
import statistics  # 통계 계산을 위해 추가


def run_single_simulation(master_process_list_normal, master_process_list_realtime):
    """
    단일 시뮬레이션 실행 및 결과 반환 (반복 실행용)
    """
    comparison_results = {}
    realtime_results = {}
    
    # 1. FCFS
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_fcfs = SimulatorFCFS(non_rt_processes)
    sim_fcfs.run()
    fcfs_n = len(sim_fcfs.completed_processes)
    comparison_results['FCFS'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_fcfs.completed_processes) / fcfs_n) if fcfs_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_fcfs.completed_processes) / fcfs_n) if fcfs_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_fcfs.gantt_chart) / sim_fcfs.current_time) * 100 if sim_fcfs.current_time > 0 else 0,
        'context_switches': sim_fcfs.context_switches
    }
    
    # 2. RR (Q=4)
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_rr = SimulatorRR(non_rt_processes, time_quantum=4)
    sim_rr.run()
    rr_n = len(sim_rr.completed_processes)
    comparison_results['RR(Q=4)'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_rr.completed_processes) / rr_n) if rr_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_rr.completed_processes) / rr_n) if rr_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_rr.gantt_chart) / sim_rr.current_time) * 100 if sim_rr.current_time > 0 else 0,
        'context_switches': sim_rr.context_switches
    }
    
    # 3. SJF (SRTF)
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_sjf = SimulatorSJF(non_rt_processes)
    sim_sjf.run()
    sjf_n = len(sim_sjf.completed_processes)
    comparison_results['SJF'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_sjf.completed_processes) / sjf_n) if sjf_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_sjf.completed_processes) / sjf_n) if sjf_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_sjf.gantt_chart) / sim_sjf.current_time) * 100 if sim_sjf.current_time > 0 else 0,
        'context_switches': sim_sjf.context_switches
    }
    
    # 4. Static Priority
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_prio = SimulatorPriorityStatic(non_rt_processes)
    sim_prio.run()
    prio_n = len(sim_prio.completed_processes)
    comparison_results['Priority(Static)'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_prio.completed_processes) / prio_n) if prio_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_prio.completed_processes) / prio_n) if prio_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_prio.gantt_chart) / sim_prio.current_time) * 100 if sim_prio.current_time > 0 else 0,
        'context_switches': sim_prio.context_switches
    }
    
    # 5. Dynamic Priority (Aging)
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_prio_dyn = SimulatorPriorityDynamic(non_rt_processes, aging_factor=10)
    sim_prio_dyn.run()
    prio_dyn_n = len(sim_prio_dyn.completed_processes)
    comparison_results['Priority(Aging)'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_prio_dyn.completed_processes) / prio_dyn_n) if prio_dyn_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_prio_dyn.completed_processes) / prio_dyn_n) if prio_dyn_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_prio_dyn.gantt_chart) / sim_prio_dyn.current_time) * 100 if sim_prio_dyn.current_time > 0 else 0,
        'context_switches': sim_prio_dyn.context_switches
    }
    
    # 6. MLFQ
    non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
    sim_mlfq = SimulatorMLFQ(non_rt_processes)
    sim_mlfq.run()
    mlfq_n = len(sim_mlfq.completed_processes)
    comparison_results['MLFQ'] = {
        'avg_turnaround': (sum(p.turnaround_time for p in sim_mlfq.completed_processes) / mlfq_n) if mlfq_n > 0 else 0,
        'avg_waiting': (sum(p.wait_time for p in sim_mlfq.completed_processes) / mlfq_n) if mlfq_n > 0 else 0,
        'cpu_utilization': (sum(end - start for pid, start, end in sim_mlfq.gantt_chart) / sim_mlfq.current_time) * 100 if sim_mlfq.current_time > 0 else 0,
        'context_switches': sim_mlfq.context_switches
    }
    
    # 7. RM (Rate Monotonic)
    if master_process_list_realtime:
        rt_processes_rm = copy.deepcopy(master_process_list_realtime)
        sim_rm = SimulatorRM(rt_processes_rm)
        sim_rm.run()
        if sim_rm.completed_processes:
            rm_n = len(sim_rm.completed_processes)
            realtime_results['RM'] = {
                'deadline_misses': sim_rm.deadline_misses,
                'avg_turnaround': (sum(p.turnaround_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
                'avg_waiting': (sum(p.wait_time for p in sim_rm.completed_processes) / rm_n) if rm_n > 0 else 0,
                'cpu_utilization': (sum(end - start for pid, start, end in sim_rm.gantt_chart) / sim_rm.current_time) * 100 if sim_rm.current_time > 0 else 0,
                'context_switches': sim_rm.context_switches
            }
    
    # 8. EDF (Earliest Deadline First)
    if master_process_list_realtime:
        rt_processes_edf = copy.deepcopy(master_process_list_realtime)
        sim_edf = SimulatorEDF(rt_processes_edf)
        sim_edf.run()
        if sim_edf.completed_processes:
            edf_n = len(sim_edf.completed_processes)
            realtime_results['EDF'] = {
                'deadline_misses': sim_edf.deadline_misses,
                'avg_turnaround': (sum(p.turnaround_time for p in sim_edf.completed_processes) / edf_n) if edf_n > 0 else 0,
                'avg_waiting': (sum(p.wait_time for p in sim_edf.completed_processes) / edf_n) if edf_n > 0 else 0,
                'cpu_utilization': (sum(end - start for pid, start, end in sim_edf.gantt_chart) / sim_edf.current_time) * 100 if sim_edf.current_time > 0 else 0,
                'context_switches': sim_edf.context_switches
            }
    
    return comparison_results, realtime_results


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
    num_iterations = 1  # 기본값: 1회 실행
    
    # --- 2. 모드에 따른 프로세스 데이터 로드 ---
    if SIMULATION_MODE == 'PERFORMANCE':
        print("--- 🚀 모드: 알고리즘 성능 비교 (랜덤 생성) ---")
        
        # 반복 실행 옵션
        repeat_choice = ''
        while repeat_choice not in ['1', '2']:
            print("\n실행 모드를 선택하세요:")
            print("  [1] 단일 실행 (1회)")
            print("  [2] 반복 실행 (여러 워크로드로 평균 통계)")
            repeat_choice = input("선택 (1 또는 2): ").strip()
        
        if repeat_choice == '2':
            while True:
                try:
                    num_iterations = int(input("반복 횟수를 입력하세요 (2-100): ").strip())
                    if 2 <= num_iterations <= 100:
                        break
                    else:
                        print("2에서 100 사이의 값을 입력하세요.")
                except ValueError:
                    print("올바른 숫자를 입력하세요.")
        
        print(f"\n워크로드 생성 중... (반복: {num_iterations}회)")
        master_process_list_normal = generate_random_processes(
            num_processes=8,
            arrival_lambda=3.0,  # 평균 3ms 간격으로 도착
            max_cpu_burst=20,
            max_io_burst=30,
            workload_distribution={'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
        )
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
        
        print("=" * 70)
        print("CPU Scheduling Simulation & Visualization (Performance Mode)")
        print("=" * 70)
        print(f"\n반복 시뮬레이션 실행 중... (총 {num_iterations}회)\n")
        
        import warnings
        warnings.filterwarnings('ignore')
        
        # 반복 실행을 위한 통계 수집 변수
        all_comparison_results = []
        all_realtime_results = []
        
        # 마지막 실행의 시뮬레이터 객체들 (시각화용)
        last_sim_fcfs = None
        last_sim_rr = None
        last_sim_sjf = None
        last_sim_prio = None
        last_sim_prio_dyn = None
        last_sim_mlfq = None
        last_sim_rm = None
        last_sim_edf = None
        
        # 반복 실행
        for iteration in range(num_iterations):
            if num_iterations > 1:
                print(f"[반복 {iteration + 1}/{num_iterations}] ", end="")
                # 매 반복마다 새로운 워크로드 생성
                master_process_list_normal = generate_random_processes(
                    num_processes=8,
                    arrival_lambda=3.0,
                    max_cpu_burst=20,
                    max_io_burst=30,
                    workload_distribution={'cpu_bound': 0.3, 'io_bound': 0.4, 'mixed': 0.3}
                )
                master_process_list_realtime = generate_random_realtime_processes(num_processes=4, max_period=50)
            
            # 단일 시뮬레이션 실행
            comparison_results, realtime_results = run_single_simulation(
                master_process_list_normal, 
                master_process_list_realtime
            )
            
            all_comparison_results.append(comparison_results)
            all_realtime_results.append(realtime_results)
            
            if num_iterations > 1:
                print("✓")
        
        # 평균 통계 계산
        print("\n통계 계산 중...", end=" ")
        averaged_comparison = {}
        averaged_realtime = {}
        
        # Non-realtime 알고리즘 평균
        for alg in all_comparison_results[0].keys():
            averaged_comparison[alg] = {
                'avg_turnaround': statistics.mean([r[alg]['avg_turnaround'] for r in all_comparison_results]),
                'avg_waiting': statistics.mean([r[alg]['avg_waiting'] for r in all_comparison_results]),
                'cpu_utilization': statistics.mean([r[alg]['cpu_utilization'] for r in all_comparison_results]),
                'context_switches': statistics.mean([r[alg]['context_switches'] for r in all_comparison_results]),
                'std_turnaround': statistics.stdev([r[alg]['avg_turnaround'] for r in all_comparison_results]) if num_iterations > 1 else 0,
                'std_waiting': statistics.stdev([r[alg]['avg_waiting'] for r in all_comparison_results]) if num_iterations > 1 else 0,
            }
        
        # Realtime 알고리즘 평균
        if all_realtime_results and all_realtime_results[0]:
            for alg in all_realtime_results[0].keys():
                averaged_realtime[alg] = {
                    'deadline_misses': statistics.mean([r[alg]['deadline_misses'] for r in all_realtime_results if alg in r]),
                    'avg_turnaround': statistics.mean([r[alg]['avg_turnaround'] for r in all_realtime_results if alg in r]),
                    'avg_waiting': statistics.mean([r[alg]['avg_waiting'] for r in all_realtime_results if alg in r]),
                    'cpu_utilization': statistics.mean([r[alg]['cpu_utilization'] for r in all_realtime_results if alg in r]),
                    'context_switches': statistics.mean([r[alg]['context_switches'] for r in all_realtime_results if alg in r]),
                }
        print("✓")
        
        # 시각화를 위해 마지막 워크로드로 한 번 더 실행 (간트 차트용)
        print("\n시각화를 위한 최종 실행...")
        
        # 간트 차트 시각화용 시뮬레이션 (출력 억제)
        print("[1/8] FCFS...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_fcfs = SimulatorFCFS(non_rt_processes)
        sim_fcfs.run()
        visualizer.visualize_algorithm_complete(sim_fcfs.gantt_chart, sim_fcfs.completed_processes, "FCFS")
        print("✓")
        
        print("[2/8] RR (Q=4)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_rr = SimulatorRR(non_rt_processes, time_quantum=4)
        sim_rr.run()
        visualizer.visualize_algorithm_complete(sim_rr.gantt_chart, sim_rr.completed_processes, "RR (Q=4)")
        print("✓")
        
        print("[3/8] SJF (SRTF)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_sjf = SimulatorSJF(non_rt_processes)
        sim_sjf.run()
        visualizer.visualize_algorithm_complete(sim_sjf.gantt_chart, sim_sjf.completed_processes, "SJF (Preemptive)")
        print("✓")
        
        print("[4/8] Priority (Static)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_prio = SimulatorPriorityStatic(non_rt_processes)
        sim_prio.run()
        visualizer.visualize_algorithm_complete(sim_prio.gantt_chart, sim_prio.completed_processes, "Priority (Static)")
        print("✓")
        
        print("[5/8] Priority (Aging)...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_prio_dyn = SimulatorPriorityDynamic(non_rt_processes, aging_factor=10)
        sim_prio_dyn.run()
        visualizer.visualize_algorithm_complete(sim_prio_dyn.gantt_chart, sim_prio_dyn.completed_processes, "Priority (Aging)")
        print("✓")
        
        print("[6/8] MLFQ...", end=" ")
        non_rt_processes = [p for p in copy.deepcopy(master_process_list_normal) if p.period == 0]
        sim_mlfq = SimulatorMLFQ(non_rt_processes)
        sim_mlfq.run()
        visualizer.visualize_algorithm_complete(sim_mlfq.gantt_chart, sim_mlfq.completed_processes, "MLFQ")
        print("✓")
        
        # ========== Realtime Scheduling Algorithms ==========
        
        print("[7/8] RM (Realtime)...", end=" ")
        rt_processes_rm = copy.deepcopy(master_process_list_realtime)
        sim_rm = SimulatorRM(rt_processes_rm)
        sim_rm.run()
        if sim_rm.completed_processes:
            visualizer.visualize_algorithm_complete(sim_rm.gantt_chart, sim_rm.completed_processes, "Rate Monotonic")
        print("✓")
        
        print("[8/8] EDF (Realtime)...", end=" ")
        rt_processes_edf = copy.deepcopy(master_process_list_realtime)
        sim_edf = SimulatorEDF(rt_processes_edf)
        sim_edf.run()
        if sim_edf.completed_processes:
            visualizer.visualize_algorithm_complete(sim_edf.gantt_chart, sim_edf.completed_processes, "EDF")
        print("✓")
        
        # ========== Generate Comparison Charts ==========
        
        print("\nGenerating comparison charts...", end=" ")
        
        # 평균 통계로 비교 차트 생성
        visualizer.compare_algorithms(averaged_comparison)
        
        if averaged_realtime:
            visualizer.create_realtime_analysis(averaged_realtime)
        
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
        print(f"✅ All simulations complete! ({num_iterations}회 반복 평균)")
        print("=" * 70)
        
        # Summary statistics (평균값 출력)
        print("\n📊 Algorithm Performance Summary (평균):")
        print("-" * 110)
        if num_iterations > 1:
            print(f"{'Algorithm':<20} {'Avg TT':>12} {'±Std':>10} {'Avg WT':>12} {'±Std':>10} {'CPU Util':>12} {'Context SW':>12}")
        else:
            print(f"{'Algorithm':<20} {'Avg Turnaround':>15} {'Avg Waiting':>15} {'CPU Util':>12} {'Context SW':>12}")
        print("-" * 110)
        for alg, stats in averaged_comparison.items():
            if num_iterations > 1:
                print(f"{alg:<20} {stats['avg_turnaround']:>11.2f}ms ±{stats['std_turnaround']:>8.2f} {stats['avg_waiting']:>11.2f}ms ±{stats['std_waiting']:>8.2f} {stats['cpu_utilization']:>11.2f}% {stats['context_switches']:>12.1f}")
            else:
                print(f"{alg:<20} {stats['avg_turnaround']:>14.2f}ms {stats['avg_waiting']:>14.2f}ms {stats['cpu_utilization']:>11.2f}% {stats['context_switches']:>12.0f}")
        
        if averaged_realtime:
            print("\n📊 Realtime Scheduling Summary (평균):")
            print("-" * 90)
            print(f"{'Algorithm':<20} {'Deadline Misses':>18} {'Avg Turnaround':>15} {'Context SW':>12}")
            print("-" * 90)
            for alg, stats in averaged_realtime.items():
                print(f"{alg:<20} {stats['deadline_misses']:>18.1f} {stats['avg_turnaround']:>14.2f}ms {stats['context_switches']:>12.1f}")
        
        print("\n" + "=" * 70)

# (if __name__ == "__main__": 는 수정 없음)

if __name__ == "__main__":
    run_simulations_with_visualization()
