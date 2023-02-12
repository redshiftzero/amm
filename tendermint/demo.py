#!/usr/bin/python3
import threading
import queue

from tendermint.app import n, f, TendermintProcess

if __name__ == '__main__': 
    # Algorithm assumes the following
    assert n > 3*f

    # Case in algorithm 1
    assert n == 3*f + 1

    queues = []
    for node_num in range(n):
        queues.append(queue.Queue())

    threads = list()
    for node_num in range(n):
        node = TendermintProcess(node_num, queues)
        x = threading.Thread(target=node.process_events, args=())
        threads.append(x)
        x.start()
