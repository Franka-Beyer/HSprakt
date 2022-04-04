#!/usr/bin/env python3
# -*- coding: utf-8 -*-
#
# Copyright (C) 2022 franka.beyer@fau.de

import json
import pickle
import regex as re
from collections import Counter
import csv
from typing import List, Dict, Any, Tuple
import click
import numpy
import math

def read_resultnames(names:List[str], la:List[str]) -> Tuple[List[str], Dict[str, str]]:
    """
    Liest aus mehreren Dateien eine Liste der Dateien ein, die Ergebnisse von CQP-Anfragen enthalten. Erstellt ein Wortpaar-Label/Relation-Dictionary.

    :param names: Liste von Strings; Pfade zu bzw. Namen der Dateien, die erfolgreiche CQP-Abfragen auflisten
    :param la: Liste von Labeln/Relationen als Strings; parallel zu :names:; zur Klassifizierung der Wortpaare
    """
    res = []
    labelsdict = {}
    c = 0
    for name in names:
        with open(name, "rb") as f:
            new = pickle.load(f)
        for pair in new:
            labelsdict[pair[:-10]] = la[c]
        c += 1
        res.extend(new)
    return res, labelsdict

def read_in_cqp_result(file:str) -> Any:
    """
    Liest eine Datei, die die Ergebnisse einer CQP-Anfrage enthält zeilenweise ein, bereinigt sie und gibt sie zusammen mit einer Indikatiorvariable als Liste von Strings zurück.

    :param file: Pfad zu bzw. Name einer Datei, die CQP-Ergebinisse enthält, als String
    """
    l = None
    try:
        with open(file) as f:
            l = f.readlines()
    except FileNotFoundError:
        print("Keine Ergebnisse für " + file[:-9])
    if l:
        nonum = [x.split(":")[1] for x in l]              #remove numbers and :
        nosym = [re.sub(r"[<>\n]", "", x) for x in nonum] #remove brackets and newlines
        return True,[" ".join(x.split()) for x in nosym]  #remove unnecessary whitespaces in front
    else:
        return None,"Keine Ergebnisse in CQP gefunden."


def make_patterndict(resultnames:List[str]) -> Dict[str, List[str]]:
    """
    Nimmt Liste von Strings bzw. Dateien, die CQP-Ergebnisse enthalten, entgegen. Lässt diese einlesen und produziert ein Wortpaar-CQP-Ergebnisse-Dictionary.

    :param resultnames: Liste von Strings bzw. Dateien, die CQP-Ergebnisse enthalten
    """
    patterndict = {}
    for result in resultnames:
        info, res = read_in_cqp_result(result)
        if info:
            patterndict[result[:-10]] = res
    return patterndict

def celex_lemmatize(liste:List[str], dictionary:Dict[str, str]) -> List[str]:
    """
    Nimmt Liste von einzelnen CQP-Ergebnissen (je eine Zeile pro Listenelement) an. Lemmatisiert diese zeilenwiese mit Hilfe eines auf CELEX basierenden Wortform-Lemma-Dictionary und gibt die resultierende Liste zurück.

    :param liste: zeilenweise Liste von CQP-Ergebnissen (bzw. je einem Ergebnis)
    :param dictionary: Wortform-Lemma-Dictionary, hier basierend auf CELEX
    """
    hl = []
    for e in liste:
        hl2 = []
        for x in e.split():
            if x in dictionary.keys():
                x = dictionary[x]
            hl2.append(x)
        hl.append(" ".join(hl2))
    return hl

def x_y_out(musterliste:List[str], wordliste:List[str]) -> List[str]:
    """
    Nimmt Liste lemmatisierter CQP-Ergebniszeilen und zugehöriges Wortpaar als Liste an. Ersetzt die beiden Wörter des gesuchten Wortpaares durch X bzw. Y.

    :param musterliste: Liste lemmatisierter CQP-Ergebniszeilen
    :param wordliste: zugehöriges Wortpaar als Liste
    """
    hl = []
    for e in musterliste:
        hl2 = []
        for w in e.split():
            if w == wordliste[0]:
                w = 'X'
            if w == wordliste[1]:
                w = 'Y'
            hl2.append(w)
        hl.append(" ".join(hl2))
    return hl

