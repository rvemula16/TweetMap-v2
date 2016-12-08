# Used to --
# Define a worker pool that will pick up messages from the queue to process. These workers should each run on a separate pool thread.
# Make a call to the sentiment API off your preference (e.g. Alchemy (Links to an external site.)). This can return a positive, negative or neutral sentiment evaluation for the text of the submitted Tweet.
# As soon as the tweet is processed send a notification -using SNS- to an HTTP endpoint (Links to an external site.) that contains the information about the tweet.
#
import boto3
import json
import collections
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
from alchemyapi import AlchemyAPI

# User credentials to access Twitter API
access_token = 'XXXXXXXXXXXXXXXXXXXXXXXXX'
access_token_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'
consumer_key = 'XXXXXXXXXXXXXXXXXXXXXXXX'
consumer_secret = 'XXXXXXXXXXXXXXXXXXXXXXXXXXXXX'

awsauth = AWS4Auth('XXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXX','us-west-2', 'es')
# to perform sentiment analysis on the tweets collected
alchemyapi = AlchemyAPI()
# Get the queue
sqs = boto3.resource('sqs')
dic = collections.OrderedDict()


try:
	queue = sqs.get_queue_by_name(QueueName='testqq')
	# process messages
	while True:
		for msg in queue.receive_messages(WaitTimeSeconds = 10):
			parsed_input = json.loads(msg.body)
			id = parsed_input['id']
			text = parsed_input['text']
			response = alchemyapi.sentiment("text", text)
			coordinates = parsed_input['coordinates']
			status = response.get('status')
			if status == 'ERROR':
				sentiment = "neutral"
			else:
				sentiment = response["docSentiment"]["type"]
			dic['id'] = id
			dic['text'] = text
			dic['coordinates'] = coordinates
			dic['sentiment'] = sentiment
			jsonArray = json.dumps(dic)
			# creating a sns topic to send notification
			client = boto3.client('sns')
			res = client.create_topic(Name = 'newtweet')
			topicArn = res['TopicArn'];
			response = client.subscribe(TopicArn= topicArn,Protocol='HTTP',Endpoint= 'http://XXXXXXXXXXXXXXXXXXXXXXX/process')
			response = client.publish(TopicArn=topicArn,Message=str(jsonArray))
			clientone = boto3.client('sns')
			res = client.create_topic(Name = 'res')
			print("beforrrrrrrrrrrrrrrrrrrrrrr#############################")
			topicArn = res['TopicArn'];
			response = client.subscribe(TopicArn= topicArn,Protocol='HTTP',Endpoint= 'http://XXXXXXXXXXXXXXXXXXXXXXX/responsive')
			response = client.publish(TopicArn=topicArn,Message=str(jsonArray))
			print("DONE")
			
except BaseException as e:
	print(str(e))

except attributeerror as e:
	print(str(e))

except keyerror as e:
	print(str(e))			
		
except exception as e:
	print(str(e))
