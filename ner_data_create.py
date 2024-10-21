import os
import random

# Automaton for string matching
import ahocorasick
import re
from tqdm import tqdm
import sys


class Build_Ner_data:
    """
    This is a class for generating NER data. The main purpose is to label text from the medical.json file in the data folder.
    There are four types of labels ["Food", "Drug Company", "Treatment Method", "Drug"],
    and the entities corresponding to each label are in f'{type}.txt' under the data folder.
    Each entity is imported into the Aho-Corasick automaton, and pattern matching is performed on each text.
    """

    def __init__(self):
        self.idx2type = [
            "Disease",
            "Disease Symptoms",
            "Checkup Item",
            "Department",
            "Food",
            "Drug Company",
            "Treatment Method",
            "Drug",
        ]
        self.type2idx = {
            "Disease": 0,
            "Disease Symptoms": 1,
            "Checkup Item": 2,
            "Department": 3,
            "Food": 4,
            "Drug Company": 5,
            "Treatment Method": 6,
            "Drug": 7,
        }
        self.max_len = 30
        self.p = ["，", "。", "！", "；", "：", ",", ".", "?", "!", ";"]
        self.ahos = [ahocorasick.Automaton() for i in range(len(self.idx2type))]

        # Load all entities into the Aho-Corasick automaton
        for type in self.idx2type:
            with open(
                os.path.join("data", "ent_aug", f"{type}.txt"), encoding="utf-8"
            ) as f:
                all_en = f.read().split("\n")
            for en in all_en:
                if len(en) >= 2:
                    self.ahos[self.type2idx[type]].add_word(en, en)
        for i in range(len(self.ahos)):
            self.ahos[i].make_automaton()

    def split_text(self, text):
        """
        Randomly split long text into short text segments.

        :param text: Long text input
        :return: A list representing the split short texts
        :rtype: list
        """
        text = text.replace("\n", ",")
        pattern = r"([，。！；：,.?!;])(?=.)|[？,]"

        sentences = []

        for s in re.split(pattern, text):
            if s and len(s) > 0:
                sentences.append(s)

        sentences_text = [x for x in sentences if x not in self.p]
        sentences_punctuation = [x for x in sentences[1::2] if x in self.p]
        split_text = []
        now_text = ""

        # Random length, 15% chance of generating short text, 10% chance of generating long text
        for i in range(len(sentences_text)):
            if (
                len(now_text) > self.max_len
                and random.random() < 0.9
                or random.random() < 0.15
            ) and len(now_text) > 0:
                split_text.append(now_text)
                now_text = sentences_text[i]
                if i < len(sentences_punctuation):
                    now_text += sentences_punctuation[i]
            else:
                now_text += sentences_text[i]
                if i < len(sentences_punctuation):
                    now_text += sentences_punctuation[i]
        if len(now_text) > 0:
            split_text.append(now_text)

        # Randomly select 30% of the data and change the final punctuation to '。'
        for i in range(len(split_text)):
            if random.random() < 0.3:
                if split_text[i][-1] in self.p:
                    split_text[i] = split_text[i][:-1] + "。"
                else:
                    split_text[i] = split_text[i] + "。"
        return split_text

    def make_text_label(self, text):
        """
        Use the Aho-Corasick automaton to identify entities in the text and generate NER labels.

        :param text: Input text
        :return: A list representing the labels
        :rtype: list
        """
        label = ["O"] * len(text)
        flag = 0
        mp = {}
        for type in self.idx2type:
            li = list(self.ahos[self.type2idx[type]].iter(text))
            if len(li) == 0:
                continue
            li = sorted(li, key=lambda x: len(x[1]), reverse=True)
            for en in li:
                ed, name = en
                st = ed - len(name) + 1
                if st in mp or ed in mp:
                    continue
                label[st : ed + 1] = ["B-" + type] + ["I-" + type] * (ed - st)
                flag += 1
                for i in range(st, ed + 1):
                    mp[i] = 1
        return label, flag


# Write the text and corresponding labels to ner_data2.txt
def build_file(all_text, all_label):
    with open(os.path.join("data", "ner_data_aug.txt"), "w", encoding="utf-8") as f:
        for text, label in zip(all_text, all_label):
            for t, l in zip(text, label):
                f.write(f"{t} {l}\n")
            f.write("\n")


if __name__ == "__main__":
    print("hehe")
    with open(os.path.join("data", "medical.json"), "r", encoding="utf-8") as f:
        all_data = f.read().split("\n")
    build_ner_data = Build_Ner_data()

    all_text, all_label = [], []

    for data in tqdm(all_data):
        if len(data) < 2:
            continue
        data = eval(data)
        data_text = [
            data.get("desc", ""),
            data.get("prevent", ""),
            data.get("cause", ""),
        ]

        data_text_split = []
        for text in data_text:
            if len(text) == 0:
                continue
            text_split = build_ner_data.split_text(text)
            for tmp in text_split:
                if len(tmp) > 0:
                    data_text_split.append(tmp)
        for text in data_text_split:
            if len(text) == 0:
                continue
            label, flag = build_ner_data.make_text_label(text)
            if flag >= 1:
                assert len(text) == len(label)
                all_text.append(text)
                all_label.append(label)

    build_file(all_text, all_label)
