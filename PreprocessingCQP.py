#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import csv
import random
import json
import subprocess
import pickle
import regex as re
from collections import Counter
import os
import threading
import click
from typing import List, Dict, Tuple, Any

def celex_generate(wordlist:List[List[str]], lemform:Dict[str, str]) -> Dict[str, List[List[str]]]:
    """
    Nimmt Liste von Listen von Wortpaaren als Strings entgegen. Prodziert Dictionary mit Wortpaar als Key und Liste von Listen von Wortpaaren, die sämtliche Kombinationen der morphologischen Formen der Wortpaare abdecken.

    :param wordlist: Liste von Listen von Wortpaaren als Strings
    :param lemform: Dictionary, das Lemmata zu den zugehörigen Wortformen mappt
    """
    d = {}
    for e in wordlist:
        if e[0] in lemform:
            l1 = lemform[e[0]]
        else:
            l1 = [e[0]]
        if e[1] in lemform:
            l2 = lemform[e[1]]
        else:
            l2 = [e[1]]
        h = []
        for x in l1:
            for y in l2:
                h2 = []
                h2.append(x)
                h2.append(y)
                h.append(h2)
        d[":".join(e)] = h
    return d

def write_cqp_scripts(forms:Dict[str, List[List[str]]], corpusname:str) -> Tuple[List[str], List[str]]: 
    """
    Nimmt Dictionary mit Wortpaaren als Keys und Listen von Listen der möglichen Kombinationen der morphologischen Formen entgegen. Schreibt für jedes Wortpaar ein CQP-Script, das der Reihe nach alle diese Kombinationen abfragt und die Ergebnisse in einer Datei je Wortpaar sammelt. Gibt die Namen der produzierten Scripte als Liste und die Namen der Ergebnisdateien als Liste zurück.

    :param forms: Dictionary mit Wortpaaren als Keys und Listen von Listen der möglichen Kombinationen der morphologischen Formen als Values
    :param corpusname: Name bzw. Aktivierung des CQP-Korpus, das verwendet werden soll
    """
    names = []
    files = []
    for e in forms.keys():
        lines = [corpusname, 'set Context 0;']
        res = str(e)
        for p in forms[e]:
            s1 = 'rs  = []? "' + p[0] + '" []{0,3} "' + p[1] + '" [];' #hier abweichend vom Vorlagepaper mit erzwungenem Wort am Schluss (vgl. Bericht)
            s2 = 'cat rs >> "' + res + ':.txt.data";'
            lines.append(s1)
            lines.append(s2)
        name = res + '.script'
        with open(name, 'w') as f:
            for item in lines:
                f.write("%s\n" % item)
        names.append(name)
        files.append(res + ':.txt.data')
    return names, files

NPROCS=8                                          #Anzahl der Kerne, die für Multiprocessing zur Verfügung stehen
def run_cqp_queries(nameslist:List[str]) -> None:
    """
    Führt mit Verwendung von threading und subprocess sämtliche CQP-Scripte aus einer Liste aus.

    :param nameslist: Liste von Namen von CQP-Scripten
    """
    sem = threading.Semaphore(NPROCS)
    t = []
    def proc(s):
        subprocess.call(s)
        sem.release()
    for e in nameslist:
        sem.acquire()
        s = ['cqp','-f', e]
        tt = threading.Thread(target=proc,args=(s,))
        t.append(tt)
        tt.start()
    for tt in t:
        tt.join()

def read_in_cqp_result_extra(file:str) -> Any:
    """
    Prüft, ob eine Datei, die die Ergebnisse einer CQP-Abfrage enthält, tatsächlich Ergebnisse enthält, oder leer ist.

    :param file: Name der zu prüfenden CQP-Ergebinisdatei
    """
    try:
        s = os.stat(file)
    except FileNotFoundError:
        print("Keine Ergebnisse für " + file[:-9])
        return None
    else:
        return s.st_size > 0

def prepare_cqp(chunk:List[List[str]], lemmaform:Dict[str, str], corpusname:str) -> Tuple[List[str], List[List[str]]]:
    """
    Nimmt Liste von Wortpaaren entgegen. Generiert mit Hilfe von CELEX alle bekannten morphologischen Varianten für jedes Paar. Schreibt die CQP-Scirpte für die einzelenen Paare. Führt diese Scripte aus. Ermittelt, für welche Wortpaare im Korpus Ergebnisse gefunden wurden. Löscht alle entstandene leere Ergebnisdateien. Gibt eine Liste der Wortpaare, die nicht gefunden wurden, und eine Liste der Namen der Ergebnisdateien mit Inhalt zurück.

    :param chunk: Liste von Wortpaaren, je als Liste
    :param lemmaform: Lemma-Wortformen-Dictionary
    :param corpusname: Name bzw. Aktivierung des CQP-Korpus, das verwendet werden soll
    """
    results = []
    blacklisted = []
    forms = celex_generate(chunk, lemmaform)
    snames, rnames = write_cqp_scripts(forms, corpusname)
    run_cqp_queries(snames)
    for name in rnames:
        indicator = read_in_cqp_result_extra(name)
        if indicator:
            results.append(name)
        else:
            blacklisted.append(name[:-9].split(":")[:-1])
            os.remove(name)
    for sna in snames:
        os.remove(sna)
    return results, blacklisted



@click.command()
@click.option('--lemmaformname', default='LemmaForm.json', help='Name of file containing lemma-wordforms-dictionary. Defaults to "LemmaForm.json".')
@click.option('--files', '-f', multiple=True, default=['antonyms_long.csv','synonyms.csv', 'nonyms.csv'], help='Name files from which to take data to be preprocessed. Defaults to "antonyms_long.csv", "synonyms.csv" and "nonyms.csv".')
@click.option('--beginrange', default=0, help='Beginning of chunk to be preprocessed. Defaults to 0.')
@click.option('--endrange', default=200, help='End of chunk to be preprocessed. Defaults to 200.')
@click.option('--corpusname', default='EXAMPLE;', help='Name or activation phrase of CQP-corpus to be searched. Of form "<name>;" Defaults to "EXAMPLE;"')
def main(lemmaformname, files, beginrange, endrange, corpusname):
    """
    Run script to search for wordpairs in corpus and save results for later usage.
    """
    with open(lemmaformname) as f:                    #Öffnet Lemma-Wortformen-Dictionary.
        lemmaform = json.load(f)

    if lemmaformname=='LemmaForm.txt':
        newlemmaform = {}
        for k in lemmaform.keys():
            kn = k[:-1]
            newlemmaform[kn] = lemmaform[k]
    else:
        newlemmaform=lemmaform

    for file in files:

        with open(file, "r", newline="") as f:        #Liest Wortpaar-Datei zeilenweise ein.
            lines = [x for x in csv.reader(f)]
    
        chunk = lines[beginrange:endrange]            #Beschränkt Wortpaare auf gewünschten Abschnitt.

        results, blacklisted = prepare_cqp(chunk, newlemmaform, corpusname)  #Lässt Wortpaare mit CQP vorverarbeiten.

    
        with open("actual_results_" + str(beginrange) + "-" + str(endrange) + "_" + file[:-4] + ".pckl", "wb") as fp:
            pickle.dump(results, fp)
    
        with open("actual_blacklisted_" + str(beginrange) + "-" + str(endrange) + "_" + file, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerows(blacklisted)

if __name__ == "__main__":
    
    main()
