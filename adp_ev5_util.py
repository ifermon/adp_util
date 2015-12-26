#!/usr/bin/python

##############################################################################
#
# How to use this script:
#   1. You must have python installed on your machine
#   2. To run it directly if you have a non-PC (mac/linux) 
#       2.1 The first line needs to point to python To find your python type 
#           'which python'. Make sure the returned path is the same as in 
#           the first line of this file.
#       2.2. This script must be executable: 'chmod +x <fname>'
#   3. Run it using python type 'python <script name>'
#
##############################################################################
from sys import argv
from sys import exit
from os.path import basename
import argparse
import logging

"""
   This section just handles help and command line argument processing 
"""
def process_args():
    global args

    desc = ("{0} --- Helper utilty to examine ADP Ev5 files"
            ).format(basename(argv[0]))
    epilog = "Put examples here"
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)

    sub = parser.add_subparsers()

    # Statistics
    help_msg = ("prints out statistics for each file listed. "
            "Statistics include number of records, number of lines"
            "etc.")
    desc = ("prints out statistics for each file")
    epilog = "Put examples here"
    stats_p = sub.add_parser("stats",description=desc, epilog=epilog, 
            help=help_msg)
    stats_p.add_argument("files", nargs="+", help=help_msg)

    # Compare
    help_msg = ("prints out a comparision of two files. Includes "
            "all the elements from the stats command as well as different "
            "types of record by record comparisions.")
    desc = "compare two files"
    epilog = "Put examples here"
    compare_p = sub.add_parser("compare", description=desc, epilog=epilog,
            help=help_msg)
    compare_p.add_argument("file", nargs=2, help=help_msg)

    # Unique
    help_msg = ("outputs records that are unique to file 1. "
            "Different types of uniquiness can be specfified via optional"
            " flags")
    desc = ("output unique records")
    epilog = "Put examples here"
    unique_p = sub.add_parser("unique", description=desc, epilog=epilog,
            help=help_msg)
    unique_p.add_argument("file", nargs=2, help=help_msg)

    args = parser.parse_args()

    print(args)
    exit(1)
    return #END process_args

def setup_logging():
    global logd
    global logi
    global loge
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    logd = logging.debug
    logi = logging.info
    loge = logging.error
    return


class Record(object):
    def __init__(self):
        return

"""
    ADP eV5 records
    01 Job Record
    02 Personal Data Record
    03 Employment Record
    04 Tax Record
    05 General Deduction Record(s)
    06 Direct Deposit Record(s)
    07 Fifth Field Earnings Record(s)
    08 HR User Data Record
"""
class ADP_EV5_Record(Record):
    def __init__(self, parent_file, rec_id):
        self.rec_id = rec_id
        self.parent_file = parent_file
        self.job = None
        self.personal_data = None
        self.employment = None
        self.tax = None
        self.general_deduction = []
        self.direct_deposit = []
        self.fifth_field_earnings = []
        self.HR_user_data = None
        self.rec_str = ""
        self.perfect_matches = {}
        return

    def __str__(self): return self.rec_str
    def __eq__(self, other): return self.rec_str == other.rec_str
    def __ne__(self, other): return not self.__eq__(other)

    def _str(self, value): self.rec_str += value; return value

    #    Setter methods
    def set_job(s, v): 
        s.job = v
        s.emp_id = v.split("|")[1]
        s._str(v)
        return v
    def set_personal_data(s, v): s.personal_data = v; return s._str(v)
    def set_employment(s, v): s.employment = v; return s._str(v)
    def set_tax(s, v): s.tax = v; return s._str(v)
    def set_HR_user_data(s, v): s.HR_user_data = v; return s._str(v)
    def set_direct_deposit(s, v): s.direct_deposit.append(v); return s._str(v)
    def set_fifth_field_earnings(s, v): 
        s.fifth_field_earnings.append(v); return s._str(v)
    def set_general_deduction(s, v): 
        s.general_deduction.append(v); return s._str(v)

    def add_perfect_match(self, other_rec):
        pf = other_rec.parent_file
        if not self.perfect_matches.has_key(pf):
            self.perfect_matches[pf] = []
        self.perfect_matches[pf].append(other_rec)
        other_rec.add_perfect_match(self)
        return


