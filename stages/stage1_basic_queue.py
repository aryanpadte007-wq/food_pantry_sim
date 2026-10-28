"""
Stage 1 - Basic queue.

Goal: learn the core SimPy idea. Students arrive at random times and
queue for ONE volunteer. We print what happens. No stock, no statistics.

Concepts shown: generator functions, simpy.Environment, simpy.Resource,
env.timeout, random arrival times.
"""

import random
import simpy

OPEN_MINUTES = 30       # short run so the output is readable
MEAN_ARRIVAL_GAP = 1.5  # average minutes between students
MEAN_SERVICE_TIME = 2.5 # average minutes to pack a parcel


def student(env, sid, counter):
    """One student arrives, waits for the volunteer, gets served, leaves."""
    arrived = env.now
    with counter.request() as req:
        yield req  # wait in the queue
        print(f"{env.now:6.1f}  student {sid} served after {env.now - arrived:.1f} min wait")
        yield env.timeout(random.expovariate(1 / MEAN_SERVICE_TIME))


def arrivals(env, counter):
    """Create new students until closing time."""
    sid = 0
    while env.now < OPEN_MINUTES:
        yield env.timeout(random.expovariate(1 / MEAN_ARRIVAL_GAP))
        sid += 1
        env.process(student(env, sid, counter))


if __name__ == "__main__":
    random.seed(42)
    env = simpy.Environment()
    counter = simpy.Resource(env, capacity=1)  # one volunteer
    env.process(arrivals(env, counter))
    env.run(until=OPEN_MINUTES + 30)
