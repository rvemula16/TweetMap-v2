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
access_token = '781950288466935808-qJzrIDv0gv9giCmMZATqxII52juoHIW'
access_token_secret = 'gX35Ak4P8JB4s5xqEuMZNwOwO5L8bAbZhaXHHPnWQMaI0'
consumer_key = 'gbsa3hkFg4nEn5FvKHxRAmRZq'
consumer_secret = 'mygRjbiLGd40Q1HGbfObSpUCAZEGZVdDmpD8mPLJBAs4Kq6qAR'

awsauth = AWS4Auth('AKIAIEVN4MYCQV4ZQMCA', 'p1m6O3j/D82GdjOdHUmQETfqFTNCXSiDRgcJ3SzW','us-west-2', 'es')
#host = 'search-tweetmap-wvcfiy2v2joahl22p4eljwnnre.us-west-2.es.amazonaws.com'
#es = Elasticsearch(hosts=[{'host': host, 'port': 443}],
#    http_auth=awsauth,
#    use_ssl=True,
#    verify_certs=True,
#    connection_class=RequestsHttpConnection)

alchemyapi = AlchemyAPI()
sqs = boto3.resource('sqs')
dic = collections.OrderedDict()

# Get the queue
try:
	queue = sqs.get_queue_by_name(QueueName='testqq')
	# process messages
	while True:
		for msg in queue.receive_messages(WaitTimeSeconds = 10):
			print(msg.body);
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
			client = boto3.client('sns')
			res = client.create_topic(Name = 'newtweet')
			topicArn = res['TopicArn'];
			response = client.subscribe(TopicArn= topicArn,Protocol='HTTP',Endpoint= 'http://wow-dev-test.us-west-2.elasticbeanstalk.com/process')
			response = client.publish(TopicArn=topicArn,Message=str(jsonArray))
			clientone = boto3.client('sns')
			res = client.create_topic(Name = 'res')
			print("beforrrrrrrrrrrrrrrrrrrrrrr#############################")
			topicArn = res['TopicArn'];
			response = client.subscribe(TopicArn= topicArn,Protocol='HTTP',Endpoint= 'http://wow-dev-test.us-west-2.elasticbeanstalk.com/responsive')
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
