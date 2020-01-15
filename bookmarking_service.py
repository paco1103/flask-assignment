#last 0930update all things

from flask import Flask, request,jsonify
import json, sqlite3 

app = Flask(__name__)
app.config["DEBUG"] = True
app.config['JSON_SORT_KEYS'] = False	#prevent sort key for output json

db = 'bookmarks.db'

def connectDatabase():
    conn = sqlite3.connect(db)
    cur = conn.cursor()
    query = "CREATE TABLE IF NOT EXISTS 'Bookmarks' ( 'url' TEXT, 'tags' TEXT, 'text' TEXT, 'user_id' TEXT, PRIMARY KEY('url','user_id') )"
    cur.execute(query)
    conn.commit()
    query = "CREATE TABLE IF NOT EXISTS 'Users' ( 'user_id' TEXT, 'user_name' TEXT, PRIMARY KEY('user_id') )"
    cur.execute(query)
    conn.commit()
    conn.close()
    conn = sqlite3.connect(db)
    return conn



#Getting all users
#唔知係order by DESC / ASC
@app.route('/bookmarking/users', methods=['GET'])
def getAllUser():
    query = "SELECT * FROM Users order by user_id asc"
    conn = connectDatabase()
    cur = conn.cursor()
    results = cur.execute(query).fetchall()
    parsed = {
	    "count": str(len(results)), 
		"users":[]
	}
    for i in range(len(results)):
    	item = {
    		"user_id"	: results[i][0],
    		"user_name"	: results[i][1]
    	}
    	parsed["users"].append(item)
    conn.close()
    return jsonify(parsed), 200


#Adding one or more new user(s)
#改左只有all suc then insert else return error
@app.route('/bookmarking', methods=['POST'])
def addUser():
	try:
		args = request.json
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500

	query = "INSERT INTO Users VALUES(?,?)"
	allSuc = True
	sucString = {
		"count" : "",
		"users" : []
	}
	conn = connectDatabase()
	cur = conn.cursor()
	try:
		for i in range(0, len(args["users"])):
			try:
				user_id = args["users"][i]["user_id"]
				user_name = args["users"][i]["user_name"]
			except Exception as e:
				return {"reasons":[{"message":"malformed data"}]}, 500

			try:
				cur.execute(query, [user_id, user_name])
				sucString["users"].append({"user_id":user_id, "user_name":user_name})
			except Exception as e:
				allSuc = False
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500
	if allSuc:
		conn.commit()
	conn.close()
	sucString["count"] = str(len(sucString["users"]))
	if not allSuc:
		return {"reasons" : [{"message": "User already exists"}]}, 400
	return sucString, 201

#Deleting a user
#改左{ "reasons": [ { "message": "User not found" } ] }
@app.route('/bookmarking/<id>', methods=['DELETE'])
def deleteUser(id):
	query = "DELETE FROM Users WHERE user_id = ?"
	conn = connectDatabase()
	cur = conn.cursor()
	results = cur.execute(query, [id]).rowcount
	query = "DELETE FROM Bookmarks WHERE user_id = ?"
	cur.execute(query, [id]).rowcount
	conn.commit()
	conn.close()
	if results > 0:
		return "User is successfully deleted", 204
	return { "reasons": [ { "message": "User not found" } ] }, 404






