import datetime
import json
from urllib.parse import quote
from requests import Session
import pymongo
from Utils.MongoDBUtil import MongoDBUtil

db_util = MongoDBUtil()

db_driver="mongodb"
db_user="my-user"
db_password="my-password"
db_host="a54db3bede3864330a228f68c68f2379-1179598598.us-west-2.elb.amazonaws.com"
db_port="27017"
db_name="my-database"
url_string = f"{db_driver}://{db_user}:{quote(db_password)}@{db_host}:{db_port}/{db_name}"
myclient = pymongo.MongoClient(url_string)
mydb = myclient["my-database"]


def send_post_request(request, url):
    """
    Send a network call to the Models which are hosted at FastAPI server
    :param request:
    :param url:
    :return:
    """
    try:
        session = Session()
        response = session.post(
            url=url,
            json=request,
            timeout=10,
            headers={"Connection": "close"},
        )
        session.close()

        de_serialized_response = json.loads(response.content)
        return de_serialized_response
    except Exception as e:
        print(f"Error: {e}")


def validation(api_key):
    """
    validates the api key generated while registering and decides to give access or not

    Parameters
    -----------
    api_key:str
            It represents the api_key
    :param request:
    """

    #collection = db_util.get_collection()
    col=mydb["sandbox"]

    current_time = datetime.datetime.now()
    time_created = []

    # verify_collection = col.find({"_id": api_key})
    verify_collection = col.find()
    print(api_key)

    for value in verify_collection:


        if str(value["_id"]) == api_key:
        # id = str(value["_id"])
        # final_key = id
        # if final_key in [api_key]:
        #     time_created.append(value["time_created"])
            time_created.append(value["time_created"])
            break
    # if len(time_created) == 0:
    #     return 0

    time_diff = current_time - time_created[0]
    if time_diff.total_seconds() > int(18000):
        return 0
    else:
        return 1
# 604800