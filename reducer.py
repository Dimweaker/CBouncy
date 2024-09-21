import random
import re
import subprocess
from shutil import copyfile
from tempfile import mkdtemp
import os

from filemanager import CaseManager, FileINFO, ReducedPatchFileINFO, CaseBuffer
from configs import PREFIX_TEXT, SUFFIX_TEXT, OPT_FORMAT, SIMPLE_OPTS, CSMITH_HOME

class Reducer:
    def __init__(self, inputbuffer: CaseBuffer, timeout: float = 5):
        self.inputbuffer = inputbuffer
        self.timeout = timeout

    def reduce(self):
        while True:
            # main loop of reducer thread
            case = self.inputbuffer.get()
            # 1. reduce patch for each case
            self.reduce_patch(case)
            # ! case reduction take place in sub tmpdir
            reduce_dir = mkdtemp(dir=case.case_dir)

            new_case = case.copyfiles(reduce_dir)
            new_case.save_log()

            self.reduce_case(reduce_dir)

    def reduce_patch(self, case: CaseManager):
        # reduce a single patch
        for mutant in case.mutants:
            mutant.reduce_patch(timeout=self.timeout)


    @staticmethod
    def get_declaration_scope(raw_code : str) -> str:
        """Get functions from a C source file"""
        declaration_scope = re.search(rf"{PREFIX_TEXT}(.+?){SUFFIX_TEXT}", raw_code, re.S)
        return declaration_scope.group() if declaration_scope else ""


    def reduce_case(self, reduce_dir: str):
        # ! turn off (pass-clex rename-toks), (pass-clang rename-fun) in creduce
        # TODO: deal with decl reduction in the file
        # backup files
        for root, _, files in os.walk(reduce_dir):
            for file in files:
                copyfile(f"{root}/{file}", f"{root}/{file}.orig")

        # generate a reduce bash