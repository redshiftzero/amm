
from typing import Dict, List, NoReturn, Optional, Union

import logging
import time
import threading
import queue

from tendermint.timers import (ProposalTimeout, PrevoteTimeout, PrecommitTimeout,
                               timeoutPropose, timeoutPrevote, timeoutPrecommit)
from tendermint.messages import PREVOTE, PRECOMMIT, PROPOSAL
from tendermint.log import TendermintMessageLog
from tendermint.utils import getValue, valid, id_of

logger = logging.getLogger(__name__)

# Variables with index p are process local state variables
# Variables w/o index p are value placeholders

# Total voting power of processes in the system
n = 10
# Proposers have an ID 0..=9

# Total voting power of faulty processes in the system
f = 3

# Each round has a dedicated proposer.
# Mapping of rounds to proposers is known by all processes.
def proposer(h: int, round: int) -> int:
    # Not specified in the paper, here we choose h mod n
    # Implicit assumption here: Equal voting power
    return h % n

class TendermintProcess:
    def __init__(self, tendermint_id: int, queues: Dict[int, queue.Queue]):
        self.p = tendermint_id  # Proposer/node ID
        self.h_p = 0  # Current height
        self.round_p = 0  # Current round number

        # Current state of the state machine, 'propose', 'prevote', 'precommit'
        self.step_p = 'propose'

        # The most recent value for which a PRECOMMIT message has been sent
        self.lockedValue_p = None
        # The last round in which the process sent a PRECOMMIT that is not nil
        self.lockedRound_p = -1
        # A correct process locks a value v in a round r by setting
        # lockedValue=v and lockedRound=r before sending PRECOMMIT for id(v) 

        # The most recent possible decision value, where a decision value is one
        # where PROPOSAL and 2f+1 PREVOTE messages are received in a round r
        self.validValue_p = None
        # The last round in which validValue is updated
        self.validRound_p = -1

        # Committed values, one decision value per height
        self.decision_p = []

        # Log of received messages this round
        self.message_log = TendermintMessageLog(self.p)

        # Setup the "network"
        self.receive_q = queues[self.p]
        self.send_qs = {}
        for node_num in self.get_network_peers():
            self.send_qs[node_num] = queues[node_num]

        # Setup flags for the "for the first time" conditions
        self.firstPrevote = False
        self.firstPrecommit = False
        self.locked = False

        # Flags to stop running timers
        self.proposalTimer = False
        self.prevoteTimer = False
        self.precommitTimer = False

    def get_network_peers(self):
        node_ids = list(range(n))
        node_ids.pop(self.p)
        return node_ids

    def send_to_node(self, node_num: int, msg) -> None:
        # Allows "sending" to self
        if node_num == self.p:
            self.put_event_on_queue(msg)
            return

        try:
            logger.debug(f"node {self.p} - sending to {node_num}: {str(msg)}")
            self.send_qs[node_num].put(msg)
        except RuntimeError:
            logger.debug(f"peer {node_num} seems down, dropping")

    def receive(self):
        return self.receive_q.get()

    def put_event_on_queue(self, msg) -> None:
        self.receive_q.put(msg)

    def broadcast(self, message):
        # for demo purposes so things aren't so fast in scrollback
        time.sleep(0.1)
        for node_num in self.get_network_peers():
            self.send_to_node(node_num, message)

    def process_events(self) -> NoReturn:
        time.sleep(2)  # Wait for nodes to start
        self.startRound(self.round_p)
        while True:
            event = self.receive()

            if isinstance(event, PROPOSAL):
                logger.debug(f"node {self.p} - Got PROPOSAL - {event}")
                self.message_log.add_proposal(event)
                self.process(event)
            elif isinstance(event, PREVOTE):
                logger.debug(f"node {self.p} - Got PREVOTE - {event}")
                self.message_log.add_prevote(event)
                self.process(event)
            elif isinstance(event, PRECOMMIT):
                logger.debug(f"node {self.p} - Got PRECOMMIT - {event}")
                self.message_log.add_precommit(event)
                self.process(event)
            elif isinstance(event, ProposalTimeout):
                logger.info(f"node {self.p} - BOOM - ProposalTimeout hit for round {event.round} and block height {event.height}")
                self.onTimeoutPropose(event.height, event.round)
            elif isinstance(event, PrevoteTimeout):
                logger.info(f"node {self.p} - BOOM - PrevoteTimeout hit for round {event.round} and block height {event.height}")
                self.onTimeoutPrevote(event.height, event.round)
            elif isinstance(event, PrecommitTimeout):
                logger.info(f"node {self.p} - BOOM - PrecommitTimer hit for round {event.round} and block height {event.height}")
                self.onTimeoutPrecommit(event.height, event.round)
            else:
                logger.error(f"node {self.p} - Don't know what this event/message is... skipping")

    def process(self, message):
        # Algorithm 1, Line 22
        if isinstance(message, PROPOSAL) and message.h_p == self.h_p and \
              message.round_p == self.round_p and message.validRound_p == -1 and \
              message.from_node_id == proposer(self.h_p, self.round_p) and self.step_p == 'propose':
            logger.debug(f"node {self.p} - running gotProposal")
            self.gotProposal(message.value)
            return

        # Algorithm 1, Line 28
        for message in self.message_log.proposals():  # Try to see if the condition is met for any observed proposal.
            # TODO: Simplify by only adding proposal for h_p and round_p to message_log
            if message.h_p == self.h_p and message.round_p == self.round_p and message.validRound_p != -1 and \
                message.from_node_id == proposer(self.h_p, self.round_p) and self.step_p == 'propose' and \
                (self.message_log.num_prevotes_for(message.value) >= (2 * f + 1)) and \
                valid(message.value) and (self.lockedRound_p <= message.validRound_p or self.lockedValue_p == message.value):
                logger.debug(f"node {self.p} - running gotProposalAndPrevotes")
                self.gotProposalAndPrevotes(message.value, message.validRound_p)
                return

        # Algorithm 1, Line 34
        if self.step_p == 'prevote' and self.firstPrevote == False and self.message_log.num_prevotes() >= (2 * f + 1):
            self.firstPrevote = True
            self.onFirstPrevote()
            return

        # Algorithm 1, Line 36
        for message in self.message_log.proposals():  # Try to see if the condition is met for any observed proposal.
            if message.h_p == self.h_p and message.round_p == self.round_p and \
                message.from_node_id == proposer(self.h_p, self.round_p) and valid(message.value) and \
                (self.step_p == 'prevote' or self.step_p == 'precommit') and \
                (self.message_log.num_prevotes_for(message.value) >= (2 * f + 1)) and self.locked == False:
                logger.info(f"node {self.p} - running lockValue")
                self.locked = True
                self.lockValue(message.value, self.round_p)
                return

        # Algorithm 1, line 44
        if self.step_p == 'prevote' and (self.message_log.num_prevotes_for(None) >= (2 * f + 1)):
            logger.debug(f"node {self.p} - running moveToNilPrecommit")
            self.moveToNilPrecommit()
            return

        # Algorithm 1, line 47 
        if self.firstPrecommit == False and self.message_log.num_precommits() >= (2 * f + 1):
            self.firstPrecommit = True
            self.onFirstPrecommit()
            return

        # Algorithm 1, line 49 
        proposal = self.message_log.proposal(self.lockedValue_p)
        if proposal and proposal.h_p == self.h_p and proposal.round_p == self.round_p and proposal.from_node_id == proposer(self.h_p, self.round_p) and \
              (self.message_log.num_precommits_for(proposal.value) >= (2 * f + 1)):
            try:
                self.decision_p[self.h_p]
            except IndexError:
                logger.debug(f"node {self.p} - running commit")
                self.commit(proposal.value)
            return

        # Algorithm 1, line 55-56
        # If we have at least f + 1 messages for a round that is greater than self.round_p, then we should start a new round
        # ourselves. This means we are behind. 
        # TODO: Store in the main message log only messages for this round and block height. Add to a new field messages for out of round.
        # THEN RUN self.startRound(round)

    """
    If we run this function, it means we ran out of time to get a value from the proposer.
    We vote on a nil value and move on to the PREVOTE stage.
    
    Algorithm 1: Lines 57-60
    """
    def onTimeoutPropose(self, height: int, round: int):
        if height == self.h_p and round == self.round_p and self.step_p == 'propose':
            self.broadcast(PREVOTE(self.h_p, self.round_p, None))
            self.proposalTimer = False
            self.step_p = 'prevote'

    """
    If we run this function, it means we ran out of time to finish the prevote process.
    
    Algorithm 1: Lines 61-64
    """
    def onTimeoutPrevote(self, height: int, round: int):
        if height == self.h_p and round == self.round_p and self.step_p == 'prevote':
            self.broadcast(PRECOMMIT(self.h_p, self.round_p, None))
            self.prevoteTimer = False
            self.step_p = 'precommit'

    """
    If we run this function, it means we ran out of time to finish the precommit. We need
    to just start a new round.

    Algorithm 1: Lines 65-67
    """
    def onTimeoutPrecommit(self, height: int, round: int):
        if height == self.h_p and round == self.round_p:
            self.startRound(self.round_p + 1)

    """
    At the end of this stage, we have either proposed a value, or set up a timeout to move on
    to PREVOTE with a None value if the proposer misbehaves or doesn't act in time.

    Algorithm 1: Lines 11-21
    """
    def startRound(self, round: int):
        logger.debug(f"node {self.p} - starting new round!")
        # Stop all running timers
        self.proposalTimer = False
        self.prevoteTimer = False
        self.precommitTimer = False

        # # Clear out the log
        # self.message_log = TendermintMessageLog(self.p)

        self.round_p = round
        self.step_p = 'propose'

        # pausing to start the round for demo purposes
        time.sleep(1)

        if proposer(self.h_p, self.round_p) == self.p:  # We test if we are the proposer this round
            if self.validValue_p != None:
                # Q. When does a process get in here?
                # A. When a proposer is starting a round where they had a valid value from the previous round?
                proposal = self.validValue_p
            else:
                proposal = getValue()

            proposed_msg = PROPOSAL(self.h_p, self.round_p, proposal, self.validRound_p, self.p)
            self.broadcast(proposed_msg)
            # Also send to self so that we can process the proposal and prevotes as if we were any other node
            self.send_to_node(self.p, proposed_msg)
        else:  # We're not the proposer this round, give the proposer some time
            self.proposalTimer = True
            threading.Thread(target=self.startTimeoutProposal, args=(self.h_p, self.round_p)).start()

    def startTimeoutProposal(self, height, round):
        while self.proposalTimer:
            logger.debug(f"node {self.p} - setting proposal timer")
            e = ProposalTimeout(height, round)
            time.sleep(timeoutPropose(round))
            self.put_event_on_queue(e)

    """
    This has the logic for what we do when we get a value from the proposer. It ends with us
    broadcasting a prevote message and entering the prevote stage.

    Algorithm 1: Lines 22-27
    """
    def gotProposal(self, value: str):
        if valid(value) and (self.lockedRound_p == -1 or self.lockedValue_p == value):
            # Looks good let's vote for this
            self.broadcast(PREVOTE(self.h_p, self.round_p, id_of(value)))
        else:  # Invalid, lets vote nil
            self.broadcast(PREVOTE(self.h_p, self.round_p, None))

        self.proposalTimer = False
        self.step_p = 'prevote'

    """
    This has the logic for what we do once we get a proposal from a proposer (as in gotProposal)
    and ALSO we have gotten 2f+1 prevote messages from our fellow nodes with that value. It ends with us
    broadcasting a prevote message and entering the prevote stage.

    Q: When do we hit this and when do we hit gotProposal?
    A: We hit this when the decision value has been observed by the proposer before, we hit gotProposal when
    it's a new decision value?

    Q: What is the deal with the checks on vr?
    A: The checks on vr are asserting that the round we're in is less than vr (when does this happen?) or
    we're already locked on this value. We still check validity of the value just in case the state has evolved
    from the first time we saw the value.

    Algorithm 1: Lines 28-33
    """
    def gotProposalAndPrevotes(self, value: str, vr: int):
        if valid(value) and (self.lockedRound_p <= vr or self.lockedValue_p == value):
            # Looks good let's vote for this
            self.broadcast(PREVOTE(self.h_p, self.round_p, id_of(value)))
        else:  # Invalid, lets vote nil
            self.broadcast(PREVOTE(self.h_p, self.round_p, None))

        self.proposalTimer = False
        self.step_p = 'prevote'

    """
    As soon as we get 2f+1 PREVOTE messages for any value, start our prevote timer.

    Algorithm 1: Lines 34-35
    """
    def onFirstPrevote(self):
        self.prevoteTimer = True
        threading.Thread(target=self.startTimeoutPrevote, args=(self.h_p, self.round_p)).start()

    def startTimeoutPrevote(self, height, round):
        while self.prevoteTimer:
            logger.debug(f"node {self.p} - setting prevote timer")
            e = PrevoteTimeout(height, round)
            time.sleep(timeoutPrevote(round))
            self.put_event_on_queue(e)

    """
    If we get a proposal value from the proposer, and we get 2f + 1 prevotes for that value
    while the value is valid (valid(v)) and we're in the prevote or precommit stages for the first time.

    Algorithm 1: Lines 36-43
    """
    def lockValue(self, value: str, round_p: int):
        if self.step_p == 'prevote':
            self.lockedValue_p = value
            self.lockedRound_p = round_p
            self.broadcast(PRECOMMIT(self.h_p, self.round_p, id_of(value)))
            self.prevoteTimer = False
            self.step_p = 'precommit'

        self.validValue_p = value
        self.valueRound_p = round_p

    """
    This step says that if we get 2f+1 PREVOTE messages for the nil value, we should just move
    to the PRECOMMIT step with the nil value. This round has failed.

    Algorithm 1: Lines 44-46
    """
    def moveToNilPrecommit(self):
        self.broadcast(PRECOMMIT(self.h_p, self.round_p, None))
        self.prevoteTimer = False
        self.step_p = 'precommit'

    """
    As soon as we get 2f+1 PRECOMMIT messages for any value, start the precommit timer.

    Algorithm 1: Lines 47-48
    """
    def onFirstPrecommit(self):
        self.precommitTimer = True
        threading.Thread(target=self.startTimeoutPrecommit, args=(self.h_p, self.round_p)).start()

    def startTimeoutPrecommit(self, height: int, round: int):
        while self.precommitTimer:
            logger.debug(f"node {self.p} - setting precommit timer")
            e = PrecommitTimeout(height, round)
            time.sleep(timeoutPrecommit(round))
            self.put_event_on_queue(e)

    """
    If we have a Proposal value from the valid proposer, and we've had 2f+1 precommits, and we haven't committed
    a value yet this round, then we commit the value and start the next round.

    Algorithm 1: Lines 49-54
    """
    def commit(self, value: str):
        if valid(value):
            # Stop all running timers
            self.proposalTimer = False
            self.prevoteTimer = False
            self.precommitTimer = False

            logger.info(f"node {self.p} - COMMITTING! - {value}")
            self.decision_p.append(value)
            assert len(self.decision_p) - 1 == self.h_p

            # Start new round and set per-round state to initial values
            self.h_p += 1
            logger.info(f"node {self.p} - new block height - {self.h_p}")
            self.round_p = 0

            self.lockedRound_p = -1
            self.lockedValue_p = None
            self.validRound_p = -1
            self.validValue_p = None
            self.message_log = TendermintMessageLog(self.p)

            self.firstPrevote = False
            self.firstPrecommit = False
            self.locked = False

            # pausing between rounds for demo purposes
            time.sleep(1)

            self.startRound(self.round_p)
