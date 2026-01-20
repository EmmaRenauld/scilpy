unalias pytest
workon env_python3.12
# pip install prettytable

cd ~/my_applications/scil_vital/scilpy
rm -r .tests_reports
		#rm emma_all_files_coverage.txt
		#rm emma_detailed_coverage.txt
rm emma_dipy_funcs.txt
for f in src/scilpy/cli/*.py
do
    rm -r .coverage

    name=${f%.py}
    name=${name#src/scilpy/cli/scil_}
    echo "

--------------------------------
Processing pytest for script scil_$name
---------------------------------" 2>&1 | tee -a emma_detailed_coverage.txt

    # Coverage
    pytest src/scilpy/cli/tests/test_$name.py --cov-report json:.test_reports/coverage.json --cov-report html 

    # Detailed
    	# python emma_read_report_print_covered.py .test_reports/coverage.json 2>&1 | tee -a emma_detailed_coverage.txt

    # Single
    	# echo "$name : `python emma_read_report_print_covered.py --simple_output .test_reports/coverage.json`" >> emma_all_files_coverage.txt

    # Dipy functs
    #python emma_read_report_print_dipy_functions.py .test_reports/coverage.json
    echo "$name : `python emma_read_report_print_dipy_functions.py .test_reports/coverage.json`" >> emma_dipy_funcs.txt
done

