"""
GUI 기반 시뮬레이션 시나리오 선택기
tkinter를 사용하여 사용자가 시각적으로 시나리오를 선택할 수 있도록 함
"""

import tkinter as tk
from tkinter import ttk, messagebox, font
import sys


class SimulationSelector:
    """시뮬레이션 시나리오 선택 GUI"""
    
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("운영체제 스케줄링 시뮬레이터")
        self.root.geometry("800x700")
        self.root.resizable(False, False)
        
        # 색상 테마
        self.colors = {
            'bg': '#f5f7fa',
            'primary': '#4a90e2',
            'secondary': '#7b68ee',
            'success': '#50c878',
            'danger': '#e74c3c',
            'card_bg': '#ffffff',
            'text_dark': '#2c3e50',
            'text_light': '#7f8c8d',
            'border': '#e1e8ed'
        }
        
        self.root.configure(bg=self.colors['bg'])
        
        # 선택된 값들
        self.selected_mode = None
        self.selected_scenario = None
        self.num_iterations = 1
        self.result = None
        
        # 커스텀 스타일 설정
        self._setup_styles()
        self._create_widgets()
        self._center_window()
        
    def _setup_styles(self):
        """커스텀 스타일 설정"""
        style = ttk.Style()
        style.theme_use('clam')
        
        # 프레임 스타일
        style.configure('Card.TFrame', background=self.colors['card_bg'], relief='flat')
        
        # 라벨프레임 스타일
        style.configure('Card.TLabelframe', 
                       background=self.colors['card_bg'],
                       borderwidth=2,
                       relief='solid',
                       bordercolor=self.colors['border'])
        style.configure('Card.TLabelframe.Label',
                       background=self.colors['card_bg'],
                       foreground=self.colors['primary'],
                       font=('맑은 고딕', 11, 'bold'))
        
        # 라디오버튼 스타일
        style.configure('Mode.TRadiobutton',
                       background=self.colors['card_bg'],
                       foreground=self.colors['text_dark'],
                       font=('맑은 고딕', 10))
        style.map('Mode.TRadiobutton',
                 background=[('active', self.colors['card_bg'])],
                 foreground=[('active', self.colors['primary'])])
        
        # 버튼 스타일
        style.configure('Start.TButton',
                       background=self.colors['primary'],
                       foreground='white',
                       font=('맑은 고딕', 11, 'bold'),
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        style.map('Start.TButton',
                 background=[('active', '#3a7bc8')])
        
        style.configure('Exit.TButton',
                       background=self.colors['text_light'],
                       foreground='white',
                       font=('맑은 고딕', 11),
                       borderwidth=0,
                       focuscolor='none',
                       padding=(20, 10))
        style.map('Exit.TButton',
                 background=[('active', '#6b7c7d')])
    
    def _center_window(self):
        """창을 화면 중앙에 배치"""
        self.root.update_idletasks()
        width = self.root.winfo_width()
        height = self.root.winfo_height()
        x = (self.root.winfo_screenwidth() // 2) - (width // 2)
        y = (self.root.winfo_screenheight() // 2) - (height // 2)
        self.root.geometry(f'{width}x{height}+{x}+{y}')
        
    def _create_widgets(self):
        """GUI 위젯 생성"""
        # 메인 프레임
        main_frame = tk.Frame(self.root, bg=self.colors['bg'])
        main_frame.pack(fill=tk.BOTH, expand=True, padx=30, pady=30)
        
        # 헤더 영역
        header_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        header_frame.pack(fill=tk.X, pady=(0, 25))
        
        # 제목
        title_label = tk.Label(
            header_frame,
            text="🖥️ 운영체제 스케줄링 시뮬레이터",
            font=("맑은 고딕", 24, "bold"),
            bg=self.colors['bg'],
            fg=self.colors['text_dark']
        )
        title_label.pack()
        
        # 부제목
        subtitle_label = tk.Label(
            header_frame,
            text="시뮬레이션 모드를 선택하고 분석을 시작하세요",
            font=("맑은 고딕", 10),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        subtitle_label.pack(pady=(5, 0))
        
        # 모드 선택 섹션
        mode_frame = ttk.LabelFrame(main_frame, text="📋 시뮬레이션 모드 선택", 
                                   padding="20", style='Card.TLabelframe')
        mode_frame.pack(fill=tk.X, pady=(0, 20))
        
        self.mode_var = tk.StringVar(value="SCHEDULING")
        
        modes = [
            ("SCHEDULING", "📊 스케줄링 알고리즘 비교", 
             "FCFS, RR, SJF, Priority, MLFQ, RM, EDF 알고리즘 비교",
             "#4a90e2"),
            ("SYNC", "🔒 동기화 기능 테스트", 
             "우선순위 역전, 교착상태, 세마포어 테스트",
             "#7b68ee"),
            ("MEMORY", "💾 메모리 관리 시뮬레이션", 
             "페이징, 세그먼테이션, 페이지 교체 알고리즘",
             "#50c878")
        ]
        
        for i, (value, title, desc, color) in enumerate(modes):
            # 모드 카드 프레임
            card = tk.Frame(mode_frame, bg=self.colors['card_bg'], 
                          highlightbackground=self.colors['border'],
                          highlightthickness=1)
            card.pack(fill=tk.X, pady=8)
            
            rb = ttk.Radiobutton(
                card,
                text=f"{title}\n    {desc}",
                variable=self.mode_var,
                value=value,
                command=self._on_mode_change,
                style='Mode.TRadiobutton'
            )
            rb.pack(anchor=tk.W, padx=15, pady=12)
        
        # 시나리오 선택 섹션 (동기화 모드일 때만 표시)
        self.scenario_frame = ttk.LabelFrame(main_frame, text="🎯 동기화 시나리오 선택", 
                                            padding="20", style='Card.TLabelframe')
        self.scenario_frame.pack(fill=tk.X, pady=(0, 20))
        self.scenario_frame.pack_forget()  # 초기에는 숨김
        
        self.scenario_var = tk.StringVar(value="1")
        
        scenarios = [
            ("1", "🔄 고전적 동기화 문제 (우선순위 역전)"),
            ("2", "🚫 교착상태 예방 (Prevention - 자원 순서 할당)"),
            ("3", "🛡️ 교착상태 회피 (Avoidance - Banker's Algorithm)"),
            ("4", "🔁 세마포어 기반 생산자-소비자 문제")
        ]
        
        for i, (value, title) in enumerate(scenarios):
            rb = ttk.Radiobutton(
                self.scenario_frame,
                text=title,
                variable=self.scenario_var,
                value=value,
                style='Mode.TRadiobutton'
            )
            rb.pack(anchor=tk.W, padx=15, pady=8)
        
        # 반복 횟수 선택 (스케줄링 모드일 때만)
        self.iteration_frame = ttk.LabelFrame(main_frame, text="🔢 시뮬레이션 반복 횟수", 
                                             padding="20", style='Card.TLabelframe')
        self.iteration_frame.pack(fill=tk.X, pady=(0, 20))
        
        iter_inner_frame = tk.Frame(self.iteration_frame, bg=self.colors['card_bg'])
        iter_inner_frame.pack(fill=tk.X)
        
        tk.Label(
            iter_inner_frame,
            text="반복 횟수:",
            font=("맑은 고딕", 10, "bold"),
            bg=self.colors['card_bg'],
            fg=self.colors['text_dark']
        ).pack(side=tk.LEFT, padx=(0, 15))
        
        self.iteration_var = tk.IntVar(value=1)
        self.iteration_spinbox = ttk.Spinbox(
            iter_inner_frame,
            from_=1,
            to=20,
            textvariable=self.iteration_var,
            width=10,
            font=("맑은 고딕", 10)
        )
        self.iteration_spinbox.pack(side=tk.LEFT)
        
        tk.Label(
            iter_inner_frame,
            text="회  (1~20회, 여러 번 실행하여 평균 성능 측정)",
            font=("맑은 고딕", 9),
            bg=self.colors['card_bg'],
            fg=self.colors['text_light']
        ).pack(side=tk.LEFT, padx=(10, 0))
        
        # 버튼 프레임
        button_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        button_frame.pack(fill=tk.X, pady=(25, 0))
        
        # 버튼 컨테이너 (중앙 정렬)
        btn_container = tk.Frame(button_frame, bg=self.colors['bg'])
        btn_container.pack()
        
        start_btn = ttk.Button(
            btn_container,
            text="▶  시뮬레이션 시작",
            command=self._on_start,
            style='Start.TButton'
        )
        start_btn.pack(side=tk.LEFT, padx=8)
        
        exit_btn = ttk.Button(
            btn_container,
            text="✕  종료",
            command=self._on_exit,
            style='Exit.TButton'
        )
        exit_btn.pack(side=tk.LEFT, padx=8)
        
        # 정보 레이블
        info_frame = tk.Frame(main_frame, bg=self.colors['bg'])
        info_frame.pack(fill=tk.X, pady=(20, 0))
        
        info_label = tk.Label(
            info_frame,
            text="💡 시뮬레이션 모드를 선택하고 '시뮬레이션 시작'을 클릭하세요.",
            font=("맑은 고딕", 9),
            bg=self.colors['bg'],
            fg=self.colors['text_light']
        )
        info_label.pack()
        
    def _on_mode_change(self):
        """모드 변경 시 호출"""
        mode = self.mode_var.get()
        
        if mode == "SYNC":
            self.scenario_frame.pack(fill=tk.X, pady=(0, 20))
            self.iteration_frame.pack_forget()
        elif mode == "SCHEDULING":
            self.scenario_frame.pack_forget()
            self.iteration_frame.pack(fill=tk.X, pady=(0, 20))
        else:  # MEMORY
            self.scenario_frame.pack_forget()
            self.iteration_frame.pack_forget()
    
    def _on_start(self):
        """시작 버튼 클릭 시"""
        mode = self.mode_var.get()
        
        if mode == "SYNC":
            scenario = self.scenario_var.get()
            self.result = {
                'mode': mode,
                'scenario': scenario,
                'iterations': 1
            }
        elif mode == "SCHEDULING":
            iterations = self.iteration_var.get()
            if iterations < 1 or iterations > 20:
                messagebox.showerror("오류", "반복 횟수는 1~20 사이여야 합니다.")
                return
            self.result = {
                'mode': mode,
                'scenario': None,
                'iterations': iterations
            }
        else:  # MEMORY
            self.result = {
                'mode': mode,
                'scenario': None,
                'iterations': 1
            }
        
        self.root.quit()
        self.root.destroy()
    
    def _on_exit(self):
        """종료 버튼 클릭 시"""
        if messagebox.askokcancel("종료", "프로그램을 종료하시겠습니까?"):
            self.result = None
            self.root.quit()
            self.root.destroy()
    
    def show(self):
        """GUI 표시 및 결과 반환"""
        self.root.mainloop()
        return self.result


def get_user_selection():
    """
    GUI를 통해 사용자 선택을 받아 반환
    
    Returns:
        dict: {
            'mode': str,  # 'SCHEDULING', 'SYNC', 'MEMORY'
            'scenario': str or None,  # 동기화 시나리오 번호 (SYNC 모드일 때만)
            'iterations': int  # 반복 횟수
        }
        또는 None (사용자가 종료를 선택한 경우)
    """
    selector = SimulationSelector()
    return selector.show()


if __name__ == "__main__":
    # 테스트
    result = get_user_selection()
    if result:
        print(f"선택된 모드: {result['mode']}")
        print(f"시나리오: {result['scenario']}")
        print(f"반복 횟수: {result['iterations']}")
    else:
        print("사용자가 종료를 선택했습니다.")
