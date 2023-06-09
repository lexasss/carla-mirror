class SoftwareVersion(tuple[int, ...]):
    def __new__(cls, major: int, minor: int, patch: int) -> PygameVersion: ...
    def __repr__(self) -> str: ...
    def __str__(self) -> str: ...
    major: int
    minor: int
    patch: int

class PygameVersion(SoftwareVersion): ...
class SDLVersion(SoftwareVersion): ...

SDL: SDLVersion
ver: str
vernum: PygameVersion
rev: str
