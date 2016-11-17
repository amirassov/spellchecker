from collections import defaultdict, Counter
import re
import numpy as np


class Trie:
    def __init__(self):
        self.word = None
        self.probability = None
        self.children = defaultdict(Trie)
        
    def insert(self, word, probability):
        node = self
        for letter in word:
            node = node.children[letter]
        node.word = word
        node.probability = probability
       
    
class LevenshteinAutomaton:
    """
    Automaton for calculate Levenshtein distance
    """
    def __init__(self, word, max_dist):
        self.word = word
        self.max_dist = max_dist

    def start(self):
        return range(len(self.word) + 1)

    def step(self, state, letter):
        new_state = [state[0] + 1]
        for i in range(len(state) - 1):
            insert_state = new_state[i] + 1
            replace_state = state[i] + (self.word[i] != letter)
            delete_state = state[i + 1] + 1
            new_state.append(min(insert_state, replace_state, delete_state))
        return new_state

    def is_match(self, state):
        return state[-1] <= self.max_dist

    def can_match(self, state):
        return min(state) <= self.max_dist
    
    
class WordSearcher:
    def __init__(self, trie, max_dist=1, alpha=0.1):
        """
        Args:
        trie (Trie): dictionary trie
        max_dist (int): maximum distance Levenstein
        alpha (float): parameter of model language
        """
        self.trie = trie
        self.max_dist = max_dist
        self.alpha = alpha
        
    def search(self, word):
        """
        Args:
        word (string)
        
        Return:
        a list of nearest (word, distance)
        
        Example:
        'corect' =>
        [('direct', 2.8976129598587455),
         ('comet', 3.1622304395971579),
         ('collect', 3.0746835658617675),
         ('correct', 2.0287303329239235),
         ('corrects', 3.3924889488965624),
         ...]
        """
        words = []
        automaton = LevenshteinAutomaton(word, self.max_dist)
        state = automaton.start()
        self.search_recursive(self.trie.children, automaton, state, words)
        return words
        
    def search_recursive(self, node, automaton, state, words):
        """
        Support function for a previous
        """
        for letter in node:
            new_state = automaton.step(state, letter)
            if automaton.is_match(new_state) and node[letter].word != None:
                words.append((node[letter].word, new_state[-1] - \
                              self.alpha * np.log(node[letter].probability)))
            if automaton.can_match(new_state):
                self.search_recursive(node[letter].children, automaton, new_state, words)
                

class SpellChecker:
    def __init__(self, rus_dictionary, eng_dictionary, max_dist=1, alpha=0.1):
        """
        Args:
        rus_dictionary (string): path of russian dictionary
        eng_dictionary (string): path of english dictionary
        max_dist (int): maximum distance Levenstein
        alpha (float): parameter of model language
        """
        self.searcher = {}
        self.searcher['rus'] = WordSearcher(SpellChecker.get_trie(rus_dictionary), \
                                            max_dist, alpha)
        self.searcher['eng'] = WordSearcher(SpellChecker.get_trie(eng_dictionary), \
                                            max_dist, alpha)
        self.alpha = alpha
        
    @staticmethod
    def get_trie(dictionary):
        """
        dictionary (string) => trie (Trie)
        """
        cnt = Counter(SpellChecker.get_words(open(dictionary).read().lower()))
        trie = Trie()
        N = sum(cnt.values())
        for word, count in cnt.items():
            trie.insert(word, count / N)
        return trie
    
    @staticmethod
    def get_words(text):
        """
        'Я иду гулять.' => ['Я', 'иду', 'гулять']
        """
        return re.findall(r'\w+', text)
    
    @staticmethod
    def get_punctuations(text):
        """
        'Я иду гулять.' => [' ', ' ', '.']
        """ 
        return re.findall(r'[^\w]+', text)
    
    @staticmethod
    def get_case(word, correct_word):
        """
        шерлок => Шерлок
        оон => ООН
        """
        if word.istitle():
            return correct_word.title()
        if word.isupper():
            return correct_word.upper()
        return correct_word
    
    @staticmethod
    def get_language(text):
        """
        cat => eng
        кот => rus
        """
        eng_count = len(re.findall(r'[a-zA-Z]', text))
        rus_count = len(re.findall(r'\w', text)) - eng_count
        return 'eng' if rus_count < eng_count else 'rus'
        
    def check(self, text):
        """
        'стекляный' => 'стеклянный'
        'corect' => 'correct'
        """
        lang = SpellChecker.get_language(text)
        words = SpellChecker.get_words(text)
        punctuations = SpellChecker.get_punctuations(text)
        correct_words = []
        correct_text = [None] * (len(punctuations) + len(words))
        
        for word in words:
            lower_word = word.lower()
            candidates = self.searcher[lang].search(lower_word)
            candidates.append((lower_word, np.inf))
            correct_word = min(candidates, key=lambda x: x[1])[0]
            correct_words.append(SpellChecker.get_case(word, correct_word))
        
        correct_text[::2] = correct_words
        correct_text[1::2] = punctuations
        return ''.join(correct_text)