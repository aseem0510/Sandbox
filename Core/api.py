# import necessary libraries
import uvicorn
from fastapi import FastAPI, Request, File, UploadFile, Request, Form
from fastapi.responses import RedirectResponse, HTMLResponse
from fastapi.templating import Jinja2Templates
import requests
import json
from fastapi.staticfiles import StaticFiles
import boto3
from werkzeug.utils import secure_filename
import os
import io
from PIL import Image
import datetime
from Utils.MongoDBUtil import MongoDBUtil
import starlette.status as status
from starlette.responses import RedirectResponse
import os
from starlette.status import HTTP_302_FOUND,HTTP_303_SEE_OTHER
from fastapi import FastAPI, status
from fastapi.responses import RedirectResponse
from Validation.core_logic import validation
from fastapi import responses
from fastapi import APIRouter
from dotenv import load_dotenv
load_dotenv()  # take environment variables from .env.

db_util = MongoDBUtil()

AWS_ACCESS_KEY_ID = os.getenv('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.getenv('AWS_SECRET_ACCESS_KEY')
AWS_REGION = os.getenv('AWS_REGION')
S3_Bucket = os.getenv('S3_Bucket')
S3_Key = os.getenv('S3_Key')

def upload_to_aws(local_file, bucket, s3_file):
    try:
        s3.upload_file(local_file, bucket, s3_file)
        return True

    except Exception as e:
        print(e)
        return False


# intilializing fastpi instance
app = APIRouter(include_in_schema=False)
app.mount("/static", StaticFiles(directory="static"), name="static")

s3 = boto3.client('s3',
                    aws_access_key_id=AWS_ACCESS_KEY_ID,
                    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
                     )

templates = Jinja2Templates(directory="html")

user_name = None

@app.get("/home/")
async def write_home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.get('/register/', response_class=HTMLResponse)
def registration(request: Request, msg: str = None):
    try:
        lst = msg.split("-")
    except:
        lst = None
    return templates.TemplateResponse("registration.html", {"request": request, "response": lst})


@app.post("/register/")
async def register_data(request: Request, f_name: str = Form(...), l_name: str = Form(...), username: str = Form(...), email: str = Form(...), company_name: str = Form(...)):
    
    f_name = f_name
    l_name = l_name
    username = username
    email = email
    company_name = company_name

    collection = db_util.get_collection()

    c = collection.find()
    for data in c:
        print(data)
    
    print()

    verify_collection = collection.find({"first_name": f_name, "last_name": l_name, "username": username, "email": email, "company_name": company_name}
    )

    check_flag = None

    for value in verify_collection:
        if (
            value["first_name"] == f_name
            and value["last_name"] == l_name
            and value["email"] == email
            and value["company_name"] == company_name
            and value["username"] == username
        ):
            # value["time_created"] == datetime.datetime.now()
            check_flag = str(value["_id"])

    if check_flag:

        flag = validation(check_flag)

        # not expired
        if flag:

            return responses.RedirectResponse(
                    "/register/?msg=Already-Registered", status_code=status.HTTP_302_FOUND,
                )
        
        else:

            # Updating based on this
            filter = {"first_name": f_name, "last_name": l_name, "username": username, "email": email, "company_name": company_name}
            
            # Values to be updated.
            newvalues = { "$set": { 'time_created': datetime.datetime.now() } }
            
            # Using update_one() method for single
            # updation.
            collection.update_one(filter, newvalues)

            return responses.RedirectResponse(
                "/login/?msg=Access-key-updated-use-your-previous-key-for-login", status_code=status.HTTP_302_FOUND
            ) 

    else:

        collection.insert_one(
            {
                "first_name": f_name,
                "last_name": l_name,
                "email": email,
                "username": username,
                "company_name": company_name,
                "time_created": datetime.datetime.now(),
            }
        )

        c = collection.find()
        for data in c:
            print(data)
        
        return responses.RedirectResponse(
                "/login/?msg=Registered-Successfully", status_code=status.HTTP_302_FOUND
            ) 


@app.get('/login/', response_class=HTMLResponse)
async def login(request: Request, msg: str = None):
    try:
        lst = msg.split("-")
    except:
        lst = None

    return templates.TemplateResponse("login.html", {"request": request, "response": lst})


@app.post("/login/")
async def login_data(request: Request, username: str = Form(...), access_key: str = Form(...)):

    username = username    
    # api_key = access_key
    api_key = "6319b9d2b1c9e6efc7dff11f"
    # api_key = "22222222222222"

    key_ids = db_util.get_keys()

    if api_key not in key_ids:
        return responses.RedirectResponse(
                "/register/?msg=You-Are-Not-Registered", status_code=status.HTTP_302_FOUND,
        ) 

    else:

        flag = validation(api_key)

        if flag == 0:
            return responses.RedirectResponse(
                "/register/?msg=Access-Key-is-Expired-Try-to-Register-again", status_code=status.HTTP_302_FOUND,
            ) 

        else:
            return responses.RedirectResponse(
                "/dashboard/?msg=Welcome-{}-To-EM-Sandbox-Dashboard".format(username), status_code=status.HTTP_302_FOUND
            )


@app.get("/dashboard/")
async def dashboard(request: Request, msg: str = None):

    global user_name

    try:
        lst = msg.split("-")
        user_name = lst[1]
    except:
        lst = None

    return templates.TemplateResponse("dashboard.html", {"request": request, "response": lst, "username": user_name})


@app.get("/idclassification/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("id-classification.html", {"request": request})


@app.post("/idclassification/")
async def inserting_Image(image_file: UploadFile = File(...)):
    
    content_image = await image_file.read()

    filename = secure_filename(image_file.filename)

    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    # url = {
    # "task": "indianIdCard",
    # "essentials": {
    #     "files": ["https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename
    #         ]
    #     }
    # }

    url = {
        "image": "https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename
    }

    os.remove("./images/"+filename)

    r = requests.post('http://ad26e8808900b4e73adcbd73a6c212ce-613381922.us-west-2.elb.amazonaws.com:8000/idClassification/', data=json.dumps(url))

    res = str(r.json())
    print(res)
    return res


@app.get("/namematch/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("namematch.html", {"request": request})


@app.post("/namematch/")
async def inserting_Image(first: str = Form(...), second: str = Form(...)):
    
    first_name = first
    second_name = second

    url = {
            "firstName": first_name,
            "secondName": second_name
    }

    r = requests.post('http://a9ce7f382cd8a436399fdd6bcf1c7a8e-319198895.us-west-2.elb.amazonaws.com:8000/namematch/predict/', data=json.dumps(url))

    # res = str(r.json())
    # print(type(res))
    # {'Match score': 0.0, 'Match Result': 'No Match', 'Match Reason': 'Names are not Matched'}

    # res = '{"Match name": "wowww"}'
    # return res
    # print(r.json())
    # return r.json()

    d = r.json()

    new_res = dict()
    for i in d:
        temp = i.replace(" ", "")
        new_res[temp] = d[i]

    return str(new_res)


@app.get("/fullcard/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("fullcard.html", {"request": request})


@app.post("/fullcard/")
async def inserting_Image(image_file: UploadFile = File(...)):
    
    content_image = await image_file.read()

    filename = secure_filename(image_file.filename)


    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    url = {"img_url":["https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename], 
            "threshold":70,
            "doc_type":"pan",
            "callback_url":"https://preproduction-persist.signzy.tech/api/files/25329681/download/a63f05b2a4fb4cbea60d81a058dcb13ba430e8dca0e64c8da955158207b92940.jpg"
    }

    os.remove("./images/"+filename)

    r = requests.post('http://a539e755317be4e56b2871c0719eb93e-1686627489.ap-south-1.elb.amazonaws.com:8000/analytics/data/', data=json.dumps(url))

    res = str(r.json())
    return res



@app.get("/xerox/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("xerox.html", {"request": request})


@app.post("/xerox/")
async def inserting_Image(image_file: UploadFile = File(...)):
    
    content_image = await image_file.read()

    filename = secure_filename(image_file.filename)

    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    url = {
            "img_url": ["https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename],
            "threshold": 70
    }

    os.remove("./images/"+filename)

    r = requests.post('https://advforgery.signzy.app/testing/photocopy/', data=json.dumps(url))

    res = str(r.json())
    return res


@app.get("/spoof/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("spoof.html", {"request": request})


@app.post("/spoof/")
async def inserting_Image(image_file: UploadFile = File(...)):
    
    content_image = await image_file.read()

    filename = secure_filename(image_file.filename)


    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    url = {
            "images":["https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename] 
    }

    os.remove("./images/"+filename)

    r = requests.post('http://a8e133dcef2d04152b2b3e72f0f37002-1246984171.ap-south-1.elb.amazonaws.com:8000/analytics/data/', data=json.dumps(url))

    res = str(r.json())
    return res


@app.get("/solar/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("solar.html", {"request": request})


@app.post("/solar/")
async def inserting_Image(image_file: UploadFile = File(...)):
    
    content_image = await image_file.read()

    filename = secure_filename(image_file.filename)


    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    url = {
            "img_url": "https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename
    }

    os.remove("./images/"+filename)

    r = requests.post('http://a3f9f7cbe4b184427804f8ab0b0fb968-1790650436.us-west-2.elb.amazonaws.com:8000/getrooftopedges/', data=json.dumps(url))

    res = str(r.json())
    return res


@app.get("/facematch/", response_class=HTMLResponse)
def write_home(request: Request):
    return templates.TemplateResponse("facematch.html", {"request": request})


@app.post("/facematch/")
async def inserting_Image(image_file: UploadFile = File(...), card: str = Form(...), atm: str = Form(...)):
    
    content_image = await image_file.read()
    cardno = card
    atmid = atm

    filename = secure_filename(image_file.filename)


    image = Image.open(io.BytesIO(content_image))
    image.save("./images/"+filename)

    uploaded = upload_to_aws("./images/"+filename, 'sandbox-em', filename)

    url = {
            "image_from_atm": ["https://sandbox-em.s3.ap-south-1.amazonaws.com/"+filename],
            "cardno": cardno,
            "atmid": atmid,
            "time": str(datetime.datetime.now())
    }

    os.remove("./images/"+filename)

    r = requests.post('http://af935171a51ad4fdea66c8d2f5e12df5-1910570579.us-west-2.elb.amazonaws.com:8000/facematch/', data=json.dumps(url))
    
    res = str(r.json())
    return res


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="debug")

