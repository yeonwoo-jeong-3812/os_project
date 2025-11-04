import collections
import re

# -------------------------------------------------------------------
# 1. 프로세스(PCB)를 정의하는 클래스
# -------------------------------------------------------------------
class Process:
    """
    Process Control Block (PCB) 역할을 하는 클래스입니다.
    (sync 기능 추가로 burst_pattern 처리 방식 변경됨)
    """
    # 프로세스 상태를 문자열 상수로 정의
    READY = 'Ready'
    RUNNING = 'Running'
    WAITING = 'Waiting'      # I/O 대기 + '자원(Mutex) 대기' 포함
    TERMINATED = 'Terminated'

    def __init__(self, pid, arrival_time, priority, burst_pattern_str, period=0, deadline=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.static_priority = priority
        self.dynamic_priority = priority

        # 실행 패턴: "CPU:5,IO:10,LOCK:R1" 문자열을
        # [ ('CPU', 5), ('IO', 10), ('LOCK', 'R1') ]
        # 형태의 '튜플 리스트'로 변환합니다.
        self.burst_pattern = []
        try:
            # 빈 문자열이 아닐 경우에만 파싱 시도
            if burst_pattern_str:
                bursts = burst_pattern_str.split(',')
                for burst in bursts:
                    parts = burst.split(':')
                    if len(parts) < 2:
                        print(f"경고: P{pid}의 버스트 형식이 잘못되었습니다: '{burst}'. 건너뜁니다.")
                        continue
                        
                    command = parts[0].upper().strip() # CPU, IO, LOCK, UNLOCK
                    value_str = parts[1].strip()
                    
                    if command in ('CPU', 'IO'):
                        value = int(value_str)
                        self.burst_pattern.append((command, value))
                    elif command in ('LOCK', 'UNLOCK'):
                        value = value_str # 자원 이름 (e.g., "Printer")
                        self.burst_pattern.append((command, value))
                    else:
                        print(f"경고: P{pid}의 알 수 없는 명령어: '{command}'. 건너뜁니다.")
        except Exception as e:
            print(f"오류: P{pid}의 실행 패턴 파싱 실패: '{burst_pattern_str}' ({e})")
            self.burst_pattern = [] # 오류 시 빈 패턴
        
        # 현재 실행해야 할 버스트의 인덱스
        self.current_burst_index = 0
        
        # 현재 CPU 버스트의 남은 시간 (SRTF, RR 등에서 사용)
        self.remaining_cpu_time = 0 
        # 첫 번째 버스트가 CPU이면, 그 시간으로 remaining_cpu_time을 초기화
        if self.burst_pattern and self.burst_pattern[0][0] == 'CPU':
            self.remaining_cpu_time = self.burst_pattern[0][1]

        self.state = Process.READY
        self.held_resources = []

        # 실시간 스케줄링용
        self.period = period
        self.deadline = deadline
        self.absolute_deadline = 0 # EDF, RM에서 사용 (시뮬레이터가 설정)

        # --- 통계용 변수 ---
        self.wait_time = 0
        self.turnaround_time = 0
        self.last_ready_time = arrival_time
        self.completion_time = 0

    def __repr__(self):
        """
        디버깅을 위해 print(process) 실행 시 출력될 형태를 정의합니다.
        """
        return f"Process(PID:{self.pid}, Arrival:{self.arrival_time}, Priority:{self.static_priority}, Bursts:{self.burst_pattern})"

    def get_current_burst(self):
        """
        [새 함수]
        현재 실행해야 할 버스트 튜플 (명령, 값)을 반환합니다.
        (e.g., ('CPU', 5) 또는 ('LOCK', 'Printer'))
        """
        if self.current_burst_index < len(self.burst_pattern):
            return self.burst_pattern[self.current_burst_index]
        return None # 모든 버스트 종료

    def advance_to_next_burst(self):
        """
        [새 함수]
        다음 버스트로 인덱스를 이동하고,
        새 버스트가 'CPU'이면 remaining_cpu_time을 세팅합니다.
        """
        self.current_burst_index += 1
        
        next_burst = self.get_current_burst()
        if next_burst and next_burst[0] == 'CPU':
            self.remaining_cpu_time = next_burst[1]
        else:
            self.remaining_cpu_time = 0 # CPU 버스트가 아님
            
    # (get_current_burst_type 함수는 이제 사용되지 않음)

# -------------------------------------------------------------------
# 2. 입력 파일을 읽어 Process 객체 리스트를 반환하는 함수
# -------------------------------------------------------------------

def parse_input_file(filename="sample_input.txt"):
    """
    (수정됨) 입력 파일을 읽어서 Process 객체 리스트를 생성합니다.
    "CPU:5,IO:10" 형태의 문자열을 그대로 Process 클래스에 전달합니다.
    """
    processes = []
    
    # 정규식 패턴은 기존과 동일 (따옴표 안의 문자열을 통째로 가져옴)
    pattern = re.compile(r'(\d+),(\d+),(\d+),"([^"]+)",(\d+),(\d+)')
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('#') or not line:
                    continue
                
                match = pattern.match(line)
                
                if not match:
                    print(f"경고: 라인 형식이 맞지 않습니다. 건너뜁니다: {line}")
                    continue
                    
                groups = match.groups()
                
                pid = int(groups[0])
                arrival = int(groups[1])
                priority = int(groups[2])
                bursts_str = groups[3]  # "CPU:5,IO:10,LOCK:R1" 문자열
                period = int(groups[4])
                deadline = int(groups[5])

                # __init__이 새로운 burst_str을 파싱하도록 변경됨
                proc = Process(pid, arrival, priority, bursts_str, period, deadline)
                processes.append(proc)

    except FileNotFoundError:
        print(f"오류: '{filename}' 파일을 찾을 수 없습니다!")
        return []
    except Exception as e:
        print(f"파일 파싱 중 예기치 않은 오류 발생: {e}")
        if 'line' in locals():
             print(f"문제가 발생한 라인: {line}")
        return []

    return processes

# -------------------------------------------------------------------
# 3. (1.5단계) 테스트 실행
# -------------------------------------------------------------------
if __name__ == "__main__":
    """
    이 스크립트를 직접 실행하면(python process.py) 
    파일 파싱이 잘 되었는지 테스트합니다.
    """
    print("--- 1단계: 입력 파일 파싱 테스트 (수정 버전) ---")
    
    try:
        process_list = parse_input_file("sample_input.txt")
        
        if not process_list:
            print("오류: sample_input.txt 파일을 찾을 수 없거나 내용이 비어있습니다.")
        else:
            print(f"총 {len(process_list)}개의 프로세스를 읽었습니다.")
            for proc in process_list:
                print(proc) # __repr__ 호출
                print(f"  -> 파싱된 버스트: {proc.burst_pattern}")
                
    except FileNotFoundError:
        print("오류: 'sample_input.txt' 파일을 찾을 수 없습니다!")