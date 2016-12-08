from flask import Flask, render_template, request, session
from flask_socketio import SocketIO, emit, join_room, leave_room, \
    close_room, rooms, disconnect
import json
import boto3
import collections
from http.client import IncompleteRead
from requests_aws4auth import AWS4Auth
from elasticsearch import Elasticsearch, RequestsHttpConnection
async_mode = None

application = Flask(__name__)
application.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(application, async_mode=async_mode)
thread = None

awsauth = AWS4Auth('XXXXXXXXXXXXXXXXXXXXXXX', 'XXXXXXXXXXXXXXXXXXXXXXX','us-west-2', 'es')
host = 'XXXXXXXXXXXXXXXXXXXXXXX.com'

# Connecting to elasticsearch
es = Elasticsearch(hosts=[{'host': host, 'port': 443}],
    http_auth=awsauth,
    use_ssl=True,
    verify_certs=True,
    connection_class=RequestsHttpConnection)


def background_thread():
    """Example of how to send server generated events to clients."""
    count = 0
    while True:
        socketio.sleep(10)
        count += 1
        socketio.emit('my_response',
                      {'data': 'Server generated event', 'count': count},
                      namespace='/test')

# Called to process the notification/messages received from SNS 
@application.route('/process', methods=['GET','POST'])
def processinput():
	if request.method == 'POST':
		# check the message type 
		resp = request.headers.get('X-Amz-Sns-Message-Type')
		topic = request.headers.get('X-Amz-Sns-Topic-Arn')
		useragent = request.headers.get('User-Agent')
		json_data = json.loads(request.data.decode('utf-8'))
		# if SubscriptionConfirmation then send confirm response back to SNS
		if  resp =="SubscriptionConfirmation":
			client = boto3.client('sns',aws_access_key_id= 'XXXXXXXXXXXXXXXXXXXXXXX',
                        aws_secret_access_key = 'XXXXXXXXXXXXXXXXXXXXXXX',
                        region_name = 'us-west-2')
			token = json_data['Token']
			response = client.confirm_subscription(
    		TopicArn=topic,
    		Token=token
 			#AuthenticateOnUnsubscribe='string'
			)
			print(response)
			return "Subscription confirmed!"
		# if Notification then receive the message from SNS and put it into AWS Elasticsearch
		elif resp == "Notification":
			message = json_data['Message']
			client = boto3.client('sns',aws_access_key_id= 'XXXXXXXXXXXXXXXXXXXXXXX',
                        aws_secret_access_key = 'XXXXXXXXXXXXXXXXXXXXXXX',
                        region_name = 'us-west-2')
			msg_data = json.loads(message)
			msgid = str(msg_data['id'])
			es.index(index="tweetmap", doc_type='data', id=msgid, body=message) 
			print("data written into elastic search!!")
			return "Notification received"
		else:
			return "Not subscription or notification"	
	else:
		return "In get"

		
# main app to show the map
@application.route('/', methods=['GET','POST'])
def getinput():
	coord = []
	text = []
	sentiment = []
	dic = collections.OrderedDict()
	childdic = collections.OrderedDict()
	if request.method == 'POST':
		# get selected keyword
		result = request.form['option']
		if result is not None:
			bodyOfRequest=""
			firstPart = '{ "query":{"query_string":{"query":'
			lastPart = ' }}}'
			bodyOfRequest = firstPart+'"'+result+'"'+ lastPart
			# search for the keyword in elastic search
			res = es.search(index='tweetmap', body=bodyOfRequest )
			for hit in res['hits']['hits']:
				coord.append (hit["_source"]["coordinates"]["coordinates"])
				text.append(hit["_source"]["text"])
				sentiment.append(hit["_source"]["sentiment"])
				print("%(coordinates)s: %(text)s: %(sentiment)s" % hit["_source"])
			return render_template("index.html", data = coord, info = text, senti = sentiment, keyword = result)
		else:
			print ("error reading ")
			return "ERROR"
	else:
		return render_template("index.html")

# used to receive notification from SNS on indexing any new tweet 
@application.route('/responsive', methods=['GET','POST'])
def responsive():
	if request.method == 'POST':
		resp = request.headers.get('X-Amz-Sns-Message-Type')
		topic = request.headers.get('X-Amz-Sns-Topic-Arn')
		useragent = request.headers.get('User-Agent')
		json_data = json.loads(request.data.decode('utf-8'))
		if  resp =="SubscriptionConfirmation":
			client = boto3.client('sns',aws_access_key_id= 'XXXXXXXXXXXXXXXXXXXXXXX',
                        aws_secret_access_key = 'XXXXXXXXXXXXXXXXXXXXXXX',
                        region_name = 'us-west-2')
			token = json_data['Token']
			response = client.confirm_subscription(
    		TopicArn=topic,
    		Token=token
 			#AuthenticateOnUnsubscribe='string'
			)
			return render_template("index.html",data = "Sucbscription Confirmed!!")
		elif resp == "Notification":
			message = json_data['Message']
			client = boto3.client('sns',aws_access_key_id= 'XXXXXXXXXXXXXXXXXXXXXXX',
                        aws_secret_access_key = 'XXXXXXXXXXXXXXXXXXXXXXX',
                        region_name = 'us-west-2')
			# send message through socket for real time processing
			socketio.emit('my_response',{'data': message})
			return render_template("index.html",data = "Notification received")
		else:
			return render_template("index.html",data = "Not subscription or notification")
	else:
		return render_template('index.html', async_mode=socketio.async_mode)

# socket connection
@socketio.on('connect', namespace='')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})
    
	
if __name__=="__main__":
	application.debug = True
	application.run()