# remain    data
#  a X b    ()
#  X b      "*"
#  X b      "*"
#  b        "*" X
#           "*" X "*"
#           "*" X b
#  X b      a
#  b        a X
#           a X "*"
#           a X b
#  
def vary(remain:List[str], data:List[str]) -> None:
    """
    Generiert aus einer Liste sämtliche möglichen Patterns, indem die einzelnen Elemente der Reihe nach durch * ersetzt werden.
    Die Strings 'X' und 'Y' bleiben dabei erhalten.
    
    :param remain: Liste mit noch zu verarbeitenden Elementen
    :param data: Anfang des Resultats
    """
    if not remain:
        # keine noch zu verarbeitenden Elemente: fertig
        yield data
        return
    x,*remain = remain  # erstes Element isolieren
    if x not in ("X", "Y"):
        yield from vary(remain, data+("*",)) # Rest mit '*' statt des Elements generieren
    yield from vary(remain, data+(x,)) # Rest mit diesem konkreten Element generieren

def patternize(musterliste:List[str]) -> List[str]:
    """
    Produziert für eine Liste von Mustern sämtliche möglichen Patterns, indem aus jedem Muster via 'vary()' eine Liste von Patterns generiert wird.

    :param musterliste: Liste lemmatisierter CQP-Ergebniszeilen, in denen das Wortpaar durch X und Y ersetzt wurde
    """
    res = []
    for line in musterliste:
        for pattern in vary(line.split(" "),()):
            res.append(" ".join(pattern))
    return res

def patternize_and_master_list(patterndict:Dict[str, List[str]], formlemma:Dict[str, str]) -> Tuple[Dict[str, Any], List[str]]:
    """
    Nimmt Wortpaar-CQP-Ergebnisse-Dictionary und Wortform-Lemma-Dictionary entgegen. Lässt CQP-Ergebnisse lemmatisieren, das Wortpaar durch X und Y ersetzen, sämtliche möglichen Patterns für die einzelenen Wortpaare erstellen und diese zählen. Gibt Wortpaar-Counter(Patterns)-Dictionary und Liste aller produzierten Patterns zurück.

    :param patterndict: Wortpaar-CQP-Ergebnisse-Dictionary
    :param formlemma: Wortform-Lemma-Dictionary
    """
    masterpatternlist = []
    for pair in patterndict.keys():
        patterndict[pair] = celex_lemmatize(patterndict[pair], formlemma)
        patterndict[pair] = x_y_out(patterndict[pair], pair.split(":"))
        p = patternize(patterndict[pair])
        patterndict[pair] = Counter(p)
        masterpatternlist.extend(p)
    return patterndict, [x for x in masterpatternlist if x!='']

def choose_patterns(k:int, N:int, patternlist:List[str]) -> List[str]:
    """
    Gibt Liste der k mal N häufigsten Strings in einer Liste von Strings zurück.

    :param k: Faktor zur Bestimmung der Anzahl der Features, die in den Featurevektoren enthalten werden seien; Vorlage-Paper legt k = 20 nahe
    :param N: zweiter Faktor zur Limitierung der Features, Anzahl der Input-Wortpaare und damit Anzahl der Featurevektoren
    :param patternlist: Liste aller produzierten Patterns als Strings
    """
    return [word for word, word_count in Counter(patternlist).most_common(k*N)]

def generate_vectordict(patternizeddict:Dict[str, Any], chosenpatterns:List[str]) -> Dict[str, List[int]]:
    """
    Nimmt Wortpaar-Patterns-Dictionary und Liste der als Features gewählten Patterns entgegen. Produziert Wortpaar-Featurevektor-Dictionary.

    :param patternizeddict: Wortpaar-Patterns-Dictionary
    :param chosenpatterns: Liste der als Features gewählten Patterns
    """
    vektordict = {}
    for element in patternizeddict.keys():
        vektor = [0] * len(chosenpatterns)
        for idx, val in enumerate(chosenpatterns):
            if val in patternizeddict[element].keys():
                #vektor[idx] = patternizeddict[element][val]
                vektor[idx] = math.log(patternizeddict[element][val] + 1)
        vektordict[element] = vektor
    return vektordict

