import collections
import re

# -------------------------------------------------------------------
# 1. 프로세스(PCB)를 정의하는 클래스
# -------------------------------------------------------------------
class Process:
    """
    Process Control Block (PCB) 역할을 하는 클래스입니다.
    프로세스 한 개의 모든 정보를 저장합니다.
    """
    # 프로세스 상태를 문자열 상수로 정의 (디버깅 시 편리)
    READY = 'Ready'
    RUNNING = 'Running'
    WAITING = 'Waiting'
    TERMINATED = 'Terminated'

    def __init__(self, pid, arrival_time, priority, burst_pattern_str, period=0, deadline=0):
        self.pid = pid
        self.arrival_time = arrival_time
        self.static_priority = priority
        self.dynamic_priority = priority  # Aging 기법을 위해 동적 우선순위 별도 관리

        # 실행 패턴: "3,10,4" 문자열을 [3, 10, 4] 정수 리스트로 변환
        self.burst_pattern = [int(x) for x in burst_pattern_str.split(',')]
        
        # 현재 실행해야 할 버스트의 인덱스 (e.g., 0 -> 3, 1 -> 10, 2 -> 4)
        self.current_burst_index = 0
        
        # 현재 CPU 버스트의 남은 시간 (SRTF, RR 등에서 사용)
        # burst_pattern[0] (첫 CPU 버스트 시간)으로 초기화
        self.remaining_cpu_time = self.burst_pattern[0]

        self.state = Process.READY  # 모든 프로세스는 도착 시 Ready 상태

        # 실시간 스케줄링용
        self.period = period
        self.deadline = deadline # 절대 마감 시간 (계산 필요)

        # --- 통계용 변수 ---
        self.wait_time = 0         # Ready 큐에서 대기한 총 시간
        self.turnaround_time = 0   # (종료 시간 - 도착 시간)
        self.last_ready_time = arrival_time # 대기 시간 계산을 위해 Ready 큐에 들어온 시점
        self.completion_time = 0   # 종료된 시간

    def __repr__(self):
        """
        디버깅을 위해 print(process) 실행 시 출력될 형태를 정의합니다.
        """
        return f"Process(PID:{self.pid}, Arrival:{self.arrival_time}, Priority:{self.static_priority}, Bursts:{self.burst_pattern})"

    def get_current_burst_type(self):
        """
        현재 버스트가 CPU인지 I/O인지 반환
        인덱스가 짝수 (0, 2, 4, ...)면 CPU, 홀수 (1, 3, 5, ...)면 I/O
        """
        if self.current_burst_index % 2 == 0:
            return 'CPU'
        else:
            return 'I/O'

# -------------------------------------------------------------------
# 2. 입력 파일을 읽어 Process 객체 리스트를 반환하는 함수
# -------------------------------------------------------------------

def parse_input_file(filename="sample_input.txt"):
    """
    교수님이 제공한 입력 파일을 읽어서 Process 객체 리스트를 생성합니다.
    (정규식을 사용하여 파싱 오류를 수정한 최종 버전)
    """
    processes = []
    
    # 정규식 패턴: (숫자),(숫자),(숫자)," (따옴표 안의 문자열) ",(숫자),(숫자)
    # 각 괄호()는 '그룹'이 됩니다.
    pattern = re.compile(r'(\d+),(\d+),(\d+),"([^"]+)",(\d+),(\d+)')
    
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                # 주석(#)이거나 빈 줄은 건너뛰기
                if line.startswith('#') or not line:
                    continue
                
                # 정규식과 매치(match)되는지 확인
                match = pattern.match(line)
                
                if not match:
                    # 정규식에 맞지 않는 라인은 경고 후 건너뜀
                    print(f"경고: 라인 형식이 맞지 않습니다. 건너뜁니다: {line}")
                    continue
                    
                # 매치된 그룹에서 데이터를 순서대로 추출
                # groups()는 ( '1', '0', '3', '15', '0', '0' ) 같은 튜플을 반환
                groups = match.groups()
                
                pid = int(groups[0])
                arrival = int(groups[1])
                priority = int(groups[2])
                bursts = groups[3]  # 따옴표 안의 문자열 (e.g., "3,10,4")
                period = int(groups[4])
                deadline = int(groups[5])

                # Process 객체 생성
                proc = Process(pid, arrival, priority, bursts, period, deadline)
                processes.append(proc)

    except FileNotFoundError:
        print(f"오류: '{filename}' 파일을 찾을 수 없습니다!")
        print("프로젝트 폴더에 'sample_input.txt' 파일을 생성하고 내용을 채워주세요.")
        return [] # 빈 리스트 반환
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
    print("--- 1단계: 입력 파일 파싱 테스트 ---")
    
    # 테스트를 위해 sample_input.txt 파일이 같은 폴더에 있어야 합니다.
    try:
        process_list = parse_input_file("sample_input.txt")
        
        if not process_list:
            print("오류: sample_input.txt 파일을 찾을 수 없거나 내용이 비어있습니다.")
            print("같은 폴더에 'sample_input.txt' 파일을 생성해주세요.")
        else:
            print(f"총 {len(process_list)}개의 프로세스를 읽었습니다.")
            for proc in process_list:
                print(proc)
                
    except FileNotFoundError:
        print("오류: 'sample_input.txt' 파일을 찾을 수 없습니다!")
        print("프로젝트 폴더에 'sample_input.txt' 파일을 생성하고 내용을 채워주세요.")