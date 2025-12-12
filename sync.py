# sync.py

import collections

RESOURCE_ID_COUNTER = 0
DEADLOCK_STRATEGY = 'prevention'  # 'prevention', 'avoidance', 'detection'

class Resource:
    """
    Mutex 역할을 하는 공유 자원 클래스입니다.
    """
    def __init__(self, name):
        global RESOURCE_ID_COUNTER # 
        self.name = name
        self.id = RESOURCE_ID_COUNTER # 
        RESOURCE_ID_COUNTER += 1      # 
        
        self.is_locked = False
        self.owner_pid = None
        
        # 이 자원을 기다리는 프로세스들의 대기 큐 (FIFO)
        # 가이드라인에 따라 Waiting 상태가 된 프로세스들이 여기로 옵니다.
        self.waiting_queue = collections.deque()
        print(f"[자원 생성] Mutex '{self.name}'이(가) 생성되었습니다.")

    def lock(self, process, current_time):
        """
        프로세스가 이 자원의 lock을 시도합니다.
        
        :param process: lock을 시도하는 Process 객체
        :return: True (성공) 또는 False (실패)
        """
        if not self.is_locked:
            # --- Lock 성공 ---
            self.is_locked = True
            self.owner_pid = process.pid
            print(f"[Time ???] 프로세스 {process.pid}이(가) '{self.name}' Lock 획득")
            return True
        else:
            # --- Lock 실패 ---
            # 프로세스를 이 자원의 대기 큐에 추가합니다.
            self.waiting_queue.append(process)
            print(f"[Time ???] 프로세스 {process.pid}이(가) '{self.name}' Lock 실패. (대기 큐 진입)")
            return False

    def unlock(self, process, current_time):
        """
        프로세스가 이 자원의 unlock을 시도합니다.
        
        :param process: unlock을 시도하는 Process 객체
        :return: (상태가 변경되어 Ready 큐로 가야 할 프로세스) 또는 None
        """
        if self.is_locked and self.owner_pid == process.pid:
            self.is_locked = False
            self.owner_pid = None
            print(f"[Time ???] 프로세스 {process.pid}이(가) '{self.name}' Unlock 반납")
            
            # --- 대기자 처리 ---
            # 이 자원을 기다리던 프로세스가 있다면,
            if self.waiting_queue:
                # 대기 큐의 맨 앞 프로세스를 꺼냅니다.
                woken_process = self.waiting_queue.popleft()
                
                # 자원의 Lock을 이 새 프로세스에게 즉시 넘겨줍니다.
                self.is_locked = True
                self.owner_pid = woken_process.pid
                
                print(f"[Time ???] '{self.name}' 자원을 P{woken_process.pid}에게 전달. (Ready 큐로 이동)")
                # 이 프로세스는 Waiting -> Ready 상태로 변경되어야 합니다.
                return woken_process 
                
            return None # 아무도 깨울 필요 없음
        
        else:
            # (자신이 소유하지 않은 lock을 해제하려는 비정상적 경우)
            print(f"경고: P{process.pid}이(가) 소유하지 않은 '{self.name}' Unlock 시도함.")
            return None

# --- 모든 시뮬레이션이 공유할 전역 자원 관리자 ---
# (간단하게 Dictionary로 구현)
# 예: "Printer", "File", "R1", "R2" ...
RESOURCE_REGISTRY = {}

def initialize_resources(resource_names):
    global RESOURCE_REGISTRY
    global RESOURCE_ID_COUNTER # 
    
    RESOURCE_REGISTRY.clear()
    RESOURCE_ID_COUNTER = 0      # 
    
    for name in resource_names:
        # (Resource가 생성될 때마다 self.id가 0, 1, 2...로 자동 할당됨)
        RESOURCE_REGISTRY[name] = Resource(name)

def get_resource(name):
    """
    이름으로 등록된 자원(Mutex)을 가져옵니다.
    """
    return RESOURCE_REGISTRY.get(name)

def set_deadlock_strategy(strategy):
    """
    교착상태 처리 전략을 설정합니다.
    :param strategy: 'prevention', 'avoidance', 'detection'
    """
    global DEADLOCK_STRATEGY
    DEADLOCK_STRATEGY = strategy
    print(f"[교착상태 전략] '{strategy}' 모드로 설정되었습니다.")

def get_deadlock_strategy():
    """
    현재 교착상태 처리 전략을 반환합니다.
    """
    return DEADLOCK_STRATEGY

def detect_deadlock(all_processes):
    """
    교착상태 탐지 알고리즘 (순환 대기 검사)
    :param all_processes: 모든 프로세스 리스트
    :return: 교착상태에 있는 프로세스 리스트
    """
    # 자원 할당 그래프 구축
    waiting_for = {}  # {pid: resource_name}
    holding = {}      # {pid: [resource_names]}
    
    for proc in all_processes:
        if hasattr(proc, 'held_resources'):
            holding[proc.pid] = [res.name for res in proc.held_resources]
    
    # 각 자원의 대기 큐 확인
    for res_name, resource in RESOURCE_REGISTRY.items():
        if resource.waiting_queue:
            for proc in resource.waiting_queue:
                waiting_for[proc.pid] = res_name
    
    # 순환 대기 검사
    deadlocked = []
    for pid, waiting_res in waiting_for.items():
        visited = set()
        current_pid = pid
        
        while current_pid not in visited:
            visited.add(current_pid)
            
            # 현재 프로세스가 기다리는 자원
            if current_pid not in waiting_for:
                break
            
            waiting_res = waiting_for[current_pid]
            resource = RESOURCE_REGISTRY.get(waiting_res)
            
            if not resource or not resource.is_locked:
                break
            
            # 그 자원을 소유한 프로세스
            owner_pid = resource.owner_pid
            
            if owner_pid == pid:
                # 순환 발견!
                deadlocked.extend(list(visited))
                break
            
            current_pid = owner_pid
    
    return list(set(deadlocked))  # 중복 제거

def check_safe_state(process, resource, all_processes):
    """
    Banker's Algorithm을 사용한 안전 상태 검사 (간단한 버전)
    :param process: 자원을 요청하는 프로세스
    :param resource: 요청하는 자원
    :param all_processes: 모든 프로세스 리스트
    :return: True (안전), False (불안전)
    """
    # 간단한 휴리스틱: 순환 대기 가능성 검사
    if not resource.is_locked:
        return True
    
    # 자원 소유자 확인
    owner_pid = resource.owner_pid
    
    # 요청 프로세스가 이미 자원을 보유하고 있는지 확인
    if hasattr(process, 'held_resources') and process.held_resources:
        # 소유자가 요청자의 자원을 기다리고 있는지 확인
        for held_res in process.held_resources:
            if held_res.waiting_queue:
                for waiting_proc in held_res.waiting_queue:
                    if waiting_proc.pid == owner_pid:
                        # 순환 대기 가능성 발견
                        return False
    
    return True