def normalize_vectors(vd:Dict[str, List[int]]) -> Dict[str, List[float]]: #nach https://stackoverflow.com/questions/23846113/how-to-normalize-a-vector-in-python
    """
    Normalisiert alle Vektoren in einem key-vector-Dictionary einzeln. Gibt Dictionary mit normalisierten Vektoren als Values zurück.

    :param vd: Key-Vektor-Dictionary
    """
    numpy.seterr(all='raise')
    res = {}
    for key in vd.keys():
        v = vd[key]
        v_dot = numpy.dot(v, v)
        v_scalar = math.sqrt(v_dot)
        try:
            n = numpy.asarray(v) / v_scalar
            no =  n.tolist()
            res[key] = no
        except FloatingPointError:
            res[key] = [0] * len(v)
    return res

def balance_lines(lines:List[List[str]], k:int, vd:Dict[str, List[int]]) -> List[List[str]]:
    """
    Hilfsfunktion für write_weka_data(). Produziert aus Liste von Listen von Strings der Form 'Wortpaar, Label, Featurevektor' eine Liste, in der die Anzahl der Listen von Strings, die das gleiche Label enthalten, der der mit dem seltensten Label entspricht. Garantiert so, dass alle Label gleich oft vorkommen.

    :param lines: Liste von Listen der Form 'Wortpaar, Label, Featurevektor', wie sie in write_weka_data() vorkommen
    :param k: einer der beiden Faktoren für die Länge der Featurevektoren
    :param vd: Wortpaar-Featurevektor-Dictionary mit absoluten Werten, nicht normalisiert
    """
    count = {}
    lin = {}
    for el in lines[1:]:
        if el[1] not in count.keys():
            count[el[1]] = 1
            lin[el[1]] = []
            lin[el[1]].append(el)
        else:
            count[el[1]] += 1
            lin[el[1]].append(el)
        h = count[el[1]]
    for n in count.keys():
        if count[n] <= h:
            h = count[n]
    v = 20 * h * len(count) + 2
    res = []
    res.append(lines[0][:v])
    for k in lin.keys():
        co = 0
        for line in lin[k]:
            if co < h:
                hd = {line[0] : vd[line[0]][:v-2]}
                hl = [line[0], line[1]]
                for e in normalize_vectors(hd)[line[0]]:
                    hl.append(e)
                res.append(hl)
            co += 1
    return res

def write_weka_data(chosenPatterns:List[str], vectordict:Dict[str, List[float]], labelsdict:Dict[str, str], filename:str, balance:bool, k:int, vd:Dict[str, List[int]]) -> None:
    """
    Produziert csv-Datei mit den beschrifteten Featurevektoren als Zeilen, die mit weka weiterverarbeitet werden kann. Enthält je Zeile das Wortpaar, das Label bzw. die Relation der beiden Wörter zueinander sowie den Featurevektor. Ein Header ist ebenfalls mit inbegriffen.

    :param chosenPatterns: Liste der als Features gewählten Patterns
    :param vectordict: Wortpaar-Featurevektor-Dictionary
    :param labelsdict: Wortpaar-Label/Relation-Dictionary
    :param filename: Pfad zu bzw. Name der csv-Datei, die die entstandene Tabelle enthalten soll
    :param balance: ob die Anzahl der Wortpaare je Label gleich sein soll, oder nicht
    :param k: einer der beiden Faktoren für die Länge der Featurevektoren
    :param vd: Wortpaar-Featurevektor-Dictionary mit absoluten Werten, nicht normalisiert
    """
    head = ["Wortpaar", "Label"]
    head.extend(chosenPatterns)
    lines = []
    lines.append(head)
    for pair in vectordict:
        line = []
        line.append(pair)
        line.append(labelsdict[pair])
        line.extend(vectordict[pair])
        lines.append(line)
    if balance:
        lines = balance_lines(lines, k, vd)
    with open(filename, "w", newline="") as f:
        writer = csv.writer(f, delimiter='\t')
        writer.writerows(lines)