#Getting all bookmarks
@app.route('/bookmarking/bookmarks', methods=['GET'])
def getAllBookmarks():
	query_parameters = request.args
	tags = query_parameters.get('tags')
	count = query_parameters.get('count')
	offset = query_parameters.get('offset')

	query = "SELECT * FROM Bookmarks"
	if not count:
		count = None
	if not offset:
		offset = 1
	elif int(offset)<=0:
		offset = 1

	conn = connectDatabase()
	cur = conn.cursor()
	query += " order by url, user_id"
	results = cur.execute(query).fetchall()
	parsed = {
		"count": "", 
		"bookmarks":[]
	}
	if tags:
		tag = tags.split(", ") 	#唔知係,or, 
		if len(tag) <= 1:
			tag = tags.split(",")

		removeResult = []

		for i in range(0, len(results)):
			noTag = True
			booktag = results[i][1].split(", ")
			if len(booktag) <= 1:
				booktag = results[i][1].split(",")
			for j in range(0,len(booktag)):
				for k in tag:
					if k in booktag[j]:
						noTag = False
						break
				if not noTag:
					break
			if noTag:
				removeResult.append(i)

		removeCount = 0
		for x in removeResult:
			del results[x - removeCount]
			removeCount += 1

	for i in range(int(offset)-1, len(results)):
		if count != None and int(count) >0:
			count = int(count)
			count -= 1
		elif count == None:
			pass
		else:
			break
		parsed["bookmarks"].append({
			"url":results[i][0],
			"tags":results[i][1],
			"text":results[i][2],
			"user_id":results[i][3]
		})
	parsed["count"] = str(len(parsed["bookmarks"]))

	conn.close()
	return jsonify(parsed), 200







#0918
#Getting all bookmarks for a certain user
@app.route('/bookmarking/bookmarks/<id>', methods=['GET'])
def getUserAllBookmarks(id):
	query_parameters = request.args
	tags = query_parameters.get('tags')
	count = query_parameters.get('count')
	offset = query_parameters.get('offset')

	query = "SELECT * FROM Bookmarks where user_id = ?"

	if tags:
		pass
	if not count:
		count = None
	if not offset:
		offset = 1
	elif int(offset)<=0:
		offset = 1

	conn = connectDatabase()
	cur = conn.cursor()
	query += " order by url"
	results = cur.execute(query, [id]).fetchall()
	parsed = {
		"count": "", 
		"bookmarks":[]
	}


	if len(results) <1:
		query = "SELECT * FROM Users where user_id = ?"
		user = cur.execute(query, [id]).fetchall()
		if len(user) <1:
			return { "reasons": [ { "message": "User not found" } ] }, 404

	# check tags
	if tags:
		tag = tags.split(", ") 	#唔知係,or, 
		if len(tag) <= 1:
			tag = tags.split(",")

		removeResult = []

		for i in range(0, len(results)):
			noTag = True
			booktag = results[i][1].split(", ")
			if len(booktag) <= 1:
				booktag = results[i][1].split(",")
			for j in range(0,len(booktag)):
				for k in tag:
					if k in booktag[j]:
						noTag = False
						break
				if not noTag:
					break
			if noTag:
				removeResult.append(i)

		removeCount = 0
		for x in removeResult:
			del results[x - removeCount]
			removeCount += 1

	for i in range(int(offset)-1, len(results)):
		if count != None and int(count) >0:
			count = int(count)
			count -= 1
		elif count == None:
			pass
		else:
			break
		parsed["bookmarks"].append({
			"url":results[i][0],
			"tags":results[i][1],
			"text":results[i][2],
			"user_id":results[i][3]
		})
	parsed["count"] = str(len(parsed["bookmarks"]))

	conn.close()
	return jsonify(parsed), 200




#Getting a target bookmark for a certain user
#應該冇not found
@app.route('/bookmarking/bookmarks/<id>/<path:url>', methods=['GET'])
def getTargetUserBookmark(id, url):

	query = "SELECT * FROM Bookmarks Where user_id = ? and url = ?"
	conn = connectDatabase()
	cur = conn.cursor()
	results = cur.execute(query, [id, url]).fetchall()
	parsed = {
		"count": "", 
		"bookmarks":[]
	}

	for i in range(len(results)):
		parsed["bookmarks"].append({
			"url":results[i][0],
			"tags":results[i][1],
			"text":results[i][2],
			"user_id":results[i][3]
		})
	parsed["count"] = str(len(parsed["bookmarks"]))

	conn.close()
	return jsonify(parsed), 200













#Adding one or more bookmark(s) for a user
#if one fail, all fail will not add in
@app.route('/bookmarking/<id>/bookmarks', methods=['POST'])
def addBookmarks(id):
	try:
		args = request.json
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500

	conn = connectDatabase()
	cur = conn.cursor()
	query = "SELECT * from Users WHERE user_id = ?"
	results = cur.execute(query, [id]).fetchall()
	if len(results) < 1:
		return { "reasons": [ { "message": "User not found" } ] }, 404

	query = "INSERT INTO Bookmarks VALUES(?,?,?,?)"
	allSuc = True
	sucString = {
		"count":"",
		"bookmarks" : []
	}
	try:
		for i in range(0, len(args["bookmarks"])):
			try:
				url = args["bookmarks"][i]["url"]
				tags = args["bookmarks"][i]["tags"]
				text = args["bookmarks"][i]["text"]
				#user_id = args["bookmarks"][i]["user_id"]
			except Exception as e:
				return {"reasons":[{"message":"malformed data"}]}, 500

			try:
				cur.execute(query, [url, tags, text, id])
				sucString["bookmarks"].append({"url":url, "tags":tags, "text":text, "user_id":id})
			except Exception as e:
				allSuc = False
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500
	if allSuc:
		conn.commit()
	conn.close()
	sucString["count"] = str(len(sucString["bookmarks"]))
	if not allSuc:
		return {"reasons" : [{"message": "Bookmark already exists"}]}, 400
	return sucString, 201










#Updating the title/tag(s) for one or more bookmark(s) for a target user
#唔知json會有D咩, 同埋url有url and id but it is for many/ one book?
#我估only 1 book, and using json, so #左url and id
@app.route('/bookmarking/<id>/bookmarks/<path:url>', methods=['PUT'])
def updateTargetUserBookmark(id, url):
	conn = connectDatabase()
	cur = conn.cursor()
	query = "SELECT * FROM Users where user_id = ?"
	results = cur.execute(query, [id]).fetchall()
	if len(results) <1:
		return { "reasons": [ { "message": "User not found" } ] }, 404
	try:
		args = request.json
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500

	query = "UPDATE Bookmarks SET text = ?, tags = ? WHERE user_id = ? and url = ?"
	allSuc = True
	sucString = {
		"count" : "",
		"bookmarks" : []
	}

	try:
		for i in range(0, len(args["bookmarks"])):
			try:
				#url = args["bookmarks"][i]["url"]
				tags = args["bookmarks"][i]["tags"]
				text = args["bookmarks"][i]["text"]
				#user_id = args["bookmarks"][i]["user_id"]
			except Exception as e:
				return {"reasons":[{"message":"malformed data"}]}, 500

			ok = cur.execute(query, [text, tags, id, url]).rowcount
			if ok < 1:
				allSuc = False
			else:
				#user_id 改左id
				sucString["bookmarks"].append({"url":url, "tags":tags, "text":text, "user_id":id})
	except Exception as e:
		return {"reasons":[{"message":"malformed data"}]}, 500

	if allSuc:
		conn.commit()

	conn.close()
	sucString["count"] = str(len(sucString["bookmarks"]))
	if not allSuc:
		return { "reasons": [{ "message": "Bookmark not found" } ] }, 404
	return sucString, 201




#Deleting a bookmarks
#理論上唔洗改
@app.route('/bookmarking/<id>/bookmarks/<path:url>', methods=['DELETE'])
def deleteBookmarks(id, url):
	conn = connectDatabase()
	cur = conn.cursor()
	query = "SELECT * FROM Users where user_id = ?"
	results = cur.execute(query, [id]).fetchall()
	if len(results) <1:
		return { "reasons": [ { "message": "User not found" } ] }, 404

	query = "DELETE FROM Bookmarks WHERE url = ? and user_id = ?"
	results = cur.execute(query, [url, id]).rowcount
	conn.commit()
	conn.close()
	if results > 0:
		return "Request is Successful", 204
	return { "reasons": [ { "message": "Bookmark not found" } ] }, 404




app.run(port=5000)
