#!/usr/bin/env python
# coding: utf-8

# In[149]:


from googleapiclient.discovery import build
from dateutil import parser
import pandas as pd
from IPython.display import JSON

#Data viz packages
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker

#NLP 
from wordcloud import WordCloud, STOPWORDS


# In[150]:


api_key = 'AIzaSyBLY0OhEwp4EDHiD1hM1O_8uaxFDk_l-LY'


# In[151]:


channel_ids = ['UCddYvBABZ8J47nJxj-69RRw',
            # more channels here
            ]


# In[152]:


api_service_name = "youtube"
api_version = "v3"

# Get credentials and create an API client
youtube = build(
    api_service_name, api_version, developerKey=api_key)


# In[153]:


def get_channel_stats(youtube, channel_ids):
    
    all_data = []
    
    request = youtube.channels().list(
            part="snippet,contentDetails,statistics",
            id=','.join(channel_ids)
        )
    response = request.execute()

    #loop through items 
    for item in response['items']:
        data = {'channelName': item['snippet']['title'],
               'subscribers': item['statistics']['subscriberCount'],
               'views': item['statistics']['viewCount'],
               'totalVideos': item['statistics']['videoCount'],
               'playlistId': item['contentDetails']['relatedPlaylists']['uploads']
        }
        all_data.append(data)
        
        return(pd.DataFrame(all_data))


# In[154]:


channel_stats = get_channel_stats(youtube, channel_ids)


# In[155]:


channel_stats


# In[156]:


playlist_id = "UUddYvBABZ8J47nJxj-69RRw"

def get_video_ids(youtube, playlist_id):

    video_ids = []

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        playlistId=playlist_id,
        maxResults=50
    )
    response = request.execute()

    for item in response['items']:
        video_ids.append(item['contentDetails']['videoId'])
        
        next_page_token = response.get('nextPageToken')
        while next_page_token is not None:
            request = youtube.playlistItems().list(
                part="contentDetails",
                playlistId=playlist_id,
                maxResults=50,
                pageToken = next_page_token)
            response = request.execute()
            
            for item in response['items']:
                video_ids.append(item['contentDetails']['videoId'])
                
            next_page_token = response.get('nextPageToken')

    return video_ids


# In[157]:


video_ids = get_video_ids(youtube, playlist_id)


# In[158]:


#Video Count 
len(video_ids)


# In[159]:


def get_video_details(youtube, video_ids):

    all_video_info = []

    for i in range(0, len(video_ids), 50):
        request = youtube.videos().list(
            part="snippet,contentDetails,statistics",
            id=video_ids[0:5]
    )
    response = request.execute()
  

    for video in response['items']:
        stats_to_keep = {'snippet': ['channelTitle', 'title', 'description', 'tags', 'publishedAt'],
                        'statistics': ['viewCount', 'likeCount', 'favouriteCount', 'commentCount'],
                        'contentDetails': ['duration', 'definition', 'caption']}

        video_info = {}
        video_info['video_id'] = video['id']

        for k in stats_to_keep.keys():
            for v in stats_to_keep[k]:
                try:
                    video_info[v] = video[k][v]
                except:
                    video_info[v] = None

        all_video_info.append(video_info)

    return pd.DataFrame(all_video_info)


# In[160]:


#Get video details 
video_df = get_video_details(youtube, video_ids)
video_df


# # Data pre-processing

# In[161]:


video_df.isnull().any()


# In[180]:


video_df.dtypes


# In[182]:


numeric_cols = ['viewCount', 'likeCount', 'favouriteCount', 'commentCount']
video_df[numeric_cols] = video_df[numeric_cols].apply(pd.to_numeric, errors = 'coerce', axis = 1)


# In[184]:


#Publish day in the week 
video_df['publishedAt'] = video_df['publishedAt'].apply(lambda x: parser.parse(x))
video_df['pushblishedDayName'] = video_df['publishedAt'].apply(lambda x: x.strftime("%A"))


# In[185]:


#convert duration to seconds
import isodate
video_df['durationSecs'] = video_df['duration'].apply(lambda x: isodate.parse_duration(x))
video_df['durationSecs'] = video_df['durationSecs'].astype('timedelta64[s]')


# In[186]:


video_df[['durationSecs', 'duration']]


# In[187]:


#Add tag ocunt 
video_df['tagCount'] = video_df['tags'].apply(lambda x: 0 if x is None else len(x))


# In[188]:


video_df


# ## Best performing videos

# In[189]:


ax = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending=False)[0:9])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos:'{:,.0f}'.format(x/1000) + 'K'))


# # Worst Performing Video

# In[190]:


ax = sns.barplot(x = 'title', y = 'viewCount', data = video_df.sort_values('viewCount', ascending=True)[0:9])
plot = ax.set_xticklabels(ax.get_xticklabels(), rotation=90)
ax.yaxis.set_major_formatter(ticker.FuncFormatter(lambda x, pos:'{:,.0f}'.format(x/1000) + 'K'))


# # View distribution per video

# In[191]:


sns.violinplot(video_df['viewCount'])


# In[192]:


fig, ax = plt.subplots(1,2)
sns.scatterplot(data = video_df, x = 'commentCount', y = 'viewCount', ax = ax[0])
sns.scatterplot(data = video_df, x = 'likeCount', y = 'viewCount', ax = ax[1])


# In[193]:


sns.histplot(data = video_df, x = 'durationSecs', bins=30)


# ## Wordcloud for video titles 

# In[197]:


stop_words = set(('english'))
video_df['title_no_stopwords'] = video_df['title'].apply(lambda x: [item for item in str(x).split() if item not in stop_words])

all_words = list([a for b in video_df['title_no_stopwords'].tolist() for a in b])
all_words_str = ' '.join(all_words)

def plot_cloud(wordcloud):
    plt.figure(figsize=(30, 20))
    plt.imshow(wordcloud)
    plt.axis("off");
    
wordcloud = WordCloud(width = 2000, height = 1000, random_state=1, background_color='black', 
                      colormap='viridis', collocations=False).generate(all_words_str)

plot_cloud(wordcloud)


# # Upload Schedule

# In[200]:


day_df = pd.DataFrame(video_df['pushblishedDayName'].value_counts())
weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
day_df = day_df.reindex(weekdays)
ax = day_df.reset_index().plot.bar(x='index', y='pushblishedDayName', rot=0)


# In[ ]:




