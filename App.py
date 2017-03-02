from __future__ import print_function
import argparse
import yaml
import pymongo
from Utils import setting_globals, v_print
from ResumeAnalyzer import ResumeAnalyzer


parser = argparse.ArgumentParser(
    description='Extract information and analyze from collection of resumes.'
)
parser.add_argument(
    '--config', '-c',
    help='Path to configuration YAML file',
    type=str,
    required=True
)
parser.add_argument(
    '--verbose', '-v',
    help='Show all logs.',
    action='store_true'
)

print('Begin the program!')
args = parser.parse_args()
setting_globals(verbose=args.verbose)

if args.config.endswith('.yaml'):
    print('Loading config from %s' % args.config)
    configs = yaml.load(open(args.config, 'r'))
else:
    raise ValueError('Configuration must be a YAML file!')

mongo_db = pymongo.MongoClient(**configs['mongo']['conn'])[configs['mongo']['database']]
resume_dirs = configs['resume_directories']
threads = []

for i in range(0, len(resume_dirs)):
    threads.append(
        ResumeAnalyzer(
            i, mongo_db, resume_dirs[i],
            configs['watson_personal_insight'],
            configs['watson_alchemy_language']
        )
    )
    threads[i].start()

for t in threads:
    t.join()

print('\n.\nFinish the program!')
