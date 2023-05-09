class NetCmd:
    hide_mirror = 'hide_mirror'
    show_mirror = 'show_mirror'

class MirrorStatus:
    def __init__(self) -> None:
        self.is_frozen = False
        
    def handle_net_request(self, req: str) -> None:
        if req == NetCmd.hide_mirror:
            self.is_frozen = True
        elif req == NetCmd.show_mirror:
            self.is_frozen = False
        else:
            print(f'MST: uknown network command {req}')