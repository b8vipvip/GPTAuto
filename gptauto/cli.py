import argparse, uuid
from .engine import Signal, advance, is_complete
from .model import Task

def main():
    p=argparse.ArgumentParser(prog="gptauto"); s=p.add_subparsers(dest="command",required=True)
    i=s.add_parser("init"); i.add_argument("--goal",required=True); i.add_argument("--repo",required=True); i.add_argument("--done",action="append",default=[]); i.add_argument("--release-required",action="store_true"); i.add_argument("--out",default=".gptauto-task.json")
    st=s.add_parser("status"); st.add_argument("task")
    sp=s.add_parser("step"); sp.add_argument("task"); sp.add_argument("signal"); sp.add_argument("--reason",default="")
    a=p.parse_args()
    if a.command=="init":
        done=a.done or ["requested change implemented","required CI passed","final behavior verified"]
        t=Task(str(uuid.uuid4()),a.goal,a.repo,done,release_required=a.release_required); t.record("goal contract created"); t.save(a.out); print(a.out); return 0
    t=Task.load(a.task)
    if a.command=="status":
        print(f"{t.task_id} {t.state.value} complete={str(is_complete(t)).lower()} repairs={t.repair_attempts}/{t.max_repair_attempts}"); return 0
    advance(t,Signal(a.signal,a.reason)); t.save(a.task); print(t.state.value); return 0

if __name__=="__main__": raise SystemExit(main())
