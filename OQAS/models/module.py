class Module:
    def __init__(self, module_id: int, module_code: str, module_name: str, lecturer_id: int):
        self.module_id = module_id
        self.module_code = module_code
        self.module_name = module_name
        self.lecturer_id = lecturer_id

    def describe(self):
        print(f"Module {self.module_code}: {self.module_name} (Lecturer ID: {self.lecturer_id})")
