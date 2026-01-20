#!/usr/bin/env python3
# -*- coding: utf-8 -*-


import argparse
import json

from prettytable import PrettyTable


def _build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('json_report_file')

    return p


def main():
    """
    function's covered_lines: - do not include the def function statement, even
    though they show green on the html report.
                              - include partial coverage

    report {
        'meta' {
            'format'
            'version'
            'timestamp'
            'branch_coverage'
            'show_contexts'
        }
        'files' {
            'my_script.py':
                'executed_lines'
                'summary'
                'missing_lines'
                'excluded_lines'
                'executed_branches'
                'missing_branches'
                'functions'
                'classes'
        }
        'totals' {
            'covered_lines': int
            'num_statements': int   (25 189)
            'percent_covered': float
            'percent_covered_display': rounded version of percent_covered
            'missing_lines': int
            'excluded_lines': int

            (note. branches = number of total ways we can cover the files with
            all the if-else)
            'num_branches': int
            'num_partial_branches': int
            'covered_branches': int
            'missing_branches': int
        }
    }
    """
    parser = _build_arg_parser()
    args = parser.parse_args()

    with open(args.json_report_file) as f:
        report = json.load(f)

    files = list(report['files'].keys())

    total_dipy_funcs = []
    total_similar = []
    for f in files:
        # Ignoring __init__
        if f == 'src/scilpy/__init__.py':
            continue

        # -----------
        # Total executed everywhere
        # (can't count ignored. Not interesting)
        # -----------
        lines_this_file = len(report['files'][f]['executed_lines'])
        if lines_this_file > 0:
            # Loading the whole file as text
            with open(f, "r") as ff:
                content = ff.readlines()

            # Finding dipy functions.
            dipy_modules = []
            dipy_funcs = []
            for line_number in report['files'][f]['executed_lines']:
                line = content[line_number - 1]

                # 1. Remove extra spaces/newlines
                line = line.strip()

                if line.startswith('from dipy.'):
                    if "(" in line:
                        line = line.replace("(", '')
                        i = 0
                        while ')' not in line:
                            line += content[line_number + i]
                            i += 1
                        line = line.replace(")", '')
                        line = line.strip()
                        line = line.replace(' ', '')

                    # Parse line.
                    module, funcs = line.split("import", 1)
                    module = module.replace("from", "").strip()
                    funcs = [f.strip() for f in funcs.split(",")]

                    for df in funcs:
                        dipy_funcs.append([module, df])
                elif line.startswith('import dipy.'):
                    if 'as' in line:
                        _, module = line.split("as", 1)
                    else:
                        print("??? import dipy without as?")
                        raise NotImplementedError
                    dipy_modules.append(module)

            # -----------
            # Entering in functions to see what's loaded
            # -----------
            functions = report['files'][f]['functions']
            used_dipy_funcs = []
            for func in functions:
                if func == '':
                    # These are lines not in functions. Ex; all the imports
                    # Ignoring
                    continue

                for line_number in report['files'][f]['functions'][func]['executed_lines']:
                    line = content[line_number - 1]

                    for module, df in dipy_funcs:
                        if df in line:
                            # make sure that it was exactly the same call
                            ind = line.index(df)
                            if (line[ind-1] in [" ", '.', '(', ')', '['] and
                                    line[ind + len(df)] in [" ", '.', '(', ')', '[']):
                                used_dipy_funcs.append(module + '.' + df)
                            else:
                                total_similar.append(df + " possibly in : " + line)

                    for module in dipy_modules:
                        if (module + '.') in line:
                            i = line.index(module + '.')
                            df = ''
                            while line[i+1] not in ['(', ' ']:
                                df += line[i+1]
                                i += 1
                            used_dipy_funcs.append(df)

            used_dipy_funcs = list(set(used_dipy_funcs))
            total_dipy_funcs.extend(used_dipy_funcs)

    total_dipy_funcs = list(set(total_dipy_funcs))
    print("similar: ", total_similar, "; used: ", total_dipy_funcs)

if __name__ == "__main__":
    main()
