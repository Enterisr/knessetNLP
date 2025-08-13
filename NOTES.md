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