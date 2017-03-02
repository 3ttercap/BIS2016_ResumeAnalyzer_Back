"""In this Package we will extract information from a given directory.
Supported file is PDF/DOCX."""
from __future__ import print_function
import threading
import time
from . import Utils
from langdetect import lang_detect_exception
from watson_developer_cloud import PersonalityInsightsV3, \
    WatsonException


class ResumeAnalyzer(threading.Thread):
    def __init__(self, thread_id, mongo_db, resume_directory, watson_pi_config,
                 watson_al_config):
        threading.Thread.__init__(self)
        self.thread_id = thread_id
        self.mongo_db = mongo_db
        self.resume_directory = resume_directory
        self.personality_insight = PersonalityInsightsV3(**watson_pi_config)

    def run(self):
        print(
            '\033[92mStart new thread with ID'
            '\033[94m {id}'
            '\033[92m for'
            '\033[94m {directory}'
            '\033[92m at'
            '\033[94m {timestamp}\033[0m'.format(
                id=self.thread_id,
                directory=self.resume_directory,
                timestamp=time.ctime(time.time())
            )
        )

        file_list = Utils.get_file_list(self.resume_directory)
        for f in file_list:
            self.text_process(f)

        print('\033[92mExit thread ID \033[94m{id}\033[0m'.format(id=self.thread_id))

    def text_process(self, file_info):
        if file_info[2] == 'pdf':
            try:
                resume_content, resume_lang = \
                    Utils.pdf_text_extract(file_info[0])
            except TypeError:
                return
            except lang_detect_exception.LangDetectException:
                return
        elif file_info[2] == 'docx':
            try:
                resume_content, resume_lang = \
                    Utils.docx_text_extract(file_info[0])
            except lang_detect_exception.LangDetectException:
                return
        else:
            return

        user_email = Utils.mail_catcher(resume_content)
        if user_email is not None:
            persons = self.mongo_db.persons
            person = persons.find_one({"email": user_email})
            if person is None:
                person = {
                    "email": user_email,
                    "resume_content": resume_content,
                    "resume_language": resume_lang,
                    "file_name": file_info[1],
                    "file_size": file_info[3],
                    "file_modified": file_info[4],
                    "personality_profile": self.watson_personality_insight(
                        resume_content.replace(user_email, ''), resume_lang
                    )
                }
                persons.insert_one(person)
                print("Insert new document for user %s" % user_email)
            else:
                try:
                    if person['file_name'] != file_info[1] or person['file_size'] != file_info[3]:
                        persons.update(
                            {"email": user_email},
                            {"$set": {
                                "resume_content": resume_content,
                                "resume_language": resume_lang,
                                "file_name": file_info[1],
                                "file_size": file_info[3],
                                "file_modified": file_info[4],
                                "personality_profile": self.watson_personality_insight(
                                    resume_content, resume_lang
                                )
                            }}
                        )
                        print("Update new document for user %s" % user_email)
                    elif person['personality_profile'] is None:
                        persons.update(
                            {"email": user_email},
                            {"$set": {
                                "personality_profile": self.watson_personality_insight(
                                    resume_content, resume_lang
                                )
                            }}
                        )
                        print("Update new document for user %s" % user_email)
                    else:
                        print("Existed resume %s!" % user_email)
                except KeyError:
                    persons.update(
                        {"email": user_email},
                        {"$set": {
                            "resume_content": resume_content,
                            "resume_language": resume_lang,
                            "file_name": file_info[1],
                            "file_size": file_info[3],
                            "file_modified": file_info[4],
                            "personality_profile": self.watson_personality_insight(
                                resume_content, resume_lang
                            )
                        }}
                    )
                    print("Update new document for user %s" % user_email)

    def watson_personality_insight(self, text, lang):
        if lang != 'en':
            return 'Resume not in English!'
        try:
            return self.personality_insight.profile(
                text, content_type='text/plain', content_language=lang,
                accept='application/json'
            )
        except UnicodeEncodeError:
            try:
                text = text.decode('utf-8')
            except UnicodeEncodeError:
                text = text.encode('utf-8')
            return self.personality_insight.profile(
                text, content_type='text/plain', content_language=lang,
                accept='application/json'
            )
        except WatsonException:
            return 'Not enough information!'
