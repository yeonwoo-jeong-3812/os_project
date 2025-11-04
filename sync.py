# sync.py

import collections

RESOURCE_ID_COUNTER = 0

class Resource:
    """
    Mutex 역할을 하는 공유 자원 클래스입니다.
    """
    def __init__(self, name):
        global RESOURCE_ID_COUNTER # 👈 [ 2. 이 줄을 추가합니다 ]
        
        self.name = name
        self.id = RESOURCE_ID_COUNTER # 👈 [ 3. 이 줄을 추가합니다 ]
        RESOURCE_ID_COUNTER += 1      # 👈 [ 4. 이 줄을 추가합니다 ]
        
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
    global RESOURCE_ID_COUNTER # 👈 [ 5. 이 줄을 추가합니다 ]
    
    RESOURCE_REGISTRY.clear()
    RESOURCE_ID_COUNTER = 0      # 👈 [ 6. 이 줄을 추가합니다 ]
    
    for name in resource_names:
        # (Resource가 생성될 때마다 self.id가 0, 1, 2...로 자동 할당됨)
        RESOURCE_REGISTRY[name] = Resource(name)

def get_resource(name):
    """
    이름으로 등록된 자원(Mutex)을 가져옵니다.
    """
    return RESOURCE_REGISTRY.get(name)