class Session:
    def __init__(self, session_id: int, module_id: int, date: str, run_id: int):
        self.session_id = session_id
        self.module_id = module_id
        self.date = date
        self.run_id = run_id

    def summary(self):
        print(f"Session {self.session_id}: Module {self.module_id} on {self.date} (Run {self.run_id})")
