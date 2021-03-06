import json


class AbstractionUtility(object):
    @staticmethod
    def read_json(json_file):
        # read json data
        with open(json_file, 'r') as f:
            data = json.load(f)

        # change json key string to int
        converted_data = {}
        for key, value in data.iteritems():
            converted_data[int(key)] = value

        return converted_data

    @staticmethod
    def write_perabstraction(final_abstraction, log_file, perabstraction_file):
        # read log file
        with open(log_file, 'r') as f:
            logs = f.readlines()

        # write logs per abstraction to file
        f_perabstraction = open(perabstraction_file, 'w')
        for abstraction_id, abstraction in final_abstraction.iteritems():
            f_perabstraction.write('Abstraction #' + str(abstraction_id) + ' ' + abstraction['abstraction'] + '\n')
            for line_id in abstraction['original_id']:
                f_perabstraction.write(str(line_id) + ' ' + logs[line_id])
            f_perabstraction.write('\n')
        f_perabstraction.close()

    @staticmethod
    def write_perline(final_abstraction, log_file, perline_file):
        # read log file
        with open(log_file, 'r') as f:
            logs = f.readlines()

        # get line id and abstraction id
        abstraction_label = {}
        for abstraction_id, abstraction in final_abstraction.iteritems():
            for line_id in abstraction['original_id']:
                abstraction_label[line_id] = abstraction_id

        # write log per line with abstraction id
        f_perline = open(perline_file, 'w')
        for line_id, log in enumerate(logs):
            f_perline.write(str(abstraction_label[line_id]) + '; ' + log)
        f_perline.close()

    @staticmethod
    def get_abstractionid_from_groundtruth(logid_abstractionid_file, abstractions):
        # read ground truth
        abstraction_groundtruth = AbstractionUtility.read_json(logid_abstractionid_file)
        groundtruth_length = len(abstraction_groundtruth.keys())

        abstractions_edited_id = {}
        for abstraction_id, abstraction in abstractions.iteritems():
            # if abstraction exist in ground truth, get id from dictionary key
            if abstraction['abstraction'] in abstraction_groundtruth.values():
                new_id = \
                    abstraction_groundtruth.keys()[abstraction_groundtruth.values().index(abstraction['abstraction'])]

            # if not exist, new id is dictionary length + 1
            else:
                new_id = groundtruth_length
                groundtruth_length += 1

            abstractions_edited_id[new_id] = abstraction

        return abstractions_edited_id
