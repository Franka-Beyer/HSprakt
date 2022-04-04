#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import csv
import random
from typing import List
import click

def read_csv_file(file:str) -> List[List[str]]:
    """
    Öffnet eine csv-Datei als Liste von Listen von Strings.

    :param file: vollständiger Pfad zur bzw. Name der zu öffnenden Datei
    """
    with open(file, "r", newline="") as f:
        l = [x for x in csv.reader(f)]
    return l

def find_new_combinations(filename1:str, filename2:str, seed:int, n:int) -> List[List[str]]:
    """
    Liest zwei csv-Dateien als Listen von Listen von Strings ein. Kombiniert diese beiden Listen zu einer. Generiert mit Hilfe von random.sample() Wortpaare, die nicht in der kombinierten Liste aus beiden Dateien vorkommen.

    :param filename1: vollständiger Pfad zur bzw. Name der ersten zu öffnenden csv-Datei
    :param filename2: vollständiger Pfad zur bzw. Name der zweiten zu öffnenden csv-Datei
    :param seed: seed, der für random gesetzt wird, um Reproduzierbarkeit zu gewährleisten
    :param n: gibt an, wie viele Wortpaare aus der produzierten Liste zurückgegeben werden sollen
    """
    pairs1 = read_csv_file(filename1)
    pairs2 = read_csv_file(filename2)
    for pair in pairs2:
        pairs1.append(pair)
    random.seed(seed)
    nonyms = []
    for line in pairs1:
        a, b = line
        l = random.sample(pairs1, 1)[0]
        x,y = l
        newline = [a, x]
        if newline not in pairs1:
            nonyms.append(newline)
    random.seed(seed)
    return random.sample(nonyms, n)

@click.command()
@click.option('--file1', default='antonyms_long.csv', help='Full path to or filename of csv file containing list of wordpairs. Defaults to "antonyms_long.csv".')
@click.option('--file2', default='synonyms.csv', help='Full path to or filename of csv file containing list of wordpairs. Defaults to "synonyms.csv".')
@click.option('--seed', default=3, help='Seed to be used by random module. Defaults to 3.')
@click.option('--n', default=40000, help='Lenght of resulting list of wordpairs. Defaults to 40000.')
@click.option('--resultname', default='nonyms.csv', help='Full path to or filename of csv file to contain resulting list. Defaults to "nonyms.csv".')
def main(file1, file2, seed, n, resultname):
    """
    Run script to generate list of wordpairs from two csv files containing lists of wordpairs that occur in neither. Save result as csv file.
    """
    nonyms = find_new_combinations(file1, file2, seed, n)  #Produziert aus zwei Dateien n Wortpaare, die in keiner vorkommen.

    with open(resultname, "w", newline="") as f:           #Speichert die neue Liste für spätere Verwendung als csv-Datei.
        writer = csv.writer(f)
        writer.writerows(nonyms)

if __name__ == "__main__":

    main()
