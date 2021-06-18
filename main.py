from wordcloud import WordCloud, STOPWORDS

import lithops
import tweepy
import pandas as pd
import matplotlib.pyplot as plt

from config.config import config
from backend import cosBackend

import data_preprocessing as dp
import data_crawling as dc
import word_count as wc


iterdf = []

def stage1():
    iterdata = [(api, 100,"coronavirus"), (api, 100,"covid19"), (api, 100,"covid-19"), (api, 100,"SARS-CoV-2")]
    
    fexec.map(dc.search_tweets, iterdata)
    result = (fexec.get_result())
    
    iterHashtag = [
                    ('data/coronavirus','','csv',result[0].to_string())
                    ,('data/covid19','','csv',result[1].to_string())
                    ,('data/covid-19','','csv',result[2].to_string()) 
                    ,('data/SARS-CoV-2','','csv',result[3].to_string())
    ]
    
    i = 0
    for tweet in result:
        print(f"\n{iterHashtag[i][0]}\n")
        cos.put_object(prefix=iterHashtag[i][0], name='', ext=iterHashtag[i][2], body=iterHashtag[i][3])
        i += 1

def stage2():
    tweets = [ [] ]
   
    keys = cos.list_keys(prefix='data')

    i = 0
    for key in keys:
        object = cos.get_object(key)
        s = object.decode()
        for sin in s.splitlines()[1:]:
            if len(tweets[i]) == 1000:
                i += 1
                tweets.append([])

            tweets[i].append(sin.split(maxsplit=5)[1:])
    
    for tweet in tweets:
        dfObj = pd.DataFrame(tweet, columns = ['date' , 'time', 'geo', 'url', 'text'])
        df_sentiment = dp.sentiment_analysis(dfObj)
        iterdf.append(df_sentiment)
        #cos.put_object(prefix='preprocess', name='', ext='csv', body=df_sentiment.to_string())
    
    #print(f"Deleting: {keys}\n")
    #cos.delete_objects(keys)

def stage3():
    result = {}
    for df in iterdf:
        result.update(wc.word_count(df))
    
    result = sorted(result.items(), key=lambda x: x[1], reverse=True)

    tokens = []
    for key in result:
        tokens.append(key[0])
    #print(tokens)
    comment_words = ''
    comment_words += " ".join(tokens)+" "
    stopwords = set(STOPWORDS)

    wordcloud = WordCloud(width = 800, height = 800,
                background_color ='white',
                stopwords = stopwords,
                min_font_size = 10).generate(comment_words)
  
    # plot the WordCloud image                       
    plt.figure(figsize = (8, 8), facecolor = None)
    plt.imshow(wordcloud)
    plt.axis("off")
    plt.tight_layout(pad = 0)
    
    plt.show()
    
    print(result)


def delete_lithop_objects():
    cos.delete_objects(keys=cos.list_keys(prefix='lithops.runtimes'))
    cos.delete_objects(keys=cos.list_keys(prefix='lithops.runtime'))
    cos.delete_objects(keys=cos.list_keys(prefix='lithops.jobs'))

if __name__ == '__main__':
    auth = tweepy.OAuthHandler(config['tweepy']['API_KEY'], config['tweepy']['API_SECRET_KEY'])
    auth.set_access_token(config['tweepy']['ACCESS_TOKEN'], config['tweepy']['ACCESS_SECRET_TOKEN'])
    api = tweepy.API(auth)
    
    
    fexec = lithops.FunctionExecutor(config=config,runtime='arppi/sd-lithops-custom-runtime-39:0.3')
    #fexec = lithops.FunctionExecutor(config=config,runtime='arppi/sd-lithops-custom-runtime-38:0.4')
    
    cos = cosBackend(config)
    
    #stage1()
    stage2()
    stage3()
    delete_lithop_objects()
   