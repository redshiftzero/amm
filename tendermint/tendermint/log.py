import logging
from typing import Optional, List

from tendermint.utils import id_of
from tendermint.messages import PREVOTE, PRECOMMIT, PROPOSAL

logger = logging.getLogger(__name__)

# TODO: Store round_p, h_p on log, check each message r, h before adding to log.
# TODO: Check that nodes only send one message each before adding to log.
class TendermintMessageLog:
    def __init__(self, node_id: int):
        self.p = node_id
        self._store = {
            'prevote': {},
            'precommit': {},
            'proposal': {},
        }

    def add_proposal(self, msg: PROPOSAL):
        self._store['proposal'][msg.value] = msg

    def add_prevote(self, msg: PREVOTE):
        try:
            self._store['prevote'][msg.id_v].append(msg)
        except KeyError:
            self._store['prevote'][msg.id_v] = [msg]
    
    def add_precommit(self, msg: PREVOTE):
        try:
            self._store['precommit'][msg.id_v].append(msg)
        except KeyError:
            self._store['precommit'][msg.id_v] = [msg]

    def proposal(self, value: str) -> Optional[PROPOSAL]:
        try:
            return self._store['proposal'][value]
        except KeyError:
            return None

    def proposals(self) -> List[PROPOSAL]:
        return self._store['proposal'].values()

    def num_prevotes(self) -> int:
        num_prevotes = 0
        for key in self._store['prevote'].keys():
            num_prevotes += len(self._store['prevote'][key])
        logger.debug(f"node {self.p} - got {num_prevotes} prevotes total")
        return num_prevotes

    def num_prevotes_for(self, value: Optional[str]) -> int:
        try:
            prevotes_for_value = self._store['prevote'][id_of(value)]
            logger.debug(f"node {self.p} - got {len(prevotes_for_value)} prevotes for {value}")
            return len(prevotes_for_value)
        except KeyError:
            return 0

    def num_precommits(self) -> int:
        num_precommits = 0
        for key in self._store['precommit'].keys():
            num_precommits += len(self._store['precommit'][key])
        logger.debug(f"node {self.p} - got {num_precommits} precommits total")
        return num_precommits

    def num_precommits_for(self, value: Optional[str]) -> int:
        try:
            precommits_for_value = self._store['precommit'][id_of(value)]
            logger.debug(f"node {self.p} - got {len(precommits_for_value)} precommits for {value}")
            return len(precommits_for_value)
        except KeyError:
            return 0