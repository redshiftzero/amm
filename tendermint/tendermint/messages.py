from typing import Optional

# Used by the proposer of the current round to suggest a decision value.
class PROPOSAL:
    def __init__(self, h_p: int, round_p: int, value: str, validRound_p: int, from_node_id: int):
        self.h_p = h_p
        self.round_p = round_p
        self.value = value
        self.validRound_p = validRound_p
        self.from_node_id = from_node_id

    def __str__(self) -> str:
        return f'<PROPOSAL, {self.h_p}, {self.round_p}, {self.value}, {self.validRound_p}>'

# Vote for a proposed value.
class PREVOTE:
    def __init__(self, h_p: int, round_p: int, id_v: Optional[str]):
        self.h_p = h_p
        self.round_p = round_p
        self.id_v = id_v

    def __str__(self) -> str:
        return f'<PREVOTE, {self.h_p}, {self.round_p}, {self.id_v}>'

# Vote for the locked value.
class PRECOMMIT:
    def __init__(self, h_p: int, round_p: int, id_v: Optional[str]):
        self.h_p = h_p
        self.round_p = round_p
        self.id_v = id_v

    def __str__(self) -> str:
        return f'<PRECOMMIT, {self.h_p}, {self.round_p}, {self.id_v}>'