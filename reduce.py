import sys

from filemanager import create_case_from_log


class Validator:
    def __init__(self, reduce_dir: str):
        self.case = create_case_from_log(f"{reduce_dir}/log.json")
        self.reduce_dir = reduce_dir

    def apply_transformation(self):
        for mutant in self.case.mutants:
            new_mutant = mutant.mutate(mutant_file=mutant.filepath.replace(".c", "_r.c"),
                                       opt_dict=mutant.functions)
            if new_mutant is None:
                return False
            new_mutant.process_file(timeout=5)
            if new_mutant.res != mutant.res:
                return False
        return True


if __name__ == "__main__":
    reduce_dir = sys.argv[1]
    validator = Validator(reduce_dir)
    flag = validator.apply_transformation()
    print(int(flag))
