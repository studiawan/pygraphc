import json


class AbstractionUtility(object):
    @staticmethod
    def read_abstraction_label_groundtruth(abstraction_label_file):
        with open(abstraction_label_file, 'r') as f:
            abstraction = json.load(f)
        return abstraction

    @staticmethod
    def read_logid_abstractionid_groundtruth(logid_abstractionid_file):
        with open(logid_abstractionid_file, 'r') as f:
            logid_absid = json.load(f)
        return logid_absid

    @staticmethod
    def write_perabstraction(final_abstraction, log_file, perabstraction_file):
        # read log file
        with open(log_file, 'r') as f:
            logs = f.readlines()

        # write logs per abstraction to file
        f_perabstraction = open(perabstraction_file, 'w')
        for abstraction_id, abstraction in final_abstraction.iteritems():
            f_perabstraction.write('Abstraction #' + str(abstraction_id) + ' '.join(abstraction['abstraction']))
            for line_id in abstraction['original_id']:
                f_perabstraction.write(str(line_id) + ' ' + logs[line_id])
            f_perabstraction.write('\n')
        f_perabstraction.close()

# filename = '/home/hudan/Git/datasets/casper-rw/logs-label-withid/auth.log'
# au = AbstractionUtility.read_abstraction_label_groundtruth(filename)
# for k, v in au.iteritems():
#     print k, v