@click.command()
@click.option('--formlemmaname', default='FormLemma.json', help='Name of file containing wordform-lemma-dictionary. Defaults to "FormLemma.json".')
@click.option('--resultfiles', '-f', multiple=True, default=["actual_results_antonyms_long.pckl", "actual_results_synonyms.pckl", "actual_results_nonyms.pckl", "actual_results_200-400_antonyms_long.pckl", "actual_results_200-400_nonyms.pckl", "actual_results_200-400_synonyms.pckl", "actual_results_400-1000_synonyms.pckl", "actual_results_1010-1020_antonyms_long.pckl", "actual_results_1010-1020_synonyms.pckl", "actual_results_1020-1030_antonyms_long.pckl", "actual_results_1020-1030_synonyms.pckl", "actual_results_1030-1040_synonyms.pckl"], help='Name files from which to take data to be preprocessed. Has to be parallel to labels.')
@click.option('--labels', '-l', multiple=True, default=["antonyms", "synonyms", "nonyms", "antonyms", "nonyms", "synonyms", "synonyms", "antonyms", "synonyms", "antonyms", "synonyms", "synonyms"], help='Lables or relations for sourcefiles used. Has to be parallel to files named as resultfiles.')
@click.option('--k', default=20, help='One of the factors determining the number of features of the vectors; should be 20 according to paper. Defaults to 20.')
@click.option('--patternfile', default='chosenPatterns.pckl', help='Full path to or name of file to contain the patterns chosen as features. Defaults to "chosenPatterns.pckl".')
@click.option('--normalize/--not-normalized', default=True, help='Whether to normalize the feature vectors or not. Defaults to yes. Balanced data is always normalized.')
@click.option('--vectorfile', default='VektorDict.json', help='Full path to or name of file to contain the wordpair-vector-dictionary. Defaults to "VektorDict.json".')
@click.option('--balance/--unbalanced', default=True, help='Whether to ensure balance of labels in data or not. Defaults to yes. Will always normalize vectors if yes.')
@click.option('--datafile', default='Data.csv', help='Full path to or name of file to contain data prepared for weka. Defaults to "Data.csv".')
def main(formlemmaname, resultfiles, labels, k, patternfile, normalize, vectorfile, balance, datafile):
    """
    Run script to finish preprocessing, patternize data and generate vectors. Save results in csv file for later usage in weka.
    """
    rnames, labelsdict = read_resultnames(resultfiles, labels)    #Liest CQP-Ergebnisse ein und erstellt Wortpaar-Label-Dictionary.

    pd = make_patterndict(rnames)                                 #Erstellt Wortpaar-CQP-Ergebnisse-Dictionary.

    with open(formlemmaname) as f:                                #Liest Wortform-Lemma-Dictionary ein.
        formlemma = json.load(f)

    if formlemmaname=='FormLemma.txt':
        newformlemma = {}
        for key in formlemma.keys():
            newformlemma[key] = formlemma[key][:-1]
    else:
        newformlemma=formlemma   

    ptd, ml = patternize_and_master_list(pd, newformlemma)        #Erstellt Wortform-Patterns-Dictionary und Liste aller Patterns.

    n = len(rnames)                                               #Bestimmt Variable n (bzw. N im Paper) aus Anzahl der Wortpaare.

    cho = choose_patterns(k, n, ml)                               #Wählt Features aus Patternliste aus.

    with open(patternfile, "wb") as f:                            #Speichert Feature-Patterns in Datei.
        pickle.dump(cho, f)

    vd = generate_vectordict(ptd, cho)                            #Erstellt Wortpaar-Featurevektor-Dictionary.

    if normalize:                                                 #Normalisiert Wortpaar-Featurevektor-Dictionary, wenn erwünscht.
        vd = normalize_vectors(vd)

    with open(vectorfile, "w") as f:                              #Speichert Wortpaar-Featurevektor-Dictionary in Datei.
        json.dump(vd, f)

    write_weka_data(cho, vd, labelsdict, datafile, balance, k, vd)#Schreibt Vektordatei für Weiterverarbeitung mit Weka.


if __name__ == "__main__":

    main()

 
