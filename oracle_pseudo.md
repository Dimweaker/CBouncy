if 不会优化掉死循环:
    results = 对 orig.c 在所有优化等级下跑一遍
    if results只有RUNTIME_TIMEOUT:
        if mutant得到了checksum | mutant 崩溃:
            a suspected bug
        else:
            mutant 全是 ITMEOUT
            no bug
    if results只有唯一checksum:
        if mutant 出现 TIMEOUT | 崩溃 | checksum 不一致：
            a suspected bug
        else:
            no bug
    if results包含有唯一checksum和RUNTIME_TIMEOUT:
        if mutant 出现不同 checksum | 崩溃：
            a suspected bug
        else if mutant 和同等级 orig.c 比较 and 结果不一致:
            maybe a bug
        else:
            no bug
    if results 里出现结果不一致 | 崩溃:
        不进行变异
        a bug
else:
    abaabaa

