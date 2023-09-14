import time
from typing import Dict

class MainLoopMeasurer:
    def __init__(self, is_proc: bool, *params: str) -> None:
        
        self._main_loop: Dict[str, float] = {}
        
        self.main_loop_time: Dict[str, float] = {}
        self.main_loop_share: Dict[str, float] = {}
        for p in params:
            self._main_loop[p] = 0
            self.main_loop_time[p] = 0
            self.main_loop_share[p] = 0
            
        self.as_proc_time = is_proc
        self.cycles = 0
        self.init_time = self._now()
       
    def start(self) -> None:
        self._start_time = self._now()
        self._prev_timer_value = self._start_time
        
    def end(self) -> None:
        self.cycles += 1

        duration = self._now() - self.init_time
        if duration <= 0:
            return
            
        for key in self.main_loop_time:
            self.main_loop_time[key] = self._main_loop[key] / self.cycles
            self.main_loop_share[key] = 100 * self._main_loop[key] / duration
        
    def add(self, param: str) -> None:
        now = self._now()
        self._main_loop[param] += now - self._prev_timer_value
        self._prev_timer_value = now
        
    def _now(self) -> float:
        return time.process_time() if self.as_proc_time else time.perf_counter()
    

class Performance:
    def __init__(self, *params: str) -> None:
        self.enabled = True
        
        self._proc = MainLoopMeasurer(True, *params)
        self._counter = MainLoopMeasurer(False, *params)
        
        self._cycles = 0
        
    def start(self) -> None:
        self._proc.start()
        self._counter.start()
        
    def end(self) -> None:
        self._proc.end()
        self._counter.end()

        self._cycles += 1
        
        if self.enabled and self._cycles % 50 is 0:

            numf = '{:.3f}'
            procf = '{:.1f}%'
            labellen = 25
            datalen = 8

            print(f' === {self._cycles} frames ==='.ljust(labellen),
                  'processor time'.ljust(2 * datalen + 1),
                  'total time'.ljust(2 * datalen + 1)
            )
            
            for key in self._proc.main_loop_time:
                print(key.ljust(labellen),
                    numf.format(self._proc.main_loop_time[key]).ljust(datalen),
                    procf.format(self._proc.main_loop_share[key]).ljust(datalen),
                    numf.format(self._counter.main_loop_time[key]).ljust(datalen),
                    procf.format(self._counter.main_loop_share[key]).ljust(datalen)
            )

            print('[TOTAL]'.ljust(labellen),
                  numf.format(self._sum(self._proc.main_loop_time)).ljust(datalen),
                  procf.format(self._sum(self._proc.main_loop_share)).ljust(datalen),
                  numf.format(self._sum(self._counter.main_loop_time)).ljust(datalen),
                  procf.format(self._sum(self._counter.main_loop_share)).ljust(datalen)
            )
            
            print('[PROC / DURATION]'.ljust(labellen + 2 * datalen + 2),
                  procf.format(100 * self._sum(self._proc.main_loop_time) / self._sum(self._counter.main_loop_time) ).ljust(datalen)
            )
    
    def add(self, param: str) -> None:
        self._proc.add(param)
        self._counter.add(param)

    def _sum(self, dict: Dict[str, float]) -> float:
        acc = 0
        for key, value in dict.items():
            acc += value
        return acc
