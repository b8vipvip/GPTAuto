from dataclasses import dataclass
from .model import State, Task

class ProtocolError(RuntimeError): pass

@dataclass(frozen=True)
class Signal:
    name: str
    reason: str = ""

TRANSITIONS={
 State.GOAL:{"accepted":State.INSPECT,"blocked":State.BLOCKED},
 State.INSPECT:{"ready":State.IMPLEMENT,"blocked":State.BLOCKED},
 State.IMPLEMENT:{"committed":State.PR,"blocked":State.BLOCKED},
 State.PR:{"opened":State.WAIT_CI,"blocked":State.BLOCKED},
 State.WAIT_CI:{"passed":State.MERGE,"failed":State.ANALYZE,"blocked":State.BLOCKED},
 State.ANALYZE:{"fixable":State.FIX,"blocked":State.BLOCKED},
 State.FIX:{"committed":State.WAIT_CI,"blocked":State.BLOCKED},
 State.MERGE:{"merged":State.MAIN_CI,"blocked":State.BLOCKED},
 State.MAIN_CI:{"passed":State.RELEASE,"failed":State.ANALYZE,"blocked":State.BLOCKED},
 State.RELEASE:{"released":State.VERIFY,"skipped":State.VERIFY,"failed":State.ANALYZE,"blocked":State.BLOCKED},
 State.VERIFY:{"verified":State.DONE,"failed":State.ANALYZE,"blocked":State.BLOCKED},
 State.BLOCKED:{"resume":State.INSPECT},
 State.DONE:{},
}

def advance(task: Task, signal: Signal):
    if task.state==State.ANALYZE and signal.name=="fixable":
        if task.repair_attempts>=task.max_repair_attempts:
            task.state=State.BLOCKED; task.record("repair budget exhausted; human decision required"); return task
        task.repair_attempts+=1
    allowed=TRANSITIONS.get(task.state,{})
    if signal.name not in allowed:
        raise ProtocolError(f"invalid transition: {task.state.value} + {signal.name}")
    old=task.state; task.state=allowed[signal.name]
    task.record(signal.reason or f"{old.value} --{signal.name}--> {task.state.value}")
    return task

def is_complete(task: Task):
    return task.state==State.DONE and bool(task.definition_of_done)
