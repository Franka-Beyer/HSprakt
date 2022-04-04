#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import os
import csv
from typing import List, Dict
import click


def find_relation(n:str, liste:List[str]) -> List[List[str]]:
    """
    Sucht in Liste von Zeilen, die Relationen beschreiben, nach allen, die die Realtion n beinhalten.
    
    Gibt Liste von gesplitteten Zeilen zurück.
    
    :param n: Name der zu suchenden Relation
    :param liste: Liste von Strings, die Zeilen in einer Relationsdatei sind
    """
    res = []
    for line in liste:
        if n in line:
            res.append(line.split())
    return res

def make_dictionary(liste:List[List[str]]) -> Dict[str, str]:
    """
    Erzeugt aus Liste gesplitteter Relationen ein Dictionary, das diese Relationen in beiden Richtungen enthält.
    
    :param liste: Liste gesplitteter Strings, die eine Relation abbilden
    """
    antonyms = {}
    for e in liste:
        if e[2] not in antonyms.keys():
            antonyms[e[2].split('"')[1]]=e[3].split('"')[1]
        if e[3] not in antonyms.keys():
            antonyms[e[3].split('"')[1]]=e[2].split('"')[1]
    return antonyms

def open_all_normal_files(path:str) -> List[List[str]]:
    """
    Öffent alle Dateien im angegebenen Verzeichnis, die GermaNet-Wortlisten enthalten.

    Produziert Liste von Listen von Zeilen.

    :param path: Pfad zum Verzeichnis, in dem die GermaNet-Wortlisten nach Wortarten liegen
    """    
    files = os.listdir(path)
    ml = []
    for file in files:
        if os.path.isfile(os.path.join(path, file)):
            if file.startswith("adj") or file.startswith("nomen") or file.startswith("verben"):
                with open(os.path.join(path, file),'r') as f:
                    nhl = f.readlines()
                    ml.append(nhl)
    return ml

def find_word_ids(all_lines:List[List[str]]) -> Dict[str, str]:
    """
    Produziert Dictionary, das GermaNet-IDs zu den einzelnen Wörtern mappt.

    :param all_lines: Liste von Listen von Wortlistenzeilen
    """
    #make list of relevant lines
    m = []
    for file in all_lines:
        for line in file:
            if line.startswith("<lexUnit"):
                m.append(line)
            if line.startswith('<orthForm'):
                m.append(line)
    #make dict mapping numbers to relevant lines
    n2l = {}
    for e,im in enumerate(m):
        if e not in n2l.keys():
            n2l[e]=im
    #make final dict of ids to words
    i2w = {}
    for e in n2l.keys():
        if "id=" in n2l[e]:
            ident = n2l[e].split('"')[1]
            if ident not in i2w.keys():
                i2w[ident]=n2l[e+1][10:-12]
    return i2w

def transform_to_words(antonymsdict:Dict, i2w:Dict) -> List[List[str]]:
    """
    Erzeugt aus Dictionary, das Relationen darstellt, Liste von Listen von Wortpaaren, die in dieser Relation zueinander stehen.

    :param antonymsdict: Dictionary, das Relationen darstellt; hier: Antonyme
    :param i2w: Dictionary, das GermaNet-IDs zu Wörtern mappt
    """
    asse = []
    for e in antonymsdict.keys():
        l = []
        l.append(i2w[e])
        l.append(i2w[antonymsdict[e]])
        asse.append(l)
    return asse

def shorten_list(ants:List[List[str]]) -> List[List[str]]:#leider nicht ganz korrekt, da len(ant)/2=1789.5
    """
    Erzeugt Liste von Listen von Antonymen, bei der jedes zweite Wortpaar entfernt wurde. Liefert Antonymenliste ohne Doppelungen.

    :param ants: Liste von Listen von Antonymenpaaren
    """
    s = []
    for e, l in enumerate(ants):
        if e%2==0:
            s.append(l)
    return s


@click.command()
@click.option('--fullpath', default='GN_V140/GN_V140_XML/gn_relations.xml', help='Full path to relations file of GermaNet. Defaults to "GN_V140/GN_V140_XML/gn_relations.xml".')
@click.option('--path', default='GN_V140/GN_V140_XML/', help='Full path to directory containing GermaNet xml files. Defaults to "GN_V140/GN_V140_XML/".')
@click.option('--relation', default='antonym', help='Relation to be extracted as named by GermaNet. Defaults to "antonym".')
@click.option('--filenamelong', default='antonyms_long.csv', help='Full path to or filename of csv file containing long resulting list. Defaults to "antonyms_long.csv".')
@click.option('--filenameshort', default='antonyms_short.csv', help='Full path to or filename of csv file containing short resulting list. Defaults to "antonyms_short.csv".')
def main(fullpath, path, relation, filenamelong, filenameshort):
    """
    Run script to generate long (containing relation in both directions) and short (containing relation in one direction) lists of antonyms from GermaNet files. Save results as csv files.
    """
    
    with open(fullpath) as f:                                   #Liest die Relationsdatei der zur Verfügung stehenden GermaNet Version zeilenweise ein.
        l = f.readlines()

    hl = find_relation(relation, l)                             #Sucht sämtliche Zeilen heraus, die Antonyme beschreiben.

    anton = make_dictionary(hl)                                 #Erstellt aus diesen Zeilen ein Dictionary, das die Relationen abbildet.

    all_lines = open_all_normal_files(path)                     #Liest alle GermaNet-Wortlisten zeilenweise ein.

    i2w = find_word_ids(all_lines)                              #Erstellt Dictionary, das GermaNet-IDs den passenden Wörtern zuordnet.

    ant = transform_to_words(anton, i2w)                        #Erzeugt Liste von Listen von Antonymen. (Je a zu b und b zu a.)

    short = shorten_list(ant)                                   #Erzeugt verkürzte Antonymenliste. (Nur je a zu b.)

    with open(filenamelong, "w", newline="") as f:              #Speichert Antonymenliste für spätere Verwendung als csv-Datei.
        writer = csv.writer(f)
        writer.writerows(ant)

    with open(filenameshort, "w", newline="") as f:             #Speichert verkürzte Antonymenliste als csv-Datei.
        writer = csv.writer(f)
        writer.writerows(short)


if __name__ == "__main__":

    main()
