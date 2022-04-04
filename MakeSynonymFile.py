#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import regex as re
import csv
from typing import List
import click

def read_in_thesaurus(file:str, n=2) -> List[List[str]]:
    """
    Liest den OpenThesaurus ein und erzeugt Liste von Listen von je n Synonymen, wobei der default von n 2 ist. Ausgewählt werden je die ersten n Synonyme, die der Thesaurus nennt.

    :param file: Name der (bzw. Pfad zur) einzulesenden Thesaurusdatei
    :param n: Voreinstellung 2; gibt an, wie viele Synonyme je Zeile verwendet werden sollen
    """
    with open(file) as f:
        l = f.readlines()
    nl = l[18:]                      #remove license and preamble
    ni = [x[:-1] for x in nl]        #remove \n
    ni2 = [re.sub(r'\([^\)]*\)', '', x) for x in ni] #remove everything in round brackets
    ni3 = [" ".join(x.split()) for x in ni2 if not bool(re.search("\.{3}", x))] #remove whitespaces and halfstring
    ls = [x.split(';') for x in ni3] #create list of lists
    hl = []
    for e in ls:
        hl2 = []
        for x in e:
            hl2.append("".join(x.rstrip().lstrip())) #remove unnecessary whitespaces
        hl.append(hl2)
    fl = []
    for e in hl:
        fl.append(e[:n])             #take only first n synonyms, default 2
    return fl

@click.command()
@click.option('--fullpath', default='OpenThesaurus-Textversion/openthesaurus.txt', help='Full path to thesaurus file as txt of OpenThesaurus. Defaults to "OpenThesaurus-Textversion/openthesaurus.txt".')
@click.option('--filename', default='synonyms.csv', help='Full path to or filename of csv file to contain resulting list. Defaults to "synonyms.csv".')
@click.option('--n', default=2, help='How many synonyms each to include in list, defaults to two.')
def main(fullpath, filename, n):
    """
    Run script to generate list of n, default=2, synonyms each from OpenThesaurus. Save result as csv file.
    """
    lines = read_in_thesaurus(fullpath, n)             #Liest den OpenThesaurus ein und generiert Synonymenliste.

    with open(filename, "w", newline="") as f:         #write 43463 synonym pairs to file, Speichert Synonymenliste für spätere Verwendung.
        writer = csv.writer(f)
        writer.writerows(lines)

if __name__ == "__main__":

    main()
