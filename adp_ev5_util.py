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
from sys import stdout
from os.path import basename
from os.path import isfile
import argparse
import logging
import time
from copy import copy

"""
   This section just handles help and command line argument processing 
"""
def process_args():
    desc = ("{0} --- Helper utilty to examine ADP Ev5 files"
            ).format(basename(argv[0]))
    epilog = "Put examples here"
    parser = argparse.ArgumentParser(description=desc, epilog=epilog)

    sub = parser.add_subparsers(title="subcommands", 
            description="valid subcommands", dest="cmd")

    # Statistics
    help_msg = ("prints out statistics for each file listed. "
            "Statistics include number of records, number of lines"
            "etc.")
    desc = ("prints out statistics for each file")
    epilog = "Put examples here"
    stats_p = sub.add_parser("stats",description=desc, epilog=epilog, 
            help=help_msg)
    stats_p.add_argument("stats", nargs="+", help=help_msg)

    # Compare
    help_msg = ("prints out a comparision of two files. Includes "
            "all the elements from the stats command as well as different "
            "types of record by record comparisions.")
    desc = "compare two files"
    epilog = "Put examples here"
    compare_p = sub.add_parser("compare", description=desc, epilog=epilog,
            help=help_msg)
    compare_p.add_argument("fcompare", nargs=2, help=help_msg)

    # Unique
    help_msg = ("outputs records that are unique to file 1. "
            "Different types of uniquiness can be specfified via optional"
            " flags")
    desc = ("output unique records")
    epilog = "Put examples here"
    unique_p = sub.add_parser("unique", description=desc, epilog=epilog,
            help=help_msg)
    unique_p.add_argument("unique", nargs=2, help=help_msg)
    unique_p.add_argument("-f", "--file", nargs=1, help="send output to file")

    return parser.parse_args()
    #END process_args

def setup_logging():
    global logd
    global logi
    global loge
    logging.basicConfig(filename='example.log',level=logging.DEBUG)
    sh = logging.StreamHandler(stdout)
    logging.getLogger().addHandler(sh)
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
        self.pf = parent_file
        self.job = None
        self.personal_data = None
        self.employment = None
        self.tax = None
        self.general_deduction = []
        self.direct_deposit = []
        self.fifth_field_earnings = []
        self.HR_user_data = None
        self.rec_str = ""
        return

    def __repr__(self): return self.rec_str
    def __hash__(self): return hash(self.rec_str)
    def __str__(self): return self.rec_str
    def __ne__(self, other): return not self.__eq__(other)
    def __eq__(self, other): 
        if ADP_File.match_type == ADP_File.EMP_ID:
            return self.emp_id == other.emp_id
        else: return self.rec_str == other.rec_str

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

##### END class adp_ev5_record


