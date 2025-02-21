#!/usr/bin/python
# -*- coding: utf-8 -*-

# Practical Natural Language Processing Tools (practNLPTools): Combination of Senna and Stanford dependency Extractor
#
# Copyright (C) 2014 PractNLP Project
# Author: Biplab Ch Das' <bipla12@cse.iitb.ac.in>
# URL: <http://www.cse.iitb.ac.in/biplab12>
# For license information, see LICENSE.TXT

"""
A module for interfacing with the SENNA and Stanford Dependency Extractor.
SUPPORTED_OPERATIONS: It provides Part of Speech Tags, Semantic Role Labels, Shallow Parsing (Chunking), Named Entity Recognisation (NER), Dependency Parse and Syntactic Constituency Parse.
Requirement: Java Runtime Environment :)
"""

import subprocess
import os
from platform import architecture, system


class Annotator:
    r"""
    A general interface of the SENNA/Stanford Dependency Extractor pipeline that supports any of the
    operations specified in SUPPORTED_OPERATIONS.
....
    SUPPORTED_OPERATIONS: It provides Part of Speech Tags, Semantic Role Labels, Shallow Parsing (Chunking), Named Entity ....   ....Recognisation (NER), Dependency Parse and Syntactic Constituency Parse.
    Applying multiple operations at once has the speed advantage. For example,
    senna v3.0 will calculate the POS tags in case you are extracting the named
    entities. Applying both of the operations will cost only the time of
    extracting the named entities. Same is true for dependency Parsing.
    SENNA pipeline has a fixed maximum size of the sentences that it can read.
    By default it is 1024 token/sentence. If you have larger sentences, changing
    the MAX_SENTENCE_SIZE value in SENNA_main.c should be considered and your
    system specific binary should be rebuilt. Otherwise this could introduce
    misalignment errors.
    Example:

    """

    def getSennaTagBatch(self, sentences):
        input_data = ''
        for sentence in sentences:
            input_data += sentence + '\n'
        input_data = input_data[:-1]
        package_directory = os.path.dirname(os.path.abspath(__file__))
        os_name = system()
        executable = ''
        if os_name == 'Linux':
            bits = architecture()[0]
            if bits == '64bit':
                executable = 'senna-linux64'
            elif bits == '32bit':
                executable = 'senna-linux32'
            else:
                executable = 'senna'
        if os_name == 'Windows':
            executable = 'senna-win32.exe'
        if os_name == 'Darwin':
            executable = 'senna-osx'
        senna_executable = os.path.join(package_directory, executable)
        cwd = os.getcwd()
        os.chdir(package_directory)
        p = subprocess.Popen(senna_executable, stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        senna_stdout = p.communicate(input=input_data)[0]
        os.chdir(cwd)
        return senna_stdout.split('''

''')[0:-1]

    def getSennaTag(self, sentence):
        input_data = sentence.encode()
        package_directory = os.path.dirname(os.path.abspath(__file__))
        os_name = system()
        executable = ''
        if os_name == 'Linux':
            bits = architecture()[0]
            if bits == '64bit':
                executable = 'senna-linux64'
            elif bits == '32bit':
                executable = 'senna-linux32'
            else:
                executable = 'senna'
        if os_name == 'Windows':
            executable = 'senna-win32.exe'
        if os_name == 'Darwin':
            executable = 'senna-osx'
        senna_executable = os.path.join(package_directory, executable)
        cwd = os.getcwd()
        os.chdir(package_directory)
        p = subprocess.Popen(senna_executable, stdout=subprocess.PIPE,
                             stdin=subprocess.PIPE)
        senna_stdout = p.communicate(input=input_data)[0]
        os.chdir(cwd)
        return senna_stdout.decode()

    def getDependency(self, parse):
        package_directory = os.path.dirname(os.path.abspath(__file__))
        cwd = os.getcwd()
        os.chdir(package_directory)
        parsefile = open(cwd + '/in.parse', 'w')
        parsefile.write(parse)
        parsefile.close()
        p = subprocess.Popen([
            'java',
            '-cp',
            'stanford-parser.jar',
            'edu.stanford.nlp.trees.EnglishGrammaticalStructure',
            '-treeFile',
            cwd + '/in.parse',
            '-collapsed',
        ], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        p.wait()
        stanford_out = p.stdout.read()
        os.chdir(cwd)
        return stanford_out.strip()

    def getBatchAnnotations(self, sentences, dep_parse=False):
        annotations = []
        batch_senna_tags = self.getSennaTagBatch(sentences)
        for senna_tags in batch_senna_tags:
            annotations += [self.getAnnotationsAfterTagging(senna_tags)]
        if dep_parse:
            syntax_tree = ''
            for annotation in annotations:
                syntax_tree += annotation['syntax_tree']
            dependencies = \
                self.getDependency(syntax_tree).split('''

''')

            # print dependencies

            if len(annotations) == len(dependencies):
                for (d, a) in zip(dependencies, annotations):
                    a['dep_parse'] = d
        return annotations

    def getAnnotationsAfterTagging(self, senna_tags, dep_parse=False):
        annotations = {}
        senna_tags = map(lambda x: x.strip(), senna_tags.split('\n'))
        no_verbs = len(senna_tags[0].split('\t')) - 6
        words = []
        pos = []
        chunk = []
        ner = []
        verb = []
        srls = []
        syn = []
        for senna_tag in senna_tags:
            senna_tag = senna_tag.split('\t')
            words += [senna_tag[0].strip()]
            pos += [senna_tag[1].strip()]
            chunk += [senna_tag[2].strip()]
            ner += [senna_tag[3].strip()]
            verb += [senna_tag[4].strip()]
            srl = []
            for i in range(5, 5 + no_verbs):
                srl += [senna_tag[i].strip()]
            srls += [tuple(srl)]
            syn += [senna_tag[-1]]
        roles = []
        for j in range(no_verbs):
            role = {}
            i = 0
            temp = ''
            curr_labels = map(lambda x: x[j], srls)
            for curr_label in curr_labels:
                splits = curr_label.split('-')
                if splits[0] == 'S':
                    if len(splits) == 2:
                        if splits[1] == 'V':
                            role[splits[1]] = words[i]
                        else:
                            if splits[1] in role:
                                role[splits[1]] += ' ' + words[i]
                            else:
                                role[splits[1]] = words[i]
                    elif len(splits) == 3:
                        if splits[1] + '-' + splits[2] in role:
                            role[splits[1] + '-' + splits[2]] += ' ' \
                                                                 + words[i]
                        else:
                            role[splits[1] + '-' + splits[2]] = words[i]
                elif splits[0] == 'B':
                    temp = temp + ' ' + words[i]
                elif splits[0] == 'I':
                    temp = temp + ' ' + words[i]
                elif splits[0] == 'E':
                    temp = temp + ' ' + words[i]
                    if len(splits) == 2:
                        if splits[1] == 'V':
                            role[splits[1]] = temp.strip()
                        else:
                            if splits[1] in role:
                                role[splits[1]] += ' ' + temp
                                role[splits[1]] = \
                                    role[splits[1]].strip()
                            else:
                                role[splits[1]] = temp.strip()
                    elif len(splits) == 3:
                        if splits[1] + '-' + splits[2] in role:
                            role[splits[1] + '-' + splits[2]] += ' ' \
                                                                 + temp
                            role[splits[1] + '-' + splits[2]] = \
                                role[splits[1] + '-'
                                     + splits[2]].strip()
                        else:
                            role[splits[1] + '-' + splits[2]] = \
                                temp.strip()
                    temp = ''
                i += 1
            if 'V' in role:
                roles += [role]
        annotations['words'] = words
        annotations['pos'] = zip(words, pos)
        annotations['ner'] = zip(words, ner)
        annotations['srl'] = roles
        annotations['verbs'] = filter(lambda x: x != '-', verb)
        annotations['chunk'] = zip(words, chunk)
        annotations['dep_parse'] = ''
        annotations['syntax_tree'] = ''
        for (w, s, p) in zip(words, syn, pos):
            annotations['syntax_tree'] += s.replace('*', '(' + p + ' '
                                                    + w + ')')

        # annotations['syntax_tree']=annotations['syntax_tree'].replace("S1","S")

        if dep_parse:
            annotations['dep_parse'] = \
                self.getDependency(annotations['syntax_tree'])
        return annotations

    def getAnnotations(self, sentence, dep_parse=False):
        annotations = {}
        senna_tags = self.getSennaTag(sentence)
        senna_tags = list(map(lambda x: x.strip(), senna_tags.split('\n')))
        no_verbs = len(senna_tags[0].split('\t')) - 6
        words = []
        pos = []
        chunk = []
        ner = []
        verb = []
        srls = []
        syn = []
        for senna_tag in senna_tags[0:-2]:
            senna_tag = senna_tag.split('\t')
            words += [senna_tag[0].strip()]
            pos += [senna_tag[1].strip()]
            chunk += [senna_tag[2].strip()]
            ner += [senna_tag[3].strip()]
            verb += [senna_tag[4].strip()]
            srl = []
            for i in range(5, 5 + no_verbs):
                srl += [senna_tag[i].strip()]
            srls += [tuple(srl)]
            syn += [senna_tag[-1]]
        roles = []
        for j in range(no_verbs):
            role = {}
            i = 0
            temp = ''
            curr_labels = map(lambda x: x[j], srls)
            for curr_label in curr_labels:
                splits = curr_label.split('-')
                if splits[0] == 'S':
                    if len(splits) == 2:
                        if splits[1] == 'V':
                            role[splits[1]] = words[i]
                        else:
                            if splits[1] in role:
                                role[splits[1]] += ' ' + words[i]
                            else:
                                role[splits[1]] = words[i]
                    elif len(splits) == 3:
                        if splits[1] + '-' + splits[2] in role:
                            role[splits[1] + '-' + splits[2]] += ' ' \
                                                                 + words[i]
                        else:
                            role[splits[1] + '-' + splits[2]] = words[i]
                elif splits[0] == 'B':
                    temp = temp + ' ' + words[i]
                elif splits[0] == 'I':
                    temp = temp + ' ' + words[i]
                elif splits[0] == 'E':
                    temp = temp + ' ' + words[i]
                    if len(splits) == 2:
                        if splits[1] == 'V':
                            role[splits[1]] = temp.strip()
                        else:
                            if splits[1] in role:
                                role[splits[1]] += ' ' + temp
                                role[splits[1]] = \
                                    role[splits[1]].strip()
                            else:
                                role[splits[1]] = temp.strip()
                    elif len(splits) == 3:
                        if splits[1] + '-' + splits[2] in role:
                            role[splits[1] + '-' + splits[2]] += ' ' \
                                                                 + temp
                            role[splits[1] + '-' + splits[2]] = \
                                role[splits[1] + '-'
                                     + splits[2]].strip()
                        else:
                            role[splits[1] + '-' + splits[2]] = \
                                temp.strip()
                    temp = ''
                i += 1
            if 'V' in role:
                roles += [role]
        annotations['words'] = words
        annotations['pos'] = zip(words, pos)
        annotations['ner'] = zip(words, ner)
        annotations['srl'] = roles
        annotations['verbs'] = filter(lambda x: x != '-', verb)
        annotations['chunk'] = zip(words, chunk)
        annotations['dep_parse'] = ''
        annotations['syntax_tree'] = ''
        for (w, s, p) in zip(words, syn, pos):
            annotations['syntax_tree'] += s.replace('*', '(' + p + ' '
                                                    + w + ')')

        # annotations['syntax_tree']=annotations['syntax_tree'].replace("S1","S")

        if dep_parse:
            annotations['dep_parse'] = \
                self.getDependency(annotations['syntax_tree'])
        return annotations


def test():
    annotator = Annotator()
    print(annotator.getBatchAnnotations(['He killed the man with a knife and murdered him with a dagger.'
                                      , 'He is a good boy.'], dep_parse=True))
    print(annotator.getAnnotations('Republican candidate George Bush was great.'
                             , dep_parse=True)['dep_parse'])
    print(annotator.getAnnotations('Republican candidate George Bush was great.'
                             , dep_parse=True)['chunk'])


if __name__ == '__main__':
    test()
