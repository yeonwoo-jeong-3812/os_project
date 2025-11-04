import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
from matplotlib import font_manager
import pandas as pd

class SchedulingVisualizer:
    """
    CPU 스케줄링 시뮬레이션 결과를 시각화하는 클래스
    """
    def __init__(self):
        # 한글 폰트 설정 (Windows 환경)
        import platform
        if platform.system() == 'Windows':
            plt.rcParams['font.family'] = 'Malgun Gothic'
        else:
            plt.rcParams['font.family'] = 'DejaVu Sans'
        
        plt.rcParams['axes.unicode_minus'] = False  # 마이너스 기호 깨짐 방지
        
        # 프로세스별 색상 정의
        self.colors = {
            1: '#FF6B6B',  # 빨강
            2: '#4ECDC4',  # 청록
            3: '#45B7D1',  # 파랑
            4: '#FFA07A',  # 연어색
            5: '#98D8C8',  # 민트
            6: '#F7DC6F',  # 노랑
        }
        
        # 화면 크기 자동 감지
        self.screen_width, self.screen_height = self._get_screen_size()
        
        # DPI 설정 (기본값)
        self.dpi = 100
        
        # 화면 크기에 따른 figure 크기 계산 (인치 단위)
        self.fig_width = (self.screen_width / self.dpi) * 0.95  # 화면 너비의 95%
        self.fig_height = (self.screen_height / self.dpi) * 0.85  # 화면 높이의 85%
    
    def _get_screen_size(self):
        """화면 크기를 자동으로 감지합니다"""
        try:
            import tkinter as tk
            root = tk.Tk()
            root.withdraw()  # 창 숨기기
            width = root.winfo_screenwidth()
            height = root.winfo_screenheight()
            root.destroy()
            return width, height
        except:
            # tkinter 실패 시 기본값 (Full HD)
            return 1920, 1080
    
    def visualize_gantt_chart(self, gantt_chart, algorithm_name, save_path=None):
        """
        Visualize Gantt chart
        
        Args:
            gantt_chart: [(pid, start, end), ...] format list
            algorithm_name: Algorithm name (e.g. "FCFS", "RR(Q=4)")
            save_path: Save path (show on screen if None)
        """
        # Auto-adjust figure size based on screen
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.95, self.fig_height * 0.6))
        
        # Show execution segments per process
        y_pos = 0
        for pid, start, end in gantt_chart:
            color = self.colors.get(pid, '#CCCCCC')
            ax.barh(y_pos, end - start, left=start, height=0.6, 
                   color=color, edgecolor='black', linewidth=0.5)
            
            # Show process ID
            duration = end - start
            if duration > 2:  # Show inside if wide enough
                ax.text(start + duration/2, y_pos, f'P{pid}', 
                       ha='center', va='center', fontsize=9, fontweight='bold')
        
        # Set axes with larger fonts
        ax.set_xlabel('시간 (ms)', fontsize=13)
        ax.set_ylabel('CPU', fontsize=13)
        ax.set_title(f'{algorithm_name} 간트 차트', fontsize=15, fontweight='bold', pad=15)
        ax.set_yticks([y_pos])
        ax.set_yticklabels(['CPU'], fontsize=12)
        ax.tick_params(axis='x', labelsize=11)
        
        # Add grid
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # Add legend
        legend_elements = [mpatches.Patch(facecolor=self.colors.get(i, '#CCCCCC'), 
                                         edgecolor='black', label=f'P{i}') 
                          for i in sorted(set(pid for pid, _, _ in gantt_chart))]
        ax.legend(handles=legend_elements, loc='upper right', ncol=6, fontsize=10)
        
        # Better layout spacing
        plt.subplots_adjust(left=0.05, right=0.98, top=0.93, bottom=0.08)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()

    def create_process_timeline(self, completed_processes, gantt_chart, algorithm_name, save_path=None):
        """
        Process timeline (arrival, waiting, execution, completion)
        
        Args:
            completed_processes: List of Process objects
            gantt_chart: [(pid, start, end), ...] format list
            algorithm_name: Algorithm name
            save_path: Save path
        """
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.95, self.fig_height * 0.75))
        
        # Sort by process
        processes = sorted(completed_processes, key=lambda p: p.pid)
        
        for i, proc in enumerate(processes):
            y_pos = i
            
            # Show arrival time (dot)
            ax.plot(proc.arrival_time, y_pos, 'go', markersize=8, label='도착' if i == 0 else '')
            
            # Show execution segments
            proc_executions = [(start, end) for pid, start, end in gantt_chart if pid == proc.pid]
            for start, end in proc_executions:
                ax.barh(y_pos, end - start, left=start, height=0.3, 
                       color=self.colors.get(proc.pid, '#CCCCCC'), 
                       edgecolor='black', linewidth=0.5)
            
            # Show completion time (dot)
            ax.plot(proc.completion_time, y_pos, 'ro', markersize=8, label='종료' if i == 0 else '')
            
            # Total segment (arrival ~ completion)
            ax.barh(y_pos, proc.turnaround_time, left=proc.arrival_time, height=0.6, 
                   color='lightgray', alpha=0.3, edgecolor='gray', linestyle='--', linewidth=1)
        
        # Set axes
        ax.set_xlabel('시간 (ms)', fontsize=13)
        ax.set_ylabel('프로세스', fontsize=13)
        ax.set_title(f'{algorithm_name} 프로세스 타임라인', fontsize=15, fontweight='bold', pad=15)
        ax.set_yticks(range(len(processes)))
        ax.set_yticklabels([f'P{p.pid}' for p in processes], fontsize=11)
        ax.tick_params(axis='x', labelsize=11)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', fontsize=11)
        
        # Better layout spacing
        plt.subplots_adjust(left=0.08, right=0.96, top=0.93, bottom=0.08)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()
    
    def create_statistics_table(self, completed_processes, algorithm_name, save_path=None):
        """
        Create statistics table per process
        
        Args:
            completed_processes: List of Process objects
            algorithm_name: Algorithm name
            save_path: Save path
        """
        # Create dataframe
        data = []
        for proc in sorted(completed_processes, key=lambda p: p.pid):
            data.append({
                'PID': f'P{proc.pid}',
                '도착시간': proc.arrival_time,
                '종료시간': proc.completion_time,
                '반환시간': proc.turnaround_time,
                '대기시간': proc.wait_time,
                '우선순위': proc.static_priority
            })
        
        df = pd.DataFrame(data)
        
        # Add average row
        avg_row = {
            'PID': '평균',
            '도착시간': '-',
            '종료시간': '-',
            '반환시간': df['반환시간'].mean(),
            '대기시간': df['대기시간'].mean(),
            '우선순위': '-'
        }
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
        
        # Visualize table
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.7, len(data) * (self.fig_height * 0.06) + 2))
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=df.values, colLabels=df.columns,
                        cellLoc='center', loc='center',
                        colColours=['#E8E8E8'] * len(df.columns))
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Header style
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Average row style
        for i in range(len(df.columns)):
            table[(len(data) + 1, i)].set_facecolor('#FFE5B4')
            table[(len(data) + 1, i)].set_text_props(weight='bold')
        
        plt.title(f'{algorithm_name} - 프로세스 통계', fontsize=14, fontweight='bold', pad=20)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()
        
        return df
    
    def create_realtime_analysis(self, rt_results_dict, save_path=None):
        """
        Realtime scheduling analysis (RM vs EDF)
        
        Args:
            rt_results_dict: {
                'RM': {'deadline_misses': int, 'avg_turnaround': float, ...},
                'EDF': {'deadline_misses': int, 'avg_turnaround': float, ...}
            }
            save_path: Save path
        """
        algorithms = list(rt_results_dict.keys())
        deadline_misses = [rt_results_dict[alg]['deadline_misses'] for alg in algorithms]
        avg_tt = [rt_results_dict[alg]['avg_turnaround'] for alg in algorithms]
        
        # Auto-adjust figure size based on screen
        fig = plt.figure(figsize=(self.fig_width * 0.85, self.fig_height * 0.7))
        
        # Create subplots with more space
        ax1 = plt.subplot(1, 2, 1)
        ax2 = plt.subplot(1, 2, 2)
        
        # Deadline miss count
        colors_bar = ['#FF6B6B' if x > 0 else '#4ECDC4' for x in deadline_misses]
        ax1.bar(algorithms, deadline_misses, color=colors_bar, edgecolor='black', width=0.5)
        ax1.set_ylabel('횟수', fontsize=13)
        ax1.set_title('마감시한 초과 횟수', fontsize=14, fontweight='bold', pad=20)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim([0, max(deadline_misses) * 1.3 if max(deadline_misses) > 0 else 1])
        for i, v in enumerate(deadline_misses):
            ax1.text(i, v + (max(deadline_misses)*0.05 if max(deadline_misses) > 0 else 0.1), 
                    f'{v}', ha='center', fontsize=12, fontweight='bold')
        
        # Average turnaround time
        ax2.bar(algorithms, avg_tt, color='#45B7D1', edgecolor='black', width=0.5)
        ax2.set_ylabel('시간 (ms)', fontsize=13)
        ax2.set_title('평균 반환시간', fontsize=14, fontweight='bold', pad=20)
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim([0, max(avg_tt) * 1.2])
        for i, v in enumerate(avg_tt):
            ax2.text(i, v + max(avg_tt)*0.04, f'{v:.2f}', ha='center', fontsize=11)
        
        # Main title with more space
        fig.suptitle('실시간 스케줄링 비교 (RM vs EDF)', fontsize=16, fontweight='bold', y=0.96)
        
        # Better layout with more margins
        plt.subplots_adjust(left=0.08, right=0.95, top=0.88, bottom=0.1, wspace=0.25)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.5)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()

    
    
    def compare_algorithms(self, results_dict, save_path=None):
        """
        Compare performance of multiple algorithms with bar charts
        
        Args:
            results_dict: {
                'algorithm_name': {
                    'avg_turnaround': float,
                    'avg_waiting': float,
                    'cpu_utilization': float
                }
            }
            save_path: Save path
        """
        algorithms = list(results_dict.keys())
        avg_tt = [results_dict[alg]['avg_turnaround'] for alg in algorithms]
        avg_wt = [results_dict[alg]['avg_waiting'] for alg in algorithms]
        cpu_util = [results_dict[alg]['cpu_utilization'] for alg in algorithms]
        
        # Auto-adjust figure size based on screen
        fig, axes = plt.subplots(1, 3, figsize=(self.fig_width * 0.95, self.fig_height * 0.75))
        
        # Average turnaround time
        axes[0].bar(algorithms, avg_tt, color='#FF6B6B', edgecolor='black', width=0.6)
        axes[0].set_ylabel('시간 (ms)', fontsize=13)
        axes[0].set_title('평균 반환시간', fontsize=15, fontweight='bold', pad=20)
        axes[0].grid(axis='y', alpha=0.3)
        axes[0].set_ylim([0, max(avg_tt) * 1.15])
        for i, v in enumerate(avg_tt):
            axes[0].text(i, v + max(avg_tt)*0.02, f'{v:.2f}', ha='center', fontsize=10)
        
        # Average waiting time
        axes[1].bar(algorithms, avg_wt, color='#4ECDC4', edgecolor='black', width=0.6)
        axes[1].set_ylabel('시간 (ms)', fontsize=13)
        axes[1].set_title('평균 대기시간', fontsize=15, fontweight='bold', pad=20)
        axes[1].grid(axis='y', alpha=0.3)
        axes[1].set_ylim([0, max(avg_wt) * 1.15])
        for i, v in enumerate(avg_wt):
            axes[1].text(i, v + max(avg_wt)*0.02, f'{v:.2f}', ha='center', fontsize=10)
        
        # CPU utilization
        axes[2].bar(algorithms, cpu_util, color='#45B7D1', edgecolor='black', width=0.6)
        axes[2].set_ylabel('사용률 (%)', fontsize=13)
        axes[2].set_title('CPU 사용률', fontsize=15, fontweight='bold', pad=20)
        axes[2].set_ylim([0, 105])
        axes[2].grid(axis='y', alpha=0.3)
        for i, v in enumerate(cpu_util):
            axes[2].text(i, v + 2, f'{v:.2f}%', ha='center', fontsize=10)
        
        # Rotate x-axis labels for better visibility
        for ax in axes:
            ax.tick_params(axis='x', rotation=15, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
        
        # Perfect spacing to fit fullscreen without clipping
        plt.subplots_adjust(left=0.05, right=0.98, top=0.90, bottom=0.15, wspace=0.22)
        
        plt.tight_layout()
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()
    
    def create_process_timeline(self, completed_processes, gantt_chart, algorithm_name, save_path=None):
        """
        Process timeline (arrival, waiting, execution, completion)
        
        Args:
            completed_processes: List of Process objects
            gantt_chart: [(pid, start, end), ...] format list
            algorithm_name: Algorithm name
            save_path: Save path
        """
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.95, self.fig_height * 0.75))
        
        # Sort by process
        processes = sorted(completed_processes, key=lambda p: p.pid)
        
        for i, proc in enumerate(processes):
            y_pos = i
            
            # Show arrival time (dot)
            ax.plot(proc.arrival_time, y_pos, 'go', markersize=8, label='도착' if i == 0 else '')
            
            # Show execution segments
            proc_executions = [(start, end) for pid, start, end in gantt_chart if pid == proc.pid]
            for start, end in proc_executions:
                ax.barh(y_pos, end - start, left=start, height=0.3, 
                       color=self.colors.get(proc.pid, '#CCCCCC'), 
                       edgecolor='black', linewidth=0.5)
            
            # Show completion time (dot)
            ax.plot(proc.completion_time, y_pos, 'ro', markersize=8, label='종료' if i == 0 else '')
            
            # Total segment (arrival ~ completion)
            ax.barh(y_pos, proc.turnaround_time, left=proc.arrival_time, height=0.6, 
                   color='lightgray', alpha=0.3, edgecolor='gray', linestyle='--', linewidth=1)
        
        # Set axes
        ax.set_xlabel('시간 (ms)', fontsize=13)
        ax.set_ylabel('프로세스', fontsize=13)
        ax.set_title(f'{algorithm_name} 프로세스 타임라인', fontsize=15, fontweight='bold', pad=15)
        ax.set_yticks(range(len(processes)))
        ax.set_yticklabels([f'P{p.pid}' for p in processes], fontsize=11)
        ax.tick_params(axis='x', labelsize=11)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        ax.legend(loc='upper right', fontsize=11)
        
        # Better layout spacing
        plt.subplots_adjust(left=0.08, right=0.96, top=0.93, bottom=0.08)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()
    
    def create_statistics_table(self, completed_processes, algorithm_name, save_path=None):
        """
        Create statistics table per process
        
        Args:
            completed_processes: List of Process objects
            algorithm_name: Algorithm name
            save_path: Save path
        """
        # Create dataframe
        data = []
        for proc in sorted(completed_processes, key=lambda p: p.pid):
            data.append({
                'PID': f'P{proc.pid}',
                '도착시간': proc.arrival_time,
                '종료시간': proc.completion_time,
                '반환시간': proc.turnaround_time,
                '대기시간': proc.wait_time,
                '우선순위': proc.static_priority
            })
        
        df = pd.DataFrame(data)
        
        # Add average row
        avg_row = {
            'PID': '평균',
            '도착시간': '-',
            '종료시간': '-',
            '반환시간': df['반환시간'].mean(),
            '대기시간': df['대기시간'].mean(),
            '우선순위': '-'
        }
        df = pd.concat([df, pd.DataFrame([avg_row])], ignore_index=True)
        
        # Visualize table
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.7, len(data) * (self.fig_height * 0.06) + 2))
        ax.axis('tight')
        ax.axis('off')
        
        table = ax.table(cellText=df.values, colLabels=df.columns,
                        cellLoc='center', loc='center',
                        colColours=['#E8E8E8'] * len(df.columns))
        
        table.auto_set_font_size(False)
        table.set_fontsize(10)
        table.scale(1, 2)
        
        # Header style
        for i in range(len(df.columns)):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white')
        
        # Average row style
        for i in range(len(df.columns)):
            table[(len(data) + 1, i)].set_facecolor('#FFE5B4')
            table[(len(data) + 1, i)].set_text_props(weight='bold')
        
        plt.title(f'{algorithm_name} - 프로세스 통계', fontsize=14, fontweight='bold', pad=20)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()
        
        return df


# 사용 예제
    def visualize_all_gantt_charts(self, gantt_data_dict, save_path=None):
        """
        모든 알고리즘의 간트 차트를 한 화면에 표시
        
        Args:
            gantt_data_dict: {
                'algorithm_name': [(pid, start, end), ...],
                ...
            }
            save_path: Save path
        """
        algorithms = list(gantt_data_dict.keys())
        n_algorithms = len(algorithms)
        
        # Auto-adjust figure size based on number of algorithms
        fig, axes = plt.subplots(n_algorithms, 1, 
                                figsize=(self.fig_width * 0.95, min(self.fig_height * 0.12 * n_algorithms, self.fig_height * 0.9)))
        
        # If only one algorithm, make axes iterable
        if n_algorithms == 1:
            axes = [axes]
        
        for idx, (algo_name, gantt_chart) in enumerate(gantt_data_dict.items()):
            ax = axes[idx]
            
            # Show execution segments per process
            y_pos = 0
            for pid, start, end in gantt_chart:
                color = self.colors.get(pid, '#CCCCCC')
                ax.barh(y_pos, end - start, left=start, height=0.6, 
                       color=color, edgecolor='black', linewidth=0.5)
                
                # Show process ID
                duration = end - start
                if duration > 2:  # Show inside if wide enough
                    ax.text(start + duration/2, y_pos, f'P{pid}', 
                           ha='center', va='center', fontsize=8, fontweight='bold')
            
            # Set axes
            ax.set_ylabel(algo_name, fontsize=11, fontweight='bold', rotation=0, 
                         ha='right', va='center')
            ax.set_yticks([y_pos])
            ax.set_yticklabels([''])
            ax.grid(axis='x', alpha=0.3, linestyle='--')
            ax.tick_params(axis='x', labelsize=10)
            
            # Only show x-label on bottom chart
            if idx == n_algorithms - 1:
                ax.set_xlabel('시간 (ms)', fontsize=12, fontweight='bold')
            
            # Add legend only on first chart
            if idx == 0:
                all_pids = set()
                for algo_data in gantt_data_dict.values():
                    all_pids.update(pid for pid, _, _ in algo_data)
                
                legend_elements = [mpatches.Patch(facecolor=self.colors.get(i, '#CCCCCC'), 
                                                 edgecolor='black', label=f'P{i}') 
                                  for i in sorted(all_pids)]
                ax.legend(handles=legend_elements, loc='upper right', ncol=8, fontsize=9)
        
        # Main title
        fig.suptitle('전체 알고리즘 간트 차트 비교', fontsize=16, fontweight='bold')
        
        # Better layout spacing
        plt.subplots_adjust(left=0.12, right=0.96, top=0.94, bottom=0.06, hspace=0.4)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.5)
        else:
            # Display in fullscreen
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')  # Windows
            except:
                try:
                    mng.window.showMaximized()  # Qt backend
                except:
                    try:
                        mng.frame.Maximize(True)  # Tk backend
                    except:
                        pass
            plt.show()
        
        plt.close()

    def visualize_algorithm_complete(self, gantt_chart, completed_processes, algorithm_name, save_path=None):
        """
        한 알고리즘의 모든 시각화를 한 화면에 표시
        (간트 차트 + 타임라인 + 통계표)
        """
        # Create figure with 3 rows - optimized heights
        fig = plt.figure(figsize=(self.fig_width * 0.95, self.fig_height * 0.80))
        gs = fig.add_gridspec(3, 1, height_ratios=[0.5, 1, 1.1], hspace=0.35)
        
        # 1. Gantt Chart (top) - much smaller
        ax1 = fig.add_subplot(gs[0])
        y_pos = 0
        for pid, start, end in gantt_chart:
            color = self.colors.get(pid, '#CCCCCC')
            ax1.barh(y_pos, end - start, left=start, height=0.4, 
                   color=color, edgecolor='black', linewidth=0.5)
            duration = end - start
            if duration > 2:
                ax1.text(start + duration/2, y_pos, f'P{pid}', 
                       ha='center', va='center', fontsize=7, fontweight='bold')
        
        ax1.set_xlabel('시간 (ms)', fontsize=10)
        ax1.set_ylabel('CPU', fontsize=9)
        ax1.set_title(f'{algorithm_name} 간트 차트', fontsize=11, fontweight='bold', pad=6)
        ax1.set_yticks([y_pos])
        ax1.set_yticklabels(['CPU'], fontsize=8)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.grid(axis='x', alpha=0.3, linestyle='--')
        
        legend_elements = [mpatches.Patch(facecolor=self.colors.get(i, '#CCCCCC'), 
                                         edgecolor='black', label=f'P{i}') 
                          for i in sorted(set(pid for pid, _, _ in gantt_chart))]
        ax1.legend(handles=legend_elements, loc='upper right', ncol=8, fontsize=7)
        
        # 2. Process Timeline (middle)
        ax2 = fig.add_subplot(gs[1])
        processes = sorted(completed_processes, key=lambda p: p.pid)
        
        for i, proc in enumerate(processes):
            y_pos = i
            ax2.plot(proc.arrival_time, y_pos, 'go', markersize=5, label='도착' if i == 0 else '')
            
            proc_executions = [(start, end) for pid, start, end in gantt_chart if pid == proc.pid]
            for start, end in proc_executions:
                ax2.barh(y_pos, end - start, left=start, height=0.25, 
                       color=self.colors.get(proc.pid, '#CCCCCC'), 
                       edgecolor='black', linewidth=0.5)
            
            ax2.plot(proc.completion_time, y_pos, 'ro', markersize=5, label='종료' if i == 0 else '')
            ax2.barh(y_pos, proc.turnaround_time, left=proc.arrival_time, height=0.5, 
                   color='lightgray', alpha=0.25, edgecolor='gray', linestyle='--', linewidth=0.8)
        
        ax2.set_xlabel('시간 (ms)', fontsize=10)
        ax2.set_ylabel('프로세스', fontsize=10)
        ax2.set_title(f'{algorithm_name} 프로세스 타임라인', fontsize=11, fontweight='bold', pad=6)
        ax2.set_yticks(range(len(processes)))
        ax2.set_yticklabels([f'P{p.pid}' for p in processes], fontsize=8)
        ax2.tick_params(axis='x', labelsize=8)
        ax2.grid(axis='x', alpha=0.3, linestyle='--')
        ax2.legend(loc='upper right', fontsize=8)
        
        # 3. Statistics Table (bottom) - more square shape
        ax3 = fig.add_subplot(gs[2])
        ax3.axis('tight')
        ax3.axis('off')
        
        data = []
        for proc in sorted(completed_processes, key=lambda p: p.pid):
            data.append([
                f'P{proc.pid}',
                proc.arrival_time,
                proc.completion_time,
                proc.turnaround_time,
                proc.wait_time,
                proc.static_priority
            ])
        
        avg_tt = sum(p.turnaround_time for p in completed_processes) / len(completed_processes)
        avg_wt = sum(p.wait_time for p in completed_processes) / len(completed_processes)
        data.append(['평균', '-', '-', f'{avg_tt:.2f}', f'{avg_wt:.2f}', '-'])
        
        # Create table with better proportions
        table = ax3.table(cellText=data, 
                         colLabels=['PID', '도착시간', '종료시간', '반환시간', '대기시간', '우선순위'],
                         cellLoc='center', loc='center',
                         colColours=['#E8E8E8'] * 6,
                         bbox=[0.1, 0, 0.8, 1])  # [left, bottom, width, height] - narrower table
        
        table.auto_set_font_size(False)
        table.set_fontsize(9)
        table.scale(1, 2.2)  # Increased row height
        
        for i in range(6):
            table[(0, i)].set_facecolor('#4ECDC4')
            table[(0, i)].set_text_props(weight='bold', color='white', fontsize=9)
        
        for i in range(6):
            table[(len(data), i)].set_facecolor('#FFE5B4')
            table[(len(data), i)].set_text_props(weight='bold', fontsize=9)
        
        ax3.set_title(f'{algorithm_name} 프로세스 통계', fontsize=11, fontweight='bold', pad=8)
        
        # NO main title - removed!
        # Adjust layout with more bottom space
        plt.subplots_adjust(left=0.05, right=0.97, top=0.96, bottom=0.06)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.4)
        else:
            mng = plt.get_current_fig_manager()
            try:
                mng.window.state('zoomed')
            except:
                try:
                    mng.window.showMaximized()
                except:
                    try:
                        mng.frame.Maximize(True)
                    except:
                        pass
            plt.show()
        
        plt.close()


if __name__ == "__main__":
    pass
