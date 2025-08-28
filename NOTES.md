# Sentiment Analysis Progress
12.8
## Utterance Processing
- Completed processing utterances
- Each JSON file contains committee utterances for a specific date
- Considering conversion to pandas format for better analysis

## Sentiment Analysis Implementation
1. **Initial Approach**:
    - Started with a naive dictionary-based method using TextBlob with translation
    - More challenging than anticipated
    - May explore pre-trained models later (e.g., unitary/multilingual-toxic-xlm-roberta from Hugging Face)



2. **Translation Process**:
    - Most sentiment analysis requires English text due to pre-trained networks
    - Initially tested 'googletrans' but found it limiting and slow
    - Switched to LibreTranslate via Docker container
    - LibreTranslate performs adequately for sentiment analysis as it only needs to capture negative terminology rather than full contextual meaning
3. About actual conceptual clasiffiction - probably use some generic BERT, and fine tune it for that. than achieehve some embedding
    space and map it into clusters using HDBSCAN, and using ptv titles+committie names

 

4. Sentence Embedding - https://arxiv.org/pdf/1908.10084. using SBert, which is like the BERT transformer model that requires both training for langauge understanding and fine tune to the specific task (Q&A, fill the blank.. in our case - just to embed the sentences to a vector space with context). SBert contains two BERT models trained togehter that mirror each other in weights. its pre-trained to search similiarity between two sentences,which is useful for our task, because we want unlabled classifiction.
We Use SBert and not BERT with sentence classification because it was already fine tuned on sentences, for embedding on vector space.
Naively, I embed the pure utterances with a prefix of the commitee name

17.8
**FAISS**
I plan to use FAISS to be able to query the utterances and find the closest ones, and then find the MK with most utterances on the subject. might run clustering algorithm on the database because it might be too slow to search the whole vector db every time


**Initial Conclusions**
When reviewing utterances labeled as "negative" by TextBlob, I noticed they often did not contain only polarizing or inflammatory content. Many included discussions of serious or sensitive issues. For example, statements about reducing the murder rate received a negative polarity score, despite addressing an important and constructive topic in committee discussions.
This limitation might be mitigated by aggregating a large number of utterances per MK, under the assumption that an inflammatory MK will exhibit such tone consistently across a wide range of topics.

**Quility Of Life**
threads for more things and "force_reload" mechanism for whole pipeline to not start from scratch everytime unless required to 

**critical findings**
Some utterances are not saved as the metadata shows as <<יור>> or <<שר החינוך>> which is critical
Some utterances are got into the utternces database even tho they are not MKS

Translating hunders of thoustends of utternces just for santiment analsys is a bit of an overkill and takes too much time, espesically since its just for pritimive TextBlob lib. 
might just pick random 200 Utternaces for each MK.

Also, might need to find a way to make use of GPU in embedding - either use my own AMD card with orcM, or if not successful (as its not widely supported), might use some cloud compute

18.8 
Started refnining utterances. seems like some subjects are getting double written\not written. have a problem with middle names 
seems like there are too many options for first-last names kinds and ways to write them. i need to use rapidfuzz to help me with that, just to catch names correctly. also logging to file mks that didnt found exact match


22.8.25
refining utterances further, added logging. now rapidfuzz will take only from specific certainty..  also a minor refactor.


24.8.25
added app boilerplate


27.8
opted out of docker, just running libretranslate directly, too much nonsense to deal with with docker engine
addded partition system to data pipeline to allow more multiprocessing utternaces and some generator pulling in embedder.
I think the first approach of embedding whonly clean utterances and search on them is too naive, i need to add contextt to each utterance - maybe the title of the commitie.
also need to filter out useless utterances of "תגיד לו" or "אני מסכים". so the naive approch is to filter out utterances shorter than 3 words  on embedding
Also, paramerts getting too complex, i think ill configure some JSON settings file instead of all this different env vars\params\constants.
also, ill move to a class based apporach as each module gets a lot of compositions and its getting ugly 

28/8/25
there is about a 1m utterances in the full data - which is 700*m for vector space. if we choose the standart of float32 to represnent the utterances,  we have actually 700 * 1500000 * 4 = 4200000000
which is about 5GB, so my ol machine can handle it perfectly well, albiet slowly, my amd GPU is kinda not liking the idea of using it for ML pipelines and just wants to run games. 
installed remote desktop client to allow for connection to machine from my android phone. seems easier than grapichal SSH.

I think about measuring the scuesses of the embedding. might need to embed also in some naive textWord static embedding from dictionry to prove im doing better than that. also, before that, i need to have an embedding ready+run hdbscan (dont want to explicitly cap number of clusters..)
clustering is key heere not only for verification but also for an intresting feature i want to impl - i dream of an interactive infographic that will show the mks in relation to subjects, and will allow each mk to have a "profile" with core issues he's been working on.
also, this mk will have a score based on the mean sentiment of his utterances. it will be like a video game.

seems like my gpu is not supported :( ill have to use some cloud provider probably
started using google colab just to extract the embeddings file. seems much faster. embedded 1.4m in half an hour.

*moved indivudal modules for different packages because it became a mayhem 