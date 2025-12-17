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
                'RM': {'deadline_misses': int, 'avg_turnaround': float, 'context_switches': int, ...},
                'EDF': {'deadline_misses': int, 'avg_turnaround': float, 'context_switches': int, ...}
            }
            save_path: Save path
        """
        algorithms = list(rt_results_dict.keys())
        deadline_misses = [rt_results_dict[alg]['deadline_misses'] for alg in algorithms]
        avg_tt = [rt_results_dict[alg]['avg_turnaround'] for alg in algorithms]
        ctx_sw = [rt_results_dict[alg]['context_switches'] for alg in algorithms]
        
        # Auto-adjust figure size based on screen
        fig = plt.figure(figsize=(self.fig_width * 0.95, self.fig_height * 0.7))
        
        # Create subplots with more space (1x3 layout)
        ax1 = plt.subplot(1, 3, 1)
        ax2 = plt.subplot(1, 3, 2)
        ax3 = plt.subplot(1, 3, 3)
        
        # Deadline miss count
        colors_bar = ['#FF6B6B' if x > 0 else '#4ECDC4' for x in deadline_misses]
        ax1.bar(algorithms, deadline_misses, color=colors_bar, edgecolor='black', width=0.5)
        ax1.set_ylabel('횟수', fontsize=13)
        ax1.set_title('마감시한 초과 횟수', fontsize=14, fontweight='bold', pad=20)
        ax1.grid(axis='y', alpha=0.3)
        ax1.set_ylim([0, max(deadline_misses) * 1.3 if max(deadline_misses) > 0 else 1])
        for i, v in enumerate(deadline_misses):
            ax1.text(i, v + (max(deadline_misses)*0.05 if max(deadline_misses) > 0 else 0.1), 
                    f'{int(v)}', ha='center', fontsize=12, fontweight='bold')
        
        # Average turnaround time
        ax2.bar(algorithms, avg_tt, color='#45B7D1', edgecolor='black', width=0.5)
        ax2.set_ylabel('시간 (ms)', fontsize=13)
        ax2.set_title('평균 반환시간', fontsize=14, fontweight='bold', pad=20)
        ax2.grid(axis='y', alpha=0.3)
        ax2.set_ylim([0, max(avg_tt) * 1.2])
        for i, v in enumerate(avg_tt):
            ax2.text(i, v + max(avg_tt)*0.04, f'{v:.2f}', ha='center', fontsize=11)
        
        # Context switches (NEW)
        ax3.bar(algorithms, ctx_sw, color='#FFA07A', edgecolor='black', width=0.5)
        ax3.set_ylabel('횟수', fontsize=13)
        ax3.set_title('총 문맥 전환 횟수', fontsize=14, fontweight='bold', pad=20)
        ax3.grid(axis='y', alpha=0.3)
        ax3.set_ylim([0, max(ctx_sw) * 1.2 if max(ctx_sw) > 0 else 10])
        for i, v in enumerate(ctx_sw):
            ax3.text(i, v + (max(ctx_sw)*0.04 if max(ctx_sw) > 0 else 0.5), f'{v}', ha='center', fontsize=11)
        
        # Main title with more space
        fig.suptitle('실시간 스케줄링 비교 (RM vs EDF)', fontsize=16, fontweight='bold', y=0.96)
        
        # Better layout with more margins
        plt.subplots_adjust(left=0.05, right=0.98, top=0.88, bottom=0.1, wspace=0.22)
        
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
                    'cpu_utilization': float,
                    'context_switches': int
                }
            }
            save_path: Save path
        """
        algorithms = list(results_dict.keys())
        avg_tt = [results_dict[alg]['avg_turnaround'] for alg in algorithms]
        avg_wt = [results_dict[alg]['avg_waiting'] for alg in algorithms]
        cpu_util = [results_dict[alg]['cpu_utilization'] for alg in algorithms]
        ctx_sw = [results_dict[alg]['context_switches'] for alg in algorithms]
        
        # Auto-adjust figure size based on screen (2x2 grid)
        fig, axes = plt.subplots(2, 2, figsize=(self.fig_width * 0.95, self.fig_height * 0.85))
        axes = axes.flatten()
        
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
        
        # Context switches (NEW)
        axes[3].bar(algorithms, ctx_sw, color='#FFA07A', edgecolor='black', width=0.6)
        axes[3].set_ylabel('횟수', fontsize=13)
        axes[3].set_title('총 문맥 전환 횟수', fontsize=15, fontweight='bold', pad=20)
        axes[3].grid(axis='y', alpha=0.3)
        axes[3].set_ylim([0, max(ctx_sw) * 1.15 if max(ctx_sw) > 0 else 10])
        for i, v in enumerate(ctx_sw):
            axes[3].text(i, v + max(ctx_sw)*0.02 if max(ctx_sw) > 0 else 0.5, f'{v}', ha='center', fontsize=10)
        
        # Rotate x-axis labels for better visibility
        for ax in axes:
            ax.tick_params(axis='x', rotation=15, labelsize=11)
            ax.tick_params(axis='y', labelsize=11)
        
        # Perfect spacing to fit fullscreen without clipping
        plt.subplots_adjust(left=0.05, right=0.98, top=0.93, bottom=0.10, wspace=0.20, hspace=0.30)
        
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
        # 실시간 스케줄링인 경우 간트 차트를 100ms로 제한
        is_realtime = algorithm_name in ['Rate Monotonic', 'EDF']
        if is_realtime:
            gantt_chart_display = [(pid, start, end) for pid, start, end in gantt_chart if start < 100]
            max_time = 100
        else:
            gantt_chart_display = gantt_chart
            max_time = max(end for _, _, end in gantt_chart) if gantt_chart else 0
        
        # Create figure with 3 rows - optimized heights
        fig = plt.figure(figsize=(self.fig_width * 0.95, self.fig_height * 0.80))
        gs = fig.add_gridspec(3, 1, height_ratios=[0.5, 1, 1.1], hspace=0.35)
        
        # 1. Gantt Chart (top) - much smaller
        ax1 = fig.add_subplot(gs[0])
        y_pos = 0
        for pid, start, end in gantt_chart_display:
            color = self.colors.get(pid, '#CCCCCC')
            ax1.barh(y_pos, end - start, left=start, height=0.4, 
                   color=color, edgecolor='black', linewidth=0.5)
            duration = end - start
            if duration > 2:
                ax1.text(start + duration/2, y_pos, f'P{pid}', 
                       ha='center', va='center', fontsize=7, fontweight='bold')
        
        ax1.set_xlabel('시간 (ms)', fontsize=10)
        ax1.set_ylabel('CPU', fontsize=9)
        title_suffix = ' (처음 100ms)' if is_realtime else ''
        ax1.set_title(f'{algorithm_name} 간트 차트{title_suffix}', fontsize=11, fontweight='bold', pad=6)
        ax1.set_yticks([y_pos])
        ax1.set_yticklabels(['CPU'], fontsize=8)
        ax1.tick_params(axis='x', labelsize=8)
        ax1.grid(axis='x', alpha=0.3, linestyle='--')
        if is_realtime:
            ax1.set_xlim(0, max_time)
        
        legend_elements = [mpatches.Patch(facecolor=self.colors.get(i, '#CCCCCC'), 
                                         edgecolor='black', label=f'P{i}') 
                          for i in sorted(set(pid for pid, _, _ in gantt_chart))]
        ax1.legend(handles=legend_elements, loc='upper right', ncol=8, fontsize=7)
        
        # 2. Process Timeline (middle)
        ax2 = fig.add_subplot(gs[1])
        
        # 실시간 스케줄링인 경우 고유 PID만 표시
        if is_realtime:
            unique_pids = sorted(set(p.pid for p in completed_processes))
            processes_display = [next(p for p in completed_processes if p.pid == pid) for pid in unique_pids]
        else:
            processes_display = sorted(completed_processes, key=lambda p: p.pid)
        
        for i, proc in enumerate(processes_display):
            y_pos = i
            
            # 실시간인 경우 100ms 이내만 표시
            if is_realtime:
                proc_executions = [(start, end) for pid, start, end in gantt_chart if pid == proc.pid and start < 100]
                
                # 실시간 프로세스: 각 주기의 도착점과 종료점 표시
                if proc.period > 0:
                    # completed_processes에서 해당 PID의 모든 주기 정보 가져오기
                    pid_instances = [p for p in completed_processes if p.pid == proc.pid and p.arrival_time < 100]
                    
                    for idx, instance in enumerate(pid_instances):
                        # 도착점 (초록색)
                        ax2.plot(instance.arrival_time, y_pos, 'go', markersize=6, 
                               label='도착' if i == 0 and idx == 0 else '')
                        
                        # 종료점 (빨간색) - 100ms 이내인 경우만
                        if instance.completion_time <= 100:
                            ax2.plot(instance.completion_time, y_pos, 'ro', markersize=6, 
                                   label='종료' if i == 0 and idx == 0 else '')
                else:
                    # 비실시간 프로세스
                    ax2.plot(proc.arrival_time, y_pos, 'go', markersize=6, label='도착' if i == 0 else '')
            else:
                proc_executions = [(start, end) for pid, start, end in gantt_chart if pid == proc.pid]
                ax2.plot(proc.arrival_time, y_pos, 'go', markersize=6, label='도착' if i == 0 else '')
            
            for start, end in proc_executions:
                ax2.barh(y_pos, end - start, left=start, height=0.25, 
                       color=self.colors.get(proc.pid, '#CCCCCC'), 
                       edgecolor='black', linewidth=0.5)
            
            if not is_realtime:
                ax2.plot(proc.completion_time, y_pos, 'ro', markersize=6, label='종료' if i == 0 else '')
                ax2.barh(y_pos, proc.turnaround_time, left=proc.arrival_time, height=0.5, 
                       color='lightgray', alpha=0.25, edgecolor='gray', linestyle='--', linewidth=0.8)
        
        ax2.set_xlabel('시간 (ms)', fontsize=10)
        ax2.set_ylabel('프로세스', fontsize=10)
        title_suffix = ' (처음 100ms)' if is_realtime else ''
        ax2.set_title(f'{algorithm_name} 프로세스 타임라인{title_suffix}', fontsize=11, fontweight='bold', pad=6)
        ax2.set_yticks(range(len(processes_display)))
        ax2.set_yticklabels([f'P{p.pid}' for p in processes_display], fontsize=8)
        ax2.tick_params(axis='x', labelsize=8)
        ax2.grid(axis='x', alpha=0.3, linestyle='--')
        ax2.legend(loc='upper right', fontsize=8)
        if is_realtime:
            ax2.set_xlim(0, max_time)
        
        # 3. Statistics Table (bottom) - more square shape
        ax3 = fig.add_subplot(gs[2])
        ax3.axis('tight')
        ax3.axis('off')
        
        data = []
        
        # 실시간 스케줄링인 경우 PID별로 집계
        if is_realtime:
            from collections import defaultdict
            pid_stats = defaultdict(lambda: {'count': 0, 'tt': 0, 'wt': 0, 'first_arrival': float('inf')})
            
            for proc in completed_processes:
                pid_stats[proc.pid]['count'] += 1
                pid_stats[proc.pid]['tt'] += proc.turnaround_time
                pid_stats[proc.pid]['wt'] += proc.wait_time
                pid_stats[proc.pid]['first_arrival'] = min(pid_stats[proc.pid]['first_arrival'], proc.arrival_time)
            
            for pid in sorted(pid_stats.keys()):
                stats = pid_stats[pid]
                avg_tt = stats['tt'] / stats['count']
                avg_wt = stats['wt'] / stats['count']
                data.append([
                    f'P{pid}',
                    stats['first_arrival'],
                    f"{stats['count']}회 실행",
                    f'{avg_tt:.2f}',
                    f'{avg_wt:.2f}',
                    '-'
                ])
        else:
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


    def visualize_context_switch_overhead(self, overhead_data, save_path=None):
        """
        [6단계] 문맥 교환 오버헤드 분석 그래프
        
        Args:
            overhead_data: {
                'algorithm_name': {
                    'context_switches': int,
                    'total_overhead': int (ms),
                    'total_time': int (ms)
                }
            }
            save_path: 저장 경로
        """
        if not overhead_data:
            return
        
        algorithms = list(overhead_data.keys())
        context_switches = [overhead_data[alg]['context_switches'] for alg in algorithms]
        total_overhead = [overhead_data[alg]['total_overhead'] for alg in algorithms]
        total_time = [overhead_data[alg]['total_time'] for alg in algorithms]
        overhead_ratio = [(overhead_data[alg]['total_overhead'] / overhead_data[alg]['total_time'] * 100) 
                         if overhead_data[alg]['total_time'] > 0 else 0 for alg in algorithms]
        
        fig = plt.figure(figsize=(self.fig_width * 0.95, self.fig_height * 0.7))
        
        # 3개 서브플롯
        ax1 = plt.subplot(1, 3, 1)
        ax2 = plt.subplot(1, 3, 2)
        ax3 = plt.subplot(1, 3, 3)
        
        # 1. 문맥 교환 횟수
        bars1 = ax1.bar(algorithms, context_switches, color='#4ECDC4', edgecolor='black', width=0.6)
        ax1.set_ylabel('횟수', fontsize=13)
        ax1.set_title('문맥 교환 횟수', fontsize=14, fontweight='bold', pad=15)
        ax1.grid(axis='y', alpha=0.3)
        ax1.tick_params(axis='x', rotation=15, labelsize=10)
        for i, v in enumerate(context_switches):
            ax1.text(i, v + max(context_switches)*0.02, f'{v}', ha='center', fontsize=10, fontweight='bold')
        
        # 2. 총 오버헤드 시간
        bars2 = ax2.bar(algorithms, total_overhead, color='#FFA07A', edgecolor='black', width=0.6)
        ax2.set_ylabel('시간 (ms)', fontsize=13)
        ax2.set_title('총 오버헤드 시간', fontsize=14, fontweight='bold', pad=15)
        ax2.grid(axis='y', alpha=0.3)
        ax2.tick_params(axis='x', rotation=15, labelsize=10)
        for i, v in enumerate(total_overhead):
            ax2.text(i, v + max(total_overhead)*0.02, f'{v}ms', ha='center', fontsize=10, fontweight='bold')
        
        # 3. 오버헤드 비율
        colors = ['#FF6B6B' if r > 5 else '#98D8C8' for r in overhead_ratio]
        bars3 = ax3.bar(algorithms, overhead_ratio, color=colors, edgecolor='black', width=0.6)
        ax3.set_ylabel('비율 (%)', fontsize=13)
        ax3.set_title('오버헤드 비율 (총 시간 대비)', fontsize=14, fontweight='bold', pad=15)
        ax3.grid(axis='y', alpha=0.3)
        ax3.tick_params(axis='x', rotation=15, labelsize=10)
        ax3.axhline(y=5, color='red', linestyle='--', linewidth=1, alpha=0.5, label='5% 기준선')
        for i, v in enumerate(overhead_ratio):
            ax3.text(i, v + max(overhead_ratio)*0.02, f'{v:.1f}%', ha='center', fontsize=10, fontweight='bold')
        ax3.legend(loc='upper right', fontsize=9)
        
        fig.suptitle('문맥 교환 오버헤드 분석', fontsize=16, fontweight='bold', y=0.96)
        plt.subplots_adjust(left=0.06, right=0.98, top=0.88, bottom=0.12, wspace=0.25)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.5)
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

    def visualize_process_state_timeline(self, completed_processes, algorithm_name, save_path=None):
        """
        [5단계] 프로세스별 상태 타임라인 시각화 (Running/Ready/Waiting 구분)
        
        Args:
            completed_processes: Process 객체 리스트 (timeline 속성 포함)
            algorithm_name: 알고리즘 이름
            save_path: 저장 경로
        """
        if not completed_processes:
            return
        
        # timeline이 없는 프로세스 필터링
        processes_with_timeline = [p for p in completed_processes if hasattr(p, 'timeline') and p.timeline]
        if not processes_with_timeline:
            return
        
        fig, ax = plt.subplots(figsize=(self.fig_width * 0.95, self.fig_height * 0.75))
        
        # 프로세스 정렬
        processes = sorted(processes_with_timeline, key=lambda p: p.pid)
        
        # 상태별 색상 정의
        state_colors = {
            'Ready': '#FFA07A',      # 연어색 (대기)
            'Running': '#4ECDC4',    # 청록색 (실행)
            'Waiting': '#F7DC6F'     # 노란색 (I/O 대기)
        }
        
        for i, proc in enumerate(processes):
            y_pos = i
            
            # 타임라인의 각 상태 구간을 그림
            for start_time, end_time, state in proc.timeline:
                if end_time is None:
                    continue  # 종료되지 않은 상태는 건너뜀
                
                duration = end_time - start_time
                color = state_colors.get(state, '#CCCCCC')
                
                ax.barh(y_pos, duration, left=start_time, height=0.6,
                       color=color, edgecolor='black', linewidth=0.5,
                       label=state if i == 0 and state not in [s for _, _, s in proc.timeline[:proc.timeline.index((start_time, end_time, state))]] else '')
            
            # 도착 시간 표시
            ax.plot(proc.arrival_time, y_pos, 'go', markersize=6, zorder=5)
            
            # 종료 시간 표시
            if hasattr(proc, 'completion_time'):
                ax.plot(proc.completion_time, y_pos, 'ro', markersize=6, zorder=5)
        
        # 축 설정
        ax.set_xlabel('시간 (ms)', fontsize=13)
        ax.set_ylabel('프로세스', fontsize=13)
        ax.set_title(f'{algorithm_name} - 프로세스 상태 타임라인 (Ready/Running/Waiting)', 
                    fontsize=15, fontweight='bold', pad=15)
        ax.set_yticks(range(len(processes)))
        ax.set_yticklabels([f'P{p.pid}' for p in processes], fontsize=11)
        ax.tick_params(axis='x', labelsize=11)
        ax.grid(axis='x', alpha=0.3, linestyle='--')
        
        # 범례 생성 (중복 제거)
        handles, labels = ax.get_legend_handles_labels()
        by_label = dict(zip(labels, handles))
        
        # 상태별 범례 추가
        legend_elements = [
            mpatches.Patch(facecolor=state_colors['Running'], edgecolor='black', label='Running (실행)'),
            mpatches.Patch(facecolor=state_colors['Ready'], edgecolor='black', label='Ready (대기)'),
            mpatches.Patch(facecolor=state_colors['Waiting'], edgecolor='black', label='Waiting (I/O)'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='g', markersize=6, label='도착'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='r', markersize=6, label='종료')
        ]
        ax.legend(handles=legend_elements, loc='upper right', ncol=5, fontsize=10)
        
        # 레이아웃 조정
        plt.subplots_adjust(left=0.08, right=0.96, top=0.93, bottom=0.08)
        
        if save_path:
            plt.savefig(save_path, dpi=300, bbox_inches='tight', pad_inches=0.3)
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
