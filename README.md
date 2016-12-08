## TweetMapCloud-v2##

This project is performs analysis of tweets based on keywords specified.

#gettweet.py#
- used to get tweets from twitter using live streaming API provided by tweepy
- places it on AWS SQS for further processing

#application.py#
- used to host flask app for web interface
- receives notification/messages from AWS SNS containing information on the tweets received
- receives notification from AWS SNS having details of new indexed tweets
- responsible for placing and indexing tweets into/from AWS Elasticsearch

#worker.py#
- used to place perform sentiment analysis usiing alchemy API after retrieving data from AWS SQS
- send notification to app through AWS SNS