class ADP_File(object):
    # Class level variables
    PERFECT = 100
    EMP_ID = 101
    match_type = PERFECT

    def __init__(self, fname):
        self.fname = fname
        self.recs = [] #list of each record in file
        self.header = None
        self.footer = None
        self._reset_stats()
        self.compare_done = False
        self.compare_file = None

        # Self dup checks
        self.self_unique_perfect_matches = None 
        self.self_unique_perfect_match_cnt = 0
        self.self_unique_emp_id_matches = None 
        self.self_unique_emp_id_match_cnt = 0

        # Match stuff (vs other file)
        self.emp_id_matches = None
        self.perfect_matches = None
        self.perfect_match_cnt = 0
        self.emp_id_match_cnt = 0

        # Go through and process file
        self._proc_file(fname)
        self._dup_check()
        return

    def _reset_stats(self):
        self.rec_cnt = 0
        self.personal_data_cnt = 0
        self.employment_cnt = 0
        self.tax_cnt = 0
        self.fifth_field_earnings_cnt = 0
        self.direct_deposit_cnt = 0
        self.general_deduction_cnt = 0
        self.HR_user_data_cnt = 0
        return

    def __eq__(self, other): return self.fname == other.fname
    def __ne__(self, other): return not self.__eq__(other)

    """
        Checks for duplicate records and / or emp id's within the file
    """
    def _dup_check(self):
        ADP_File.match_type = ADP_File.PERFECT
        s = set(self.recs)
        self.self_unique_perfect_matches = s
        self.self_unique_perfect_match_cnt = len(s)

        ADP_File.match_type = ADP_File.EMP_ID
        s = set(self.recs)
        self.self_unique_emp_id_matches = s
        self.self_unique_emp_id_match_cnt = len(s)
        return

    """
        Given another file, returns a pointer to new file object that contains
        records that are unique to this file
    """
    def unique(self, other_file):
        if self.compare_done == False:
            self.compare(other_file)
        new_self = copy(self)
        # We are now effectively in a new object
        # Now we re-get stats and reprocess lines
        new_self._reset_stats()
        ns_set = new_self.self_unique_perfect_matches
        of_set = other_file.self_unique_perfect_matches
        new_self.recs = [] #need to reset the list of records
        for r in ns_set.difference(of_set):
            cur_rec = None
            for line in r.rec_str.splitlines():
                cur_rec = new_self._proc_line(line, cur_rec)
        # Rebuild footer
        new_self.footer = "TR|{}|{}|{}|{}|{}|{}|{}|{}".format(
                new_self.rec_cnt, new_self.personal_data_cnt,
                new_self.employment_cnt, new_self.tax_cnt, 
                new_self.general_deduction_cnt, new_self.direct_deposit_cnt,
                new_self.fifth_field_earnings_cnt, new_self.HR_user_data_cnt)
            
        return new_self

    def compare(self, other_file):
        ADP_File.match_type = ADP_File.PERFECT
        self.perfect_matches = self.self_unique_perfect_matches.intersection(
                other_file.self_unique_perfect_matches)
        self.perfect_match_cnt = len(self.perfect_matches)

        ADP_File.match_type = ADP_File.EMP_ID
        self.emp_id_matches = self.self_unique_emp_id_matches.intersection(
                other_file.self_unique_emp_id_matches)
        self.emp_id_match_cnt = len(self.emp_id_matches)
        self.compare_file = other_file
        self.compare_done = True
        return

    def compare_stats_str(self):
        if self.compare_done == False:
            ret_str =  "No file compare performed."
        else:
            cf = self.compare_file
            ret_str = ("{}:\n"
                    "  The following two files were compared:\n"
                    "\t'{}'\n\t'{}'\n"
                    "    - '{}' has {} total records\n"
                    "    - '{}' has {} total records\n"
                    "    - {} records are a perfect match\n"
                    "    - {} records have matching employee ids\n"
                    ).format(
                            time.asctime(), 
                            self.fname, cf.fname,
                            self.fname, self.rec_cnt, 
                            cf.fname, cf.rec_cnt, 
                            self.perfect_match_cnt,
                            self.emp_id_match_cnt) 
        return ret_str

    def file_stats_str(self):
        ret_str = ("File name: {}\n"
                "\tRecord count: {}\n"
                "\tDuplicate record count: {}\n"
                "\tDuplicate emp id count: {}\n"
                "\tPersonal data line count: {}\n"
                "\tEmployment line count: {}\n"
                "\tTax line count: {}\n"
                "\tGeneral deduction line count: {}\n"
                "\tDirect deposit line count: {}\n"
                "\tFifth field earnings line count: {}\n"
                "\tHR user data line count: {}\n"
                ).format(self.fname, self.rec_cnt, 
                        self.rec_cnt - self.self_unique_perfect_match_cnt,
                        self.rec_cnt - self.self_unique_emp_id_match_cnt, 
                        self.personal_data_cnt,
                        self.employment_cnt, self.tax_cnt, 
                        self.general_deduction_cnt, self.direct_deposit_cnt,
                        self.fifth_field_earnings_cnt, self.HR_user_data_cnt)
        return ret_str

    """
        Generates output suitable for a file, including header and footer
    """
    def generate_file(self, target=None):
        if target: t = open(target, 'w') 
        else: t = stdout

        t.write(self.header)
        for r in self.recs:
            for l in r.rec_str.splitlines():
                t.write("".join([l,"\n"]))
        t.write(self.footer)

        if target: t.close()
        return


    def _proc_file(self, fname):
        if not isfile(fname):
            loge("Unable to find file '{}'. Exitting with error".format(fname))
            exit(1)
        with open(fname) as fp:
            cur_rec = None
            self.header = next(fp) #consume the header line
            for line in fp:
                cur_rec = self._proc_line(line, cur_rec)
        return

    def _proc_line(self, line, cur_rec):
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
        return cur_rec
##### END class adp_ev5_file

"""
    Performs file compare
"""
def compare(file1, file2):
    f1 = ADP_File(file1)
    f2 = ADP_File(file2)
    print(f1.file_stats_str())
    print(f2.file_stats_str())
    f1.compare(f2)
    print(f1.compare_stats_str())
    return

def stats(flist):
    for f in flist:
        f = ADP_File(f)
        print(f.file_stats_str())
    return

def unique(file1, file2):
    f1 = ADP_File(file1)
    f2 = ADP_File(file2)
    f_unique = f1.unique(f2)
    f_unique.generate_file(target=args.file[0])

if __name__ == "__main__":
    args = process_args()
    setup_logging()

    if args.cmd == "compare":
        compare(args.fcompare[0], args.fcompare[1])
    elif args.cmd == "stats":
        stats(args.stats)
    elif args.cmd == "unique":
        unique(args.unique[0], args.unique[1])

