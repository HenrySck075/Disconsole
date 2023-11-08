
class MissingSentinel:
    def __repr__(self):
        return "..."
    def __str__(self) -> str:
        return self.__repr__()
MISSING = MissingSentinel()
