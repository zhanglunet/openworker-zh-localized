"""精确复现：让 gate.set() 恰好落在「某次 tick 的 due() 扫描之后」。
此时 blocked 的 next_run 仍是 1.0（A 尚未 save），tick 会再 spawn 一个 B；
待 A 完成并释放 _running_ids 后 B 才首次执行 → 重复运行。"""
import asyncio, importlib.util, sys, tempfile, pathlib

def load(n,p):
    s=importlib.util.spec_from_file_location(n,p); m=importlib.util.module_from_spec(s)
    sys.modules[n]=m; s.loader.exec_module(m); return m
R=pathlib.Path('/home/user/openworker-zh-localized/coworker/automation')
pkg=type(sys)('coworker.automation'); pkg.__path__=[str(R)]; sys.modules['coworker.automation']=pkg
models=load('coworker.automation.models',R/'models.py')
store_m=load('coworker.automation.store',R/'store.py')
sched_m=load('coworker.automation.scheduler',R/'scheduler.py')
ScheduledTask,Schedule,TaskRun=models.ScheduledTask,models.Schedule,models.TaskRun

def mk(t): return ScheduledTask(title=t,instructions="x",
    schedule=Schedule(kind="cron",cron="0 9 * * 1"),workspace="/tmp/cw")

async def run_once(tmp):
    store=store_m.TaskStore(tmp/"a.db")
    blocked,quick=mk("blocked"),mk("quick")
    for t in (blocked,quick):
        store.save(t); store._conn.execute("UPDATE scheduled_tasks SET next_run=1.0 WHERE id=?", (t.id,))
    store._conn.commit()
    gate=asyncio.Event()
    async def runner(task,trigger):
        if task.id==blocked.id: await gate.wait()
        return TaskRun(task_id=task.id,status="ok",trigger=trigger)
    s=sched_m.Scheduler(store,runner,tick_seconds=0.05)

    # 包一层 due()：第 4 次扫描（此时 blocked 仍挂起、next_run 仍为 1.0）返回后立刻开闸。
    real_due=store.due; n=0
    def due(**kw):
        nonlocal n
        rows=real_due(**kw); n+=1
        if n==4: gate.set()      # ← 窗口：本次 tick 已决定 spawn B，随后 A 才完成并 save
        return rows
    store.due=due
    s.start(); await asyncio.sleep(0.5)
    got=store.get(blocked.id).run_count
    await s.stop(); return got

async def main():
    c={}
    for _ in range(15):
        with tempfile.TemporaryDirectory() as d:
            g=await run_once(pathlib.Path(d)); c[g]=c.get(g,0)+1
    bad=sum(v for k,v in c.items() if k!=1)
    print(f"精确对准窗口：run_count 分布 {c} → 重复运行 {bad}/15")
asyncio.run(main())
