
#
# Reads a stream of tweets from the Twitter Streaming API. Note: you might follow a set of specific keywords that you find interesting
# After fetching a new tweet, check to see if it has geolocation info and is in English.
# Once the tweet validates these filters, send a message to SQS for asynchronous processing on the text of the tweet
#
from tweepy.streaming import StreamListener
from tweepy.streaming import StreamListener
from tweepy import OAuthHandler
from tweepy import Stream
from http.client import IncompleteRead
import logging
from array import *
import collections
from flask import jsonify
import threading
import json
import boto3
from elasticsearch import Elasticsearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from flask import Flask, render_template, request

_log = logging.getLogger(__name__)

# User credentials to access Twitter API
access_token = '781950288466935808-qJzrIDv0gv9giCmMZATqxII52juoHIW'
access_token_secret = 'gX35Ak4P8JB4s5xqEuMZNwOwO5L8bAbZhaXHHPnWQMaI0'
consumer_key = 'gbsa3hkFg4nEn5FvKHxRAmRZq'
consumer_secret = 'mygRjbiLGd40Q1HGbfObSpUCAZEGZVdDmpD8mPLJBAs4Kq6qAR'

# User credentials to access aws services
awsauth = AWS4Auth('AKIAIEVN4MYCQV4ZQMCA', 'p1m6O3j/D82GdjOdHUmQETfqFTNCXSiDRgcJ3SzW','us-west-2', 'es')
#host = 'search-hw2sample-3hs235mux6h4u7qnorhgx2odli.us-west-2.es.amazonaws.com'
lock = threading.Lock()

# Connecting to elasticsearch
#es = Elasticsearch(hosts=[{'host': host, 'port': 443}],
#    http_auth=awsauth,
#    use_ssl=True,
#    verify_certs=True,
#    connection_class=RequestsHttpConnection)

# Create the queue. This returns an SQS.Queue instance
sqs = boto3.resource('sqs')

# You can now access identifiers and attributes
queue = sqs.create_queue(QueueName='testqq')

class TwitterListener(StreamListener):

	
	def __init__(self, phrases):
		auth = OAuthHandler(consumer_key, consumer_secret)
		auth.set_access_token(access_token, access_token_secret)
		try:
			self.__stream = Stream(auth, listener=self)
			self.__stream.filter(track=phrases, async=True)
		except IncompleteRead:
			pass

		
	def disconnect(self):
		self.__stream.disconnect()

	def on_data(self, data):
		dic = collections.OrderedDict()
		
		try:
			data = json.loads(data)
			# Checking if geolocation is present and also if it is in english
			if data['coordinates'] and data['text'] and data['lang']=="en":
				with lock:
					with open("output.json", "a") as f:
						f.write("here")
						f.write(str(data))
						print(data)
						dic['id'] = data['id']
						dic['text'] = data['text']
						dic['coordinates'] = data['coordinates']
						jsonArray = json.dumps(dic)
						# Create a new message
						response = queue.send_message(MessageBody=jsonArray)
						#es.index(index="test", doc_type='tweet', id=data['id'], body=jsonArray) 
						print("\n@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
						print(data['coordinates']['coordinates'], data['text'])
						#print(response.get('MessageId'))
						#print(response.get('MD5OfMessageBody'))
						print("data written")
						with open("output.json", "a") as f:
							f.write(str(jsonArray))
						
			return True
		except BaseException as e:
			print(str(e))
			return True
		except attributeerror as e:
			print(str(e))
			return True
		except keyerror as e:
			print(str(e))
			return True
		except exception as e:
			print(str(e))
			return True


	def on_error(self, status):
		print(status)
		return True

if __name__ == '__main__':
	logging.basicConfig(level=logging.INFO)
	

phrases = ['trump', 'debate', 'obama', 'clinton', 'technology', 'NBA', 'movie', 'crime', 'cricket','Modi','Demonetization','India','Rupees','Brazil','Deals','Soccer','Christmas','Thanksgiving']
listener = TwitterListener(phrases)