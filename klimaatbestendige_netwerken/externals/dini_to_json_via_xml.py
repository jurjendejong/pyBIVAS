import argparse
import os
import sys
import re
import io
import tempfile
import json
import xmltodict
from datetime import datetime

# global _script_dir

'''
Converts a ini-file to a JSON-file
Chapters should be separated by a blank line, as is default for Delft3D FM
programmer: Jan.Mooiman@deltares.nl
'''


def parse_value(val):
    value = re.sub("([&])", r"&amp;", val)
    cnt = value.count("#")
    value2 = value
    if cnt == 1:
        end = value.find("#")
        value2 = value[0:end]
    if cnt == 2:
        # hash should be the first character, otherwise it is a comment hash
        begin = value.find("#")
        end = value[begin+1:].find("#")
        value2 = value[begin + 1:begin+1+end]
    if cnt == 3:
        begin = value.lstrip("#")
        end = value.rstrip("#")
        value2 = value[begin:end]

    return value2
    
    
def ini_to_json(in_file, out_file=None):
    """
    Convert Deltares ini to json file.
    If out_file is left empty, it returns the json as dictionairy
    """
    
    # print("Script directory : %s" % _script_dir)
    # print("Start directory  : %s" % start_dir)
    # print("Working directory: %s" % current_dir)

    with open(in_file, 'r') as f1:
        f2 = io.StringIO()
        # f2 = open(out_file, 'w')

        f2.write('<?xml version="1.0" encoding="utf-8" standalone="yes"?>\n')

        # f2.write('<data xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns="http://www.openda.org" xsi:schemaLocation="http://www.openda.org dataFile.xsd">\n')
        f2.write('<data>\n')

        record = f1.readline()  # read the first chapter
        while True:
            if not record:
                break
            if record == "\n" or record.strip()[0] == '#' or record.isspace():
                record = f1.readline()  # read next line
                continue
            elif record.strip()[0] == "[" and record.strip()[-1] == "]":
                chapter = record.strip()[1:-1]
                chapter = chapter.replace(" ", "_")
                f2.write('\t<%s>\n' % chapter)

                record = f1.readline()  # read the first keyword-value pair
                key, val = record.split("=", 1)
                key = key.strip().replace(" ", "_")
                value = parse_value(val)
                # if key contains the word FILE, adjust the file name to a json extension

                f2.write('\t\t<%s>%s</%s>' % (key.strip(), value.strip(), key.strip()))
                while True:  # read the key values
                    record = f1.readline()  # read the next keyword-value pair
                    if not record or record == "\n":
                        break
                    cnt = record.find("=")
                    if cnt > 0:
                        f2.write("\n")
                        key, val = record.split("=", 1)
                        key = key.strip().replace(" ", "_")
                        value = parse_value(val)
                        if str.find(key, 'File') != -1:
                            files = str.split(value, ';')
                            for file in files:
                                b_name, ext = os.path.splitext(file)
                                if ext.strip() == '.ini' or ext.strip() == '.ext':
                                    value = b_name + "_" + ext[1:].strip() + ".json"
                                    f2.write('\t\t<%s>%s</%s>' % (key.strip(), value.strip(), key.strip()))
                        else:
                            f2.write('\t\t<%s>%s</%s>' % (key.strip(), value.strip(), key.strip()))
                f2.write("\n")
                record = f1.readline()  # read the next chapter
            if not record.isspace() or record.strip()[0] == "[" and record.strip()[-1] == "]":
                f2.write('\t</%s>\n' % chapter)

        f2.write('</data>\n')
        f2.seek(0)   # set pointer at start of tmp-file

        xmlString = f2.read()
        jsonString = json.dumps(xmltodict.parse(xmlString), indent=4)

        # set chainage of a compound structure
        json_dict = json.loads(jsonString)
        nIds = []
        sIds = []
        j = json_dict.get('data').get('Structure')
        if j is not None:
            for data in json_dict.get('data').get('Structure'):
                if data['type'] == 'compound':
                    # add branchId and Chainage
                    strucIds = data['structureIds'].split(";")
                    # find strucIds[0], branchId and chainage
                    nIds.append(data['id'])
                    sIds.append(strucIds)
            for i in range(sIds.__len__()):
                chainage = get_chainage(json_dict.get('data').get('Structure'), sIds[i][0])
                error = set_chainage(json_dict.get('data').get('Structure'), nIds[i], chainage)
        # end: set chainage of a compound structure

        # set branchid to branchId
        j = json_dict.get('data').get('LateralDischarge')
        if j is not None:
            for data in json_dict.get('data').get('LateralDischarge'):
                val = data['branchid']
                if val is not None:
                    data['branchId'] = val
                    del data['branchid']
            for data in json_dict.get('data'):
                if data == 'LateralDischarge':
                    j = json_dict.get('data')
                    j['Lateral'] = j['LateralDischarge'] 
                    del j['LateralDischarge']
        # end: set branchid to branchId

        jsonString = json.dumps(json_dict, indent=4)
        if out_file is not None:
            with open(out_file, 'w') as f:
                f.write(jsonString)
            return
        else:
            return json_dict



def get_chainage(sdict, id):
   for data in sdict:
        if data['id'] == id:
            return data['chainage']


def set_chainage(sdict, id, chainage):
    for data in sdict:
        if data['id'] == id:
            data['chainage'] = chainage
            return 0
    return 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Batch process to count documented and undocumented test cases')
    # run_mode_group = parser.add_mutually_exclusive_group(required=False)
    parser.add_argument('-i', '--input',
                        help="Name of the input file.",
                        dest='in_file')
    args = parser.parse_args()

    src_dir = 'janm'
    start_dir = os.getcwd()
    if args.in_file:
        in_file = args.in_file
        src_dir = os.path.join(start_dir, )

    if not os.path.exists(in_file):
        print("Given file does not exists: %s" % src_dir)
        exit

    # _script_dir = os.path.join(start_dir, os.path.dirname(__file__))
    os.chdir(src_dir)
    current_dir = os.getcwd()

    b_name, ext = os.path.splitext(in_file)
    out_file = b_name + "_" + ext[1:] + ".json"
    if os.path.exists(out_file):
        os.remove(out_file)

    # --------------------------------------------------------------------------
    start_time = datetime.now()
    print('Start: %s\n' % start_time)
    ini_to_json(in_file, out_file)
    stop_time = datetime.now()
    print('\nJSON file is written to: %s' % os.path.join(current_dir, out_file))
    print('\nStart: %s' % start_time)
    print('End  : %s' % stop_time)
    dt = stop_time - start_time
    print('Dt   : %s' % dt)
    print('Klaar')
    # --------------------------------------------------------------------------
