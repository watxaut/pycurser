# pycurser - Or how to beautifully break your language
This repository holds a python algorithm that will scrap a word from [http://www.diccionari.cat] (the catalan 
dictionary) and put the word "fuck" (translated to catalan) before the scraped word. Then this message is 
tweeted in the following Twitter account: [https://twitter.com/L_educador]

There is some considerations regarding catalan words which makes it a little bit more complicated than english.
The word "fuck" in catalan is working as an adverb and has to be adapted to the next word depending on the type (male, 
female, verb, adjective or another adverb)

## Next steps
* Create an abstract class to retrieve the word and extend it to other languages, not just catalan