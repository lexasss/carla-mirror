class Offset:
    def __init__(self, forward: float = 0, left: float = 0, up: float = 0) -> None:
        self.forward = forward
        self.left = left
        self.up = up
        
    def __eq__(self, __o: object) -> bool:
        if type(__o) is Offset:
            return self.forward == __o.forward and self.left == __o.left and self.up == __o.up
        return False
            
    def __ne__(self, __o: object) -> bool:
        if type(__o) is Offset:
            return not self.__eq__(__o)
        return False
    
    def __str__(self) -> str:
        return f'Offset: {self.forward}, {self.left}, {self.up}'