# News Category Classification
This repo contains a simple source code for text-classification based on TextCNN. Corpus is news category dataset in English. Most open sources are a bit difficult to study & make text-classification model for beginners. So, I hope that this repo can be a good solution for people who want to have their own text-classification model.

## Data
News category dataset contains around 200k news headlines from the year 2012 to 2018 obtained from HuffPost. You can download this dataset [here](https://www.kaggle.com/rmisra/news-category-dataset).

The dataset contains 202,372 records. Each json record contains following attributes:

- `category`: Category article belongs to
- `headline`: Headline of the article
- `authors`: Person authored the article
- `link`: Link to the post
- `short_description`: Short description of the article
- `date`: Date the article was published  

Below table shows that the first 5 lines from the dataset provided by [Kaggle](https://www.kaggle.com/).

<p align="left">
<img width="700" src="https://github.com/lyeoni/nlp-tutorial/blob/master/news-category-classifcation/images/data_sample.png">
</p>


## Usage
### 1. Preprocessing corpus
Just run preprocessing.sh. It runs tokenization_ko.py, fasttext in order.
```
$ ./preprocessing.sh
```
```
structure:
  preprocessing.sh
  └── tokenization_en.py
      └── remove_emoji.py
  └── fasttext
```
```
$ python tokenization_en.py -h
usage: tokenization_en.py [-h] -input INPUT -column COLUMN -output OUTPUT

optional arguments:
  -h, --help      show this help message and exit
  -input INPUT    data file name to use
  -column COLUMN  column name to use. headline or short_description
  -output OUTPUT  data file name to write
```
example usage:
```
python tokenization_en.py -input News_Category_Dataset_v2.json -column short_description -output news.tk.txt
```
You may also need to change the argument parameters in code. e.g. classify using the headline instead of short_description.

### 2. Make data loader
It returns train/test-set as well as embedding_matrix.
```
$ python data_loader.py -h
usage: data_loader.py [-h] [-corpus_tk CORPUS_TK]
                      [-trained_word_vector TRAINED_WORD_VECTOR]
                      [-label_corpus LABEL_CORPUS]
                      [-max_word_num MAX_WORD_NUM]
                      [-min_corpus_len MIN_CORPUS_LEN]
                      [-max_corpus_len MAX_CORPUS_LEN]

optional arguments:
  -h, --help            show this help message and exit
  -corpus_tk CORPUS_TK  Default=corpus.tk.txt
  -trained_word_vector TRAINED_WORD_VECTOR
                        Default=corpus.tk.vec.txt
  -label_corpus LABEL_CORPUS
                        Default=News_Category_Dataset_v2.json
  -max_word_num MAX_WORD_NUM
                        number of words to use. Default=50,000
  -min_corpus_len MIN_CORPUS_LEN
                        minimum value of each corpus length. Default=5
  -max_corpus_len MAX_CORPUS_LEN
                        maximum value of each corpus length. Default=50```
```
```
structure:
  data_loader.py
  └── read_word_pair.py
```
You may also need to change the argument parameters in code.

### 3. Training
```
$ python train.py -h
usage: train.py [-h] [-corpus_tk CORPUS_TK]
                [-trained_word_vector TRAINED_WORD_VECTOR]
                [-label_corpus LABEL_CORPUS] [-epoch EPOCH]
                [-batch_size BATCH_SIZE]

optional arguments:
  -h, --help            show this help message and exit
  -corpus_tk CORPUS_TK  Default=corpus.tk.txt
  -trained_word_vector TRAINED_WORD_VECTOR
                        Default=corpus.tk.vec.txt
  -label_corpus LABEL_CORPUS
                        Default=News_Category_Dataset_v2.json
  -epoch EPOCH          number of iteration to train model. Default=20
  -batch_size BATCH_SIZE
                        mini batch size for parallel inference. Default=64
```
```
structure:
  train.py
  └── data_loader.py
```
You may also need to change the argument parameters in code.
