#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
- We ignore the function in __init__: always executed but it's only GET_HOME

"""
import argparse
import json

from prettytable import PrettyTable


def _build_arg_parser():
    p = argparse.ArgumentParser(description=__doc__,
                                formatter_class=argparse.RawTextHelpFormatter)
    p.add_argument('json_report_file')
    p.add_argument('--simple_output', action='store_true',
                   help="If set, prints:\n"
                        "total_covered: total_nb_func: ")

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

    # Prepare table
    field_names = ["File", "Covered*", "Nb func", "Lines in funcs", "Covered in funcs"]
    table = PrettyTable(field_names, align='r')
    table.align['File'] = 'l'

    total_executed = 0
    total_nb_functions = 0
    lines_in_functions = 0
    executed_in_functions = 0
    for f in files:
        # Ignoring __init__
        if f == 'src/scilpy/__init__.py':
            if not args.simple_output:
                print("Ignoring scilpy/__init__.py")
            continue

        # -----------
        # Total executed everywhere
        # (can't count ignored. Not interesting)
        # -----------
        lines_this_file = len(report['files'][f]['executed_lines'])
        if lines_this_file > 0:
            # print("{}: {}".format(f, nb_executed))

            # Adding to total.
            # Total should be the same as report['totals']['covered_lines']
            # without the __init__
            total_executed += lines_this_file

            # -----------
            # Total in functions
            # -----------
            functions = report['files'][f]['functions']
            nb_functions_this_file = 0
            executed_in_functions_this_file = 0
            lines_in_functions_this_file = 0
            rows_for_table = []

            for func in functions:
                if func == '':
                    # These are lines not in functions. Ex; all the imports
                    # Ignoring
                    continue

                # At least went inside the function?
                nb_executed_this_func = len(report['files'][f]['functions'][func]['executed_lines'])
                if nb_executed_this_func > 0:
                    total_this_func = nb_executed_this_func + len(report['files'][f]['functions'][func]['missing_lines'])
                    rows_for_table.append(["    -{}{}({} / {})".format(func, ' '*(35-len(func)), total_this_func, nb_executed_this_func), '', '', '', ''])

                    # Adding to totals for this file
                    nb_functions_this_file += 1
                    executed_in_functions_this_file += nb_executed_this_func
                    lines_in_functions_this_file += total_this_func

            # Add a row for this file
            table.add_row([f, lines_this_file, nb_functions_this_file, lines_in_functions_this_file, executed_in_functions_this_file])
            table.add_rows(rows_for_table)

            # Count total
            total_nb_functions += nb_functions_this_file
            lines_in_functions += lines_in_functions_this_file
            executed_in_functions += executed_in_functions_this_file

    if args.simple_output:
        print("{} : {} : {} : {}\n\n".format(total_executed, total_nb_functions, lines_in_functions, executed_in_functions))
    else:
        table.add_divider()
        table.add_row(['TOTAL', total_executed, total_nb_functions, lines_in_functions, executed_in_functions])
        print(table)
        print("*Except in __init__")

if __name__ == "__main__":
    main()
