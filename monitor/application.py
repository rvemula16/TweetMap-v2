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

awsauth = AWS4Auth('AKIAIEVN4MYCQV4ZQMCA', 'p1m6O3j/D82GdjOdHUmQETfqFTNCXSiDRgcJ3SzW','us-west-2', 'es')
host = 'search-tweetmap-wvcfiy2v2joahl22p4eljwnnre.us-west-2.es.amazonaws.com'

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

def findWholeWord(w):
    return re.compile(r'\b({0})\b'.format(w), flags=re.IGNORECASE).search

@application.route('/process', methods=['GET','POST'])
def processinput():
	#print("+++++++++++++++++++++++++++++++++++++++")
	if request.method == 'POST':
		print("!@!@!@!@!@!@!@!@!@!@!@!@!")
		resp = request.headers.get('X-Amz-Sns-Message-Type')
		topic = request.headers.get('X-Amz-Sns-Topic-Arn')
		useragent = request.headers.get('User-Agent')
		json_data = json.loads(request.data.decode('utf-8'))
		if  resp =="SubscriptionConfirmation":
			client = boto3.client('sns',aws_access_key_id= 'AKIAIEVN4MYCQV4ZQMCA',
                        aws_secret_access_key = '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',
                        region_name = 'us-west-2')
			token = json_data['Token']
			print("in confirmation:::::::::::::::::")
			response = client.confirm_subscription(
    		TopicArn=topic,
    		Token=token
 			#AuthenticateOnUnsubscribe='string'
			)
			print(response)
			return "Subscription confirmed!"
		elif resp == "Notification":
			#json_data = json.loads(request.data.decode('utf-8'))
			message = json_data['Message']
			client = boto3.client('sns',aws_access_key_id= 'AKIAIEVN4MYCQV4ZQMCA',
                        aws_secret_access_key = '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',
                        region_name = 'us-west-2')
			print("```````````````````````````````````````````````````````````````````")
			print(message)
			msg_data = json.loads(message)
			msgid = str(msg_data['id'])
			es.index(index="tweetmap", doc_type='data', id=msgid, body=message) 
			print("data written into elastic search!!")
			return "Notification received"
		else:
			return "Not subscription or notification"	
	else:
		return "In get"

		

@application.route('/', methods=['GET','POST'])
def getinput():
	coord = []
	text = []
	sentiment = []
	dic = collections.OrderedDict()
	childdic = collections.OrderedDict()
	#print ("%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%")
	if request.method == 'POST':
		#try:
		print("^^^^^^^^^^^^^^^^^^^^^^^^^^^^%%%%%%%%%%%%%%%%%%%%%%%%%%^^^^^^^^^^^^^^^^^^^^^^^^^^^")
		print(request.headers)
		result = request.form['option']
		if result is not None:
			print (result)
			#session["keyword"] = result
			bodyOfRequest=""
			firstPart = '{ "query":{"query_string":{"query":'
			lastPart = ' }}}'
			bodyOfRequest = firstPart+'"'+result+'"'+ lastPart
			print("-----------------")
			print(bodyOfRequest)
			res = es.search(index='tweetmap', body=bodyOfRequest )
			#jsonArray = json.dumps(dic)
			#jsonArray = json.dumps({})
			for hit in res['hits']['hits']:
				#childdic['coordinate'] = hit["_source"]["coordinates"]["coordinates"]
				#childdic['text'] = hit["_source"]["text"]
				#childdic['sentiment'] = hit["_source"]["sentiment"]
				#dic[1] = childdic
				coord.append (hit["_source"]["coordinates"]["coordinates"])
				text.append(hit["_source"]["text"])
				sentiment.append(hit["_source"]["sentiment"])
				#jsonArray = jsonArray.append(json.dumps(childdic))
				print("%(coordinates)s: %(text)s: %(sentiment)s" % hit["_source"])
			print("**********************************************************")
			print (coord)
			print(text)
			print(sentiment)
			return render_template("index.html", data = coord, info = text, senti = sentiment, keyword = result)
		else:
			print ("error reading ")
			return "ERROR"
		#except httplib.IncompleteRead as e:
			#result = "null"
	else:
		tv_show = "The Office"
		return render_template("index.html")


@application.route('/responsive', methods=['GET','POST'])
def responsive():
	#print("+++++++++++++++++++++++++++++++++++++++")
	if request.method == 'POST':
		print("!@!@!@!@!@!@!@!@!@!@!@!@!")
		print(request.headers)
		resp = request.headers.get('X-Amz-Sns-Message-Type')
		topic = request.headers.get('X-Amz-Sns-Topic-Arn')
		useragent = request.headers.get('User-Agent')
		json_data = json.loads(request.data.decode('utf-8'))
		if  resp =="SubscriptionConfirmation":
			client = boto3.client('sns',aws_access_key_id= 'AKIAIEVN4MYCQV4ZQMCA',
                        aws_secret_access_key = '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',
                        region_name = 'us-west-2')
			token = json_data['Token']
			print("in confirmation //////////////////////////////////////////////")
			response = client.confirm_subscription(
    		TopicArn=topic,
    		Token=token
 			#AuthenticateOnUnsubscribe='string'
			)
			print(response)
			return render_template("index.html",data = "Sucbscription Confirmed!!")
		elif resp == "Notification":
			#json_data = json.loads(request.data.decode('utf-8'))
			message = json_data['Message']
			client = boto3.client('sns',aws_access_key_id= 'AKIAIEVN4MYCQV4ZQMCA',
                        aws_secret_access_key = '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',
                        region_name = 'us-west-2')
			print(message)
			#@socketio.on('my_event', namespace='')
			#if session["keyword"] != null:
			#	search_word = session["keyword"]
			#if search_word in message:
			socketio.emit('my_response',{'data': message})
			print("notification received")
			print("CCCCCCCCCCCCCCCCCCCA@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@@")
			return render_template("index.html",data = "Notification received")
		else:
			return render_template("index.html",data = "Not subscription or notification")
	else:
		return render_template('index.html', async_mode=socketio.async_mode)

		
@socketio.on('connect', namespace='')
def test_connect():
    global thread
    if thread is None:
        thread = socketio.start_background_task(target=background_thread)
    emit('my_response', {'data': 'Connected', 'count': 0})
    
	
if __name__=="__main__":
	application.debug = True
	application.run()