##### END class adp_ev5_record

class ADP_File_Compare(object):
    def __init__(self, other_file):
        self.other_file = other_file
        self.perfect_match_cnt = 0
        self.perfect_match_list = []
        self.emp_id_match_cnt = 0
        self.emp_id_match_list = []
        return
    def add_perfect_match(self, r, other_r):
        self.perfect_match_cnt += 1
        self.perfect_match_list.append(r)
        r.add_perfect_match(other_r)
        return
    def add_emp_id_match(self, r, other_r):
        self.emp_id_match_cnt += 1
        self.emp_id_match_list.append(r)
        r.add_emp_id_match(other_r)
        return

class ADP_File(object):
    def __init__(self, fname):
        self.fname = fname
        self.recs = [] #list of each record in file
        self.rec_cnt = 0
        self.personal_data_cnt = 0
        self.employment_cnt = 0
        self.tax_cnt = 0
        self.fifth_field_earnings_cnt = 0
        self.direct_deposit_cnt = 0
        self.general_deduction_cnt = 0
        self.HR_user_data_cnt = 0
        self._proc_file(fname)
        self.file_compares = []
        return

    def __eq__(self, other): return self.fname == other.fname
    def __ne__(self, other): return not self.__eq__(other)

    def compare_file(self, other_file):
        fc = ADP_File_Compare(self, other_file)
        for r in self.recs:
            for other_r in other_file.recs:
                if r == other_r: fc.add_perfect_match_list.append(r)
                elif r.emp_id == other_r.emp_id: fc.add_emp_id_match(r, other_r)

    def _proc_file(self, fname):
        with open(fname) as fp:
            cur_rec = None
            self.header = next(fp) #consume the header line
            for line in fp:
                if line[:2] == "01":
                    self.rec_cnt += 1
                    cur_rec = ADP_EV5_Record(self, self.rec_cnt)
                    self.recs.append(cur_rec)
                    cur_rec.set_job(line)
                elif line[:2] == "02":
                    cur_rec.set_personal_data(line)
                    self.personal_data_cnt += 1
                elif line[:2] == "03":
                    cur_rec.set_employment(line)
                    self.employment_cnt += 1
                elif line[:2] == "08":
                    cur_rec.set_HR_user_data(line)
                    self.HR_user_data_cnt += 1
                elif line[:2] == "05":
                    cur_rec.set_general_deduction(line)
                    self.general_deduction_cnt += 1
                elif line[:2] == "06":
                    cur_rec.set_direct_deposit(line)
                    self.direct_deposit_cnt += 1
                elif line[:2] == "07":
                    cur_rec.set_fifth_field_earnings(line)
                    self.fifth_field_earnings_cnt += 1
                elif line[:2] == "04":
                    cur_rec.set_tax(line)
                    self.tax_cnt += 1
                elif line[:2] == "TR": self.footer = line
                else: loge("Unknown line\n{}".format(line))
        return

    def file_stats(self):
        ret_str = ("File name: {}\n"
                "\tRecord count: {}\n"
                "\tPersonal data line count: {}\n"
                "\tEmployment line count: {}\n"
                "\tTax line count: {}\n"
                "\tGeneral deduction line count: {}\n"
                "\tDirect deposit line count: {}\n"
                "\tFifth field earnings line count: {}\n"
                "\tHR user data line count: {}\n"
                ).format(self.fname, self.rec_cnt, self.personal_data_cnt,
                        self.employment_cnt, self.tax_cnt, 
                        self.general_deduction_cnt, self.direct_deposit_cnt,
                        self.fifth_field_earnings_cnt, self.HR_user_data_cnt)
        return ret_str
    


                


if __name__ == "__main__":
    #process_args()
    setup_logging()
    fn1 = argv[1]

    f1 = ADP_File(fn1)

    print(f1.file_stats())
    exit(1)

