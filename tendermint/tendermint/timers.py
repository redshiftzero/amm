# Timeouts to prevent blocking forever
initTimeoutPropose = 6
initTimeoutPrevote = 6
initTimeoutPrecommit = 6
timeoutDelta = 1

# Timeouts increase with every new round r
def timeoutPropose(round: int) -> int:
    return initTimeoutPropose + round * timeoutDelta

def timeoutPrevote(round: int) -> int:
    return initTimeoutPrevote + round * timeoutDelta

def timeoutPrecommit(round: int) -> int:
    return initTimeoutPrecommit + round * timeoutDelta

class ProposalTimeout:
    def __init__(self, height: int, round: int):
        self.height = height
        self.round = round

class PrevoteTimeout:
    def __init__(self, height: int, round: int):
        self.height = height
        self.round = round

class PrecommitTimeout:
    def __init__(self, height: int, round: int):
        self.height = height
        self.round = round