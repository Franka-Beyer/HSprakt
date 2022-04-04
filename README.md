# HSprakt Projekt Synonyme, Antonyme und Machine Learning

A set of python scripts to extract antonym and synonym lists from GermaNet and
OpenThesaurus, generate a list of wordpairs neither antonyms nor synonyms, 
extract word-lemma dictionaries from CELEX, generate all morphological forms 
for a wordpair, run a CQP search for each wordpair, generate a feature vector
for each wordpair and write the vectors to a csv file for usage in Weka.

## Requirements

Requires python 3.7.7 as well as additional packages click, collections, csv, json, math,
numpy, os, pickle, random, regex, subprocess, threading and typing.

Requires IMS Open Corpus Workbench (CWP) 3.4.22 and Weka 3.8.6

For more details, see Projektbericht, 2.1 Installation der Tools.

## Usage

Create working directory. Ensure running cqp from working directory is possible.
For ease of management consider adding raw data files to directory.

To see options offered by scripts type:
```bash
./<scriptname> --help
```

####Preparation

```bash
./MakeAntonymsFiles.py #generates files 'antonyms_long.csv' and 'antonyms_short.csv' from GN_V140

./MakeSynonymFile.py #generates 'synonyms.csv' from OpenThesaurus-Textversion

./MakeNonyms.py #generates 'nonyms.csv' from 'antonyms_long.csv' and 'synonyms.csv'

./MakeCELEXDictFiles.py #generates 'LemmaForm.json' and 'FormLemma.json' from CWLbk
```
These scripts have to be run just once before proceeding.

###Data Preprocessing

```bash
./PreprocessingCQP.py #searches for first 200 wordpairs from 'antonyms_long.csv', 'synonyms.csv' and 'nonyms.csv' in corpus, keeps results in files of form 'actual_results_0-200_<filename>.pckl' and writes blacklists of those not found in files named 'actual_blacklisted_0-200_<filename>.csv'

./PreprocessingCQP.py --beginrange=200 --endrange=1000 -f antonyms_long.csv -f synonyms.csv --corpusname=TAZ; #searches for wordpairs numbered 200 to 1000 from files named in CQP corpus named TAZ
```

This script is to be run repeatedly, until a sufficient amount of data
has been generated. The blacklist files and the ranges included in the filenames
can be used to keep track of the results of past searches. All files generated
by this script have to be kept to avoid having to repeat searches in the corpus.

```bash
./MakeVectors.py #generates 'Data.csv', a balanced data set prepared for weka, from resultfiles generated during the project, as well as 'chosenPatterns.pckl' and 'VektorDict.json', which are currently not used

./MakeVectors.py -f actual_results_antonyms.csv -f actual_results_synonyms.csv #generates 'Data.csv' from files named instead

./MakeVectors.py --datafile=DataWeka.csv #generates 'DataWeka.csv', saves results in file as specified
```
This final script creates a --datafile containing the wordpairs, their labels
and their feature vectors. The result is a csv file using tabulators
as delimters. The two other files produced are currently not in use, but might
find an application sometime later.

To avoid mistakes when inputting the --resultfiles with the option -f
and the --lables with -l, as these have to be parallel, it might be necessary
to change the defaults in the click.options in the script itself.
Especially after repeated searches of small batches of wordpairs
in the previous step, these lists might become rather long and unwieldy.

This script has to be run just once, the other two examples here serve to show
the usage of options.

###Working with data in Weka

To start Weka:
```bash
/weka-3-8-6$ java -jar weka.jar & #start weka as additional active window
```
In the Weka GUI Chooser open the Explorer.

In the Explorer choose Preprocess and Open file.... Change the filetype to csv,
choose datafile and invoke the options dialog. Click 'open' and change
fieldSeperator in weka.gui.GenericObjectEditor to TAB as described in More.

Proceed to Classify in the Explorer. Choose a classifier and view or change
its options by left clicking its name. Disable normalization of data 
if data has already been normalized in Preprocessing as is default.

For further information on weka see: https://waikato.github.io/weka-wiki/documentation/

###Using different data

To use different lists of wordpairs, create csv files of two words of chosen
relation per line, seperated by ','. See options of scripts to use these instead.
