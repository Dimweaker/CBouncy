import sys
import os

current_file_path = os.path.abspath(__file__)

current_dir = os.path.dirname(current_file_path)
print(current_dir)
os.environ["PATH"] = f"{os.environ['PATH']}:{current_dir}"

from filemanager import create_case_from_log


class Validator:
    def __init__(self, reduce_dir: str):
        self.case = create_case_from_log(f"{reduce_dir}/log.json")
        self.reduce_dir = reduce_dir

    def apply_transformation(self):
        res = self.case.orig.res
        self.case.orig.process_file(timeout=1)
        if self.case.orig.res != res:
            return False
        for mutant in self.case.mutants:
            new_mutant = mutant.mutate(mutant_file=mutant.filepath.replace(".c", "_r.c"),
                                       opt_dict=mutant.functions, code=self.case.orig.text)
            if new_mutant is None:
                return False
            new_mutant.process_file(timeout=1)
            if new_mutant.res != mutant.res:
                return False
        return True


if __name__ == "__main__":
    reduce_dir = sys.argv[1]
    validator = Validator(reduce_dir)
    flag = validator.apply_transformation()
    with open(f"{reduce_dir}/flag", "a") as f:
        f.write("0" if flag else "1")
    exit(0 if flag else 1)
