#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import regex as re
import json
from typing import Dict, List
import click

def multiple_replace(d:Dict[str, str], text:str) -> str: #von https://stackoverflow.com/questions/15175142/how-can-i-do-multiple-substitutions-using-regex
  # Create a regular expression  from the dictionary keys
  regex = re.compile("(%s)" % "|".join(map(re.escape, d.keys())))
  # For each match, look-up corresponding value in dictionary
  return regex.sub(lambda mo: d[mo.string[mo.start():mo.end()]], text)

def clean_celex(l:List[str], d:Dict[str, str]) -> List[str]:
    """
    Produziert aus Liste von Strings eine Liste von Strings, in der newline-characters entfernt wurden und einzelne Buchstaben nach einem Dictionary ersetzt wurden.

    :param liste: Liste von Strings, die als Ausgangspunkt dient
    :param d: Dictionary, das die nötigen Buchstabenerseztungen enthält
    """
    ni = [x[:-1] for x in l]                                                  #remove \n
    lf = [multiple_replace(d, x) for x in ni]                                 #make replacements
    res = [x for x in lf if not bool(re.search(r"[^a-zA-ZäÄöÖüÜßé\\\n]", x))]
    return list(filter(None, res))                                            #return list without empty strings

def create_lemform_dict(liste:List[str]) -> Dict[str, str]:
    """
    Erzeugt Dictionary, das Lemmata zu den zugehörigen Wortformen mappt.

    :param liste: Liste von Strings der Form <Wortform>//<Lemma>
    """
    di = {}
    for e in liste:
        try:
            f,l = e.split("\\")
        except ValueError:
            continue
        if l not in di.keys():
            di[l] = []
            di[l].append(f)
        else:
            di[l].append(f)
    return di

def create_formlem_dict(di:Dict[str, str]) -> Dict[str, str]:
    """
    Erzeugt Dictionary, das Wortformen zu den zugehörigen Lemmata mappt.

    :param di: Dictionary, das Lemmata zu Wortformen mappt
    """
    f = {}
    for e in di.keys():
        for x in di[e]:
            if x not in f.keys():
                f[x]=e
            else:
                f[x]=e
    return f

@click.command()
@click.option('--fullpath', default='CWLbk/CELEX.Wordformen+Lemmata.bk.txt', help='Full path to or filename of txt file containing CELEX-wordforms and lemmata. Defaults to "CWLbk/CELEX.Wordformen+Lemmata.bk.txt".')
@click.option('--celexcleanfile', default='CELEXclean.json', help='Full path to or filename of txt file to contain cleaned CELEX-wordforms and lemmata. Defaults to "CELEXclean.json".')
@click.option('--usecleanedcelex/--no-cleaned-celex', default=False, help='Whether or not to load cleaned CELEX-data from file. Defaults to not doing so.')
@click.option('--cleanedcelexfile', default='CELEXclean.json', help='Full path to or name of json file containing cleaned CELEX-data. Defaults to "CELEXclean.json".')
@click.option('--lemmaformfile', default='LemmaForm.json', help='Full path to or name of json file to contain lemmata to wordforms dictionary. Defaults to "LemmaForm.json".')
@click.option('--formlemmafile', default='FormLemma.json', help='Full path to or name of json file to contain wordforms to lemmata dictionary. Defaults to "FormLemma.json".')
def main(fullpath, celexcleanfile, usecleanedcelex, cleanedcelexfile, lemmaformfile, formlemmafile):
    """
    Run script to generate LemmaForm and FormLemma dictionarys for later use from CELEX files.
    """
    if usecleanedcelex:
        with open(cleanedcelexfile) as f:     #Liest bereinigte CELEX-Wortformen-Lemmata-Datei ein. Nur sinnvoll, wenn eine solche Datei schon vorliegt.
            lf = json.load(f)
    else:
        with open(fullpath) as f:             #Liest die CELEX-Datei zeilenweise ein.
            l = f.readlines()
        d = {'"a' : "ä", '"A' : "Ä", '"u' : "ü", '"U' : "Ü", '"o' : "ö", '"O' : "Ö", '$' : "ß", '#e' : "é"}   #Dictionary mit den nötigen Ersetztungen von Buchstaben.
        lf = clean_celex(l, d)                #Bereinigt die CELEX-Datei.
        with open(celexcleanfile, "w") as f:  #Speichert bereinigte CELEX-Wortformen-Lemmata-Datei für spätere Verwendung.
            json.dump(lf, f)

    lfd = create_lemform_dict(lf)             #Erzeugt Lemma-Wortformen-Dictionary.

    fld = create_formlem_dict(lfd)            #Erzeugt Wortform-Lemma-Dictionary.

    with open(lemmaformfile, "w") as f:       #save dict in file
        json.dump(lfd, f)

    with open(formlemmafile, "w") as f:       #save dict in file
        json.dump(fld, f)


if __name__ == "__main__":
    
    main()
