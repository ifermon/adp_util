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
        

class record(object):
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
class adp_ev5_record(record):
    def __init__(self):
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

    """
        Takes a line of data from the file and puts it into the appropriate
        variable(s)
    """
    def put_data(self, data):
        result = {
                "01": self.job,
                "02": self.personal_data,
                "03": self.employment,
                "04": self.tax,
                "08": self.HR_user_data
                }.get(data[:2], -1)
        if result == -1:
            result = {
                "05": self.general_deduction,
                "06": self.direct_deposit,
                "07": self.fifth_field_earnings,
                }.get(data[:2], -2)
            if result == -2:
                print("I have a problem")
            else:
                result.append(data)
        else:
            result = data
        self.rec_str += data
        return

    def __str__(self):
        return self.rec_str


"""
    Health Equity Cobra records
"""
class he_record(record):
    def __init__(self):
        self.emp = None
        self.plan = None
        self.id = None #Record beginning with 'I'
        self.dep = [] #List of records beginning with 'D'
        self.dep_cnt = 0 
        self.cov = None #Record beginning with 'C'
        self.id_match = [] #Pointer to record(s) in other file I line matches
        self.idplan_match = []
        self.id_match_cnt = 0
        self.idplan_match_cnt = 0
        self.emp_id_match = []
        self.emp_id_match_cnt = 0
        self.emp_id = None #Emp id extracted, lowest level of match
        return

    def cancel(self):
        dep = []
        for d in self.dep:
            dep.append(d.replace('20991231','20160101'))
        self.dep = dep
        self.cov = self.cov.replace('20991231','20160101')
        return

    def __str__(self):
        ret = "{0}{1}{2}".format(self.emp, self.plan, self.id)
        for d in self.dep:
            ret += d
        ret += self.cov
        return ret
        
    def put_dep(self, dep):
        self.dep.append(dep)
        self.dep_cnt += 1
        return

    def put_id(self, ident):
        self.id = ident
        self.emp_id = ident.split("|")[1]
        return

    def put_id_match(self, other):
        self.id_match.append(other)
        self.id_match_cnt += 1
        other.id_match.append(other)
        other.id_match_cnt += 1
        return

    def put_emp_id_match(self, other):
        self.emp_id_match.append(other)
        self.emp_id_match_cnt += 1
        other.emp_id_match.append(other)
        other.emp_id_match_cnt += 1
        return

    def put_idplan_match(self, other):
        self.idplan_match.append(other)
        self.idplan_match_cnt += 1
        other.idplan_match.append(other)
        other.idplan_match_cnt += 1
        return

    def __eq__(self, other):
        return self.emp_id == other.emp_id

    def __ne__(self, other):
        return not self.__eq__(other)

    def match(self, other):
        m_cnt = 0
        if other == self:
            m_cnt = 1
            self.put_emp_id_match(other)
            if other.id == self.id:
                m_cnt = 2
                self.put_id_match(other)
                if other.cov == self.cov:
                    self.put_idplan_match(other)
                    m_cnt = 3
        return m_cnt

