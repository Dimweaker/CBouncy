import json
import re
import sys

from filemanager import CaseManager, create_case_from_log
from configs import SIMPLE_OPTS, CSMITH_HOME, OPT_FORMAT


class Validator:
    def __init__(self, reduce_dir: str):
        self.case = create_case_from_log(f"{reduce_dir}/log.json")
        self.reduce_dir = reduce_dir

    def apply_transformation(self):
        # TODO: 获取creduce约简后的代码
        orig_r_code = " "

        for mutant in self.case.reduced_patch_mutants:
            for func, opts in mutant.functions.items():
                if not opts:
                    continue
                if func not in orig_r_code:
                    return False
                mutant_r_code = orig_r_code.replace(func, f"{func[:-1]} {OPT_FORMAT.format(','.join(opts))}")
                # TODO: 写入文件

        return True

    def check_file(self):
        # TODO: 编译检查
        return True



if __name__ == "__main__":
    reduce_dir = sys.argv[1]
    validator = Validator(reduce_dir)
    flag = validator.apply_transformation()
    if flag:
        flag = validator.check_file()
    # TODO: 输出flag
