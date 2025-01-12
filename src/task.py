import os
import util as u

def task(script: str, input: dict, output: dict, delegate):
    """Create a task"""
    return _Task(script, input, output, delegate)

def mgr():
    """Create a task manager"""
    return _TaskMgr()

class _Task:
    def __init__(self, script: str, input: dict, output: dict, delegate):
        self.script = script
        self.input = input
        self.output = output
        self.delegate = delegate

    def name(self):
        return os.path.basename(self.script)
    
    def run(self) -> str | None:
        input = {}
        for i, p in self.input.items():
            input[i] = u.home(p)
        output = {}
        for o, p in self.output.items():
            output[o] = u.home(p)
        d = self.delegate
        return d(input, output)
        

class _TaskMgr:
    outputs: set[str]
    queued: list[tuple[_Task, list[str]]]

    def __init__(self):
        self.outputs = set()
        self.queued = []

    def add(self, task: _Task) -> str | None:
        needed_inputs = []
        for input in task.input.values():
            if input.startswith("botw/"):
                # ignore botw/ inputs and assume they exist
                continue
            needed_inputs.append(u.home(input))
        # all inputs are satisfied?
        if not self._can_run(needed_inputs):
            # not satisfied, queue the task
            self.queued.append((task, needed_inputs))
            return None

        return self._schedule_tasks(task, needed_inputs)

    def _schedule_tasks(self, i_task: _Task, inputs: list[str]) -> str | None:
        exec_q = [(i_task, inputs)]
        while exec_q:
            task, inputs = exec_q.pop()
            if _is_up_to_date(task, inputs, list(task.output.values())):
                # outputs are up-to-date, skip the task
                print(f"===> {task.name():<30}: up-to-date")
            else:
                print(f"===  {task.name():<30}")
                err = task.run()
                if err is not None:
                    return err
            for o in task.output.values():
                self.outputs.add(u.home(o))
            old_q = self.queued
            self.queued = []
            for task, needed_inputs in old_q:
                if self._can_run(needed_inputs):
                    exec_q.append((task, needed_inputs))
                else:
                    self.queued.append((task, needed_inputs))

    def finish(self) -> str | None:
        if self.queued:
            for task, need_inputs in self.queued:
                print(f"===X {task.name():<30}: waiting for {need_inputs}")
            print("Available outputs are:")
            for o in self.outputs:
                print(f"  {o}")
            return "Some tasks could not be run"
        return None

    def _can_run(self, needed_inputs):
        for i in needed_inputs:
            if i not in self.outputs:
                return False
        return True
                    

        
def _is_up_to_date(task: _Task, inputs: list[str], outputs: list[str]):
    """
    Check if outputs are up-to-date. inputs or outputs can be a directory
    which means the first file in the directory will be checked
    """
    input_mtime = None
    for i in inputs + [task.script]:
        i = _get_real_path_for_mtime(i)
        if i is None:
            return False
        next_mtime = os.path.getmtime(i)
        if input_mtime is None or next_mtime > input_mtime:
            input_mtime = next_mtime
    for o in outputs:
        o = _get_real_path_for_mtime(o)
        if o is None or (input_mtime is not None and os.path.getmtime(o) < input_mtime):
            return False
    return True


def _get_real_path_for_mtime(path: str):
    if os.path.isdir(path):
        files = os.listdir(path)
        files.sort()
        if len(files) == 0:
            return None
        return os.path.join(path, files[0])
    if os.path.exists(path):
        return path
    return None