class f:
    def __init__(self, fname):
        self.fname = fname
        self.recs = []
        self.recs_unique = []
        self.recs_id_matches = []
        self.recs_idplan_matches = []
        self.match_id_cnt = 0
        self.match_idplan_cnt = 0
        self.match_emp_id_cnt = 0
        self.match_unique_cnt = 0
        self.recs_emp_id_matches = []
        self.stats_generated = False
        return

    def put_end_rec(self, end_rec):
        self.end_rec = end_rec
        return

    def _print_recs(self, recs):
        ret_str = ""
        for r in recs:
            ret_str += r.__str__()
        ret_str += self.end_rec
        return ret_str
    
    def __str__(self):
        return self._print_recs(self.recs)

    def emp_id_matches_str(self):
        return self._print_recs(self.recs_emp_id_matches)

    def unique_recs_str(self):
        return self._print_recs(self.recs_unique)

    def id_matches_str(self):
        return self._print_recs(self.recs_id_matches)

    def idplan_matches_str(self):
        return self._print_recs(self.recs_idplan_matches)

    def find_matches(self, other_file):
        for r in self.recs:
            found_match = False
            for other_r in other_file.recs:
                ret_val = r.match(other_r)
                if ret_val == 0:
                    pass
                elif ret_val == 1 and found_match == False:
                    self.match_emp_id_cnt += 1
                    self.recs_emp_id_matches.append(r)
                    found_match = True
                elif ret_val == 2 and found_match == False:
                    self.match_id_cnt += 1
                    self.recs_id_matches.append(r)
                    found_match = True
                elif ret_val == 3 and found_match == False:
                    self.recs_idplan_matches.append(r)
                    self.match_idplan_cnt += 1
                    found_match = True
                else:
                    print("Something wrong with match, probably found dups")
                    exit(2)
            if found_match == False:
                self.recs_unique.append(r)
                self.match_unique_cnt += 1
        self.stats_generated = True
        return

    def update_stats(self):
        if self.stats_generated == True:
            return
        for r in self.recs:
             if r.idplan_match_cnt != 0:
                 self.recs_idplan_matches.append(r)
                 self.match_idplan_cnt += 1
             elif r.id_match_cnt != 0:
                 self.recs_id_matches.append(r)
                 self.match_id_cnt += 1
             elif r.emp_id_match_cnt != 0:
                 self.recs_emp_id_matches.append(r)
                 self.match_emp_id_cnt += 1
             else:
                 self.recs_unique.append(r)
                 self.match_unique_cnt += 1
        self.stats_generated = True
        return


    def stats_str(self):
        ret_str = "File name: {}\n".format(self.fname)
        ret_str += "  Total Lines: {}\n".format(len(self.recs))
        ret_str += "  Unique records: {}\n".format(len(self.recs_unique))
        ret_str += "  Emp ID Matches: {}\n".format(self.match_emp_id_cnt)  
        ret_str += "  ID Field Matches: {}\n".format(self.match_id_cnt)  
        ret_str += "  ID & Plan Matches: {}".format(self.match_idplan_cnt)
        return ret_str

    def _process_cancels(self):
        for r in self.recs_unique:
            r.cancel()
        for r in self.recs_id_matches:
            r.cancel()
        return

    def cancel_str(self):
        self._process_cancels()
        ret_str = self.recs_unique_str() + self.id_matches_str() + \
                self.emp_id_matches_str()
        return ret_str

    def emp_id_compare_str(self):
        ret_str = ""
        for r in self.recs_emp_id_matches:
            ret_str += r.id
            for o in r.emp_id_match:
                ret_str += o.id
            ret_str += "\n"
        return ret_str

    def unique_emp_id_str(self):
        ret_str = ""
        for r in self.recs_unique:
            ret_str += "{}\n".format(r.emp_id)
        return ret_str

    def id_matches_emp_id_str(self):
        ret_str = ""
        for r in self.recs_id_matches:
            ret_str += "{}\n".format(r.emp_id)
        return ret_str

if __name__ == "__main__":
    #process_args()
    #script, cmd, fn1, fn2 = argv
    fn1 = argv[1]

    f1 = f(fn1)
    #f2 = f(fn2)
    with open(fn1) as fp:
        cur_rec = None
        for line in fp:
            print("processing: {}".format(line))
            if line[:2] == "01":
                print("Processed the following record:")
                print(cur_rec)
                cur_rec = adp_ev5_record()
                cur_rec.put_data(line)
            elif cur_rec != None:
                cur_rec.put_data(line)
            else:
                print("Not processed: {}".format(line))
    exit(1)

    for data_file in [f1, f2]:
        with open(data_file.fname) as fp:
            for line in fp:
               if line[0] == 'E':
                   cur_rec = record()
                   data_file.recs.append(cur_rec)
                   cur_rec.emp = line
               elif line[0] == 'P':
                   cur_rec.plan = line
               elif line[0] == 'I':
                   cur_rec.put_id(line)
               elif line[0] == 'D':
                   cur_rec.put_dep(line)
               elif line[0] == 'C':
                   cur_rec.cov = line
               elif line[0] == 'T':
                   data_file.put_end_rec(line)
               else: 
                   print("Does not match any known code, exit")
                   print(line)
                   exit(1)

    f1.find_matches(f2)
    f2.update_stats()

    help_str = "Help:\n"
    help_str += "  Syntax: he_diff <command> <file name> <file name>\n"
    help_str += "  Example: he_diff cancel file1.txt file2.txt\n"
    help_str += "  Commands:\n"
    help_str += "    cancel: Generates new HealthEquity file with cancels of\n"
    help_str += "      records that are in file 1 and not in file 2.\n"
    help_str += "    empid: Generates records from file 1 and file 2 where \n"
    help_str += "      the employee ID's match but the I record does not.\n"
    help_str += "    stats: Generates counts and types of matches.\n"
    help_str += "    unique: Prints employee id's from unique records in file 2.\n"

    if cmd == "stats":
        print(f1.stats_str())
        print(f2.stats_str())
    elif cmd == "empid":
        print("From {}\n{}".format(f1.fname, f1.emp_id_compare_str()))
    elif cmd == "cancel":
        print(f1.cancel_str())
    elif cmd == "unique":
        print(f2.unique_emp_id_str())
    elif cmd == "idmatches":
        print(f2.id_matches_emp_id_str())
    else:
        print(help_str)
