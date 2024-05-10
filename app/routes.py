"""This module implements the routes for the webserver"""
import logging
import json
import time
from app import webserver
from flask import request, jsonify
from logging.handlers import RotatingFileHandler

#make a logger for this file
logger = logging.getLogger(__name__)
#set the logger level to info
logger.setLevel(logging.INFO)
#set the formatter for the logger
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
#change the time format
formatter.converter = time.gmtime
#make a rotating file handler for the logger
file_handler =RotatingFileHandler("webserver.log", maxBytes=1000000, backupCount=10)
#add the file handler to the logger
logger.addHandler(file_handler)

file_handler.setFormatter(formatter)

# Example endpoint definition
@webserver.route('/api/post_endpoint', methods=['POST'])
def post_endpoint():
    if request.method == 'POST':
        # Assuming the request contains JSON data
        data = request.json
        print(f"got data in post {data}")

        # Process the received data
        # For demonstration purposes, just echoing back the received data
        response = {"message": "Received data successfully", "data": data}

        # Sending back a JSON response
        return jsonify(response)
    else:
        # Method Not Allowed
        return jsonify({"error": "Method not allowed"}), 405

@webserver.route('/api/jobs', methods=['GET'])
def jobs():
    if request.method == 'GET':
        return jsonify({'status': "done", "data": webserver.tasks_runner.fin}), 200

@webserver.route('/api/num_jobs', methods=['GET'])
def num_jobs():
    #log the size of the jobs queue
    logger.info("api/num_jobs returned 'num_jobs': %s", webserver.tasks_runner.jobs.qsize())
    return jsonify({"num_jobs": webserver.tasks_runner.jobs.qsize()}), 200


@webserver.route('/api/graceful_shutdown', methods=['GET'])
def graceful_shutdown():
    #call the shutdown method of the tasks_runner
    webserver.tasks_runner.shutdown()
    #log the response
    logger.info("api/graceful_shutdown returned 'status': 'done'")
    return jsonify({"status": "done"}), 200

@webserver.route('/api/get_results/<job_id>', methods=['GET'])
def get_response(job_id):
    # Check if job_id is in done_jobs
    if webserver.tasks_runner.fin.get(job_id) == None:
        # If not found, return error and log the response
        logger.info("api/get_results/%s returned 'status': 'error', 'reason': 'not found'", job_id)
        return jsonify({"status": "error", "reason": "not found"}), 200

    elif webserver.tasks_runner.fin.get(job_id) == "done":
        # If found, return the result from it's output file
        with open(f"results/{job_id}.json", 'r',  encoding="UTF-8") as file:
            data = json.load(file)
            #log the response
            logger.info("api/get_results/{job_id} returned 'status': 'done', 'data': %s", data)
            return jsonify({"status": "done", "data": data}), 200
    else:
        logger.info("api/get_results/{job_id} returned 'status': 'running'")
        return jsonify({"status": "running"}), 200


@webserver.route('/api/states_mean', methods=['POST'])
def states_mean_request():
    # Get request data
    question = request.json # Get the question from the request
    operation = "states_mean"  #Get the operation for the request
    job_id = webserver.tasks_runner.job_id #Get the job id
    #log the request
    logger.info("api/states/mean Received request: %s", request.json)
    # Create a dictionary with data for the job
    data = {"question": question.get("question"),
            "operation": operation,
            "job_id": "job_id_" + str(job_id)
            }
    # Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    #return the job id
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/state_mean', methods=['POST'])
def state_mean_request():
    req = request.json #get the request
    #log the request
    logger.info("api/state_mean Received request: %s", request.json)
    #set the operation as 'state_mean'
    operation = "state_mean"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    # Create a dictionary with data for the job
    data ={
        "question": req.get("question"),
        "state": req.get("state"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id)
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    #return the job_id
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/best5', methods=['POST'])
def best5_request():
    #Get the request
    req = request.json
    #log the request
    logger.info("api/best5 Received request: %s", req)
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #set the operation as 'best5'
    operation = "best5"
    #get the questions that are best when data is min
    best_is_min = webserver.tasks_runner.data_ingestor.questions_best_is_min
    #get the questions that are best when data is max
    best_is_max = webserver.tasks_runner.data_ingestor.questions_best_is_max

    if req.get("question") in best_is_max:
        direction = "desc" #set the  sorting direction to 'desc'

    if req.get("question") in best_is_min:
        direction = "asc" #set the sorting direction to 'asc'

    #Create a dictionary with data for the job
    data ={
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id),
        "direction": direction
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    #return the job_id
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/worst5', methods=['POST'])
def worst5_request():
    #Get the request
    req = request.json
    #log the request
    logger.info("api/worst5 Received request: %s", req)
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #set the operation as 'worst5'
    operation = "worst5"
    #get the questions that are worst when data is min
    best_is_min = webserver.tasks_runner.data_ingestor.questions_best_is_min
    #get the questions that are worst when data is max
    best_is_max = webserver.tasks_runner.data_ingestor.questions_best_is_max

    if req.get("question") in best_is_max:
        direction = "asc" #set the sorting direction to 'asc'

    if req.get("question") in best_is_min:
        direction = "desc" #set the sorting direction to 'desc'

    #Create a dictionary with data for the job
    data ={
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id),
        "direction": direction
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200

@webserver.route('/api/global_mean', methods=['POST'])
def global_mean_request():
    #log the request
    logger.info("api/global_mean Received request: %s", request.json)
    #get the request
    question = request.json
    #set the operation as 'global_mean'
    operation = "global_mean"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #Create a dictionary with data for the job
    data = {
        "question": question.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id)
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/diff_from_mean', methods=['POST'])
def diff_from_mean_request():
    #log the request
    logger.info("api/diff_from_mean Received request: %s", request.json)
    #get the request
    req = request.json
    #set the operation as 'diff_from_mean'
    operation = "diff_from_mean"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #Create a dictionary with data for the job
    data = {
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id)
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/state_diff_from_mean', methods=['POST'])
def state_diff_from_mean_request():
    #log the request
    logger.info("api/state_diff_from_mean Received request: %s", request.json)
    #get the request
    req = request.json
    #set the operation as 'state_diff_from_mean'
    operation = "state_diff_from_mean"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #Create a dictionary with data for the job
    data = {
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id),
        'state': req.get("state")
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/mean_by_category', methods=['POST'])
def mean_by_category_request():
    #log the request
    logger.info("api/mean_by_category Received request: %s", request.json)
    #get the request
    req = request.json
    #set the operation as 'mean_by_category'
    operation = "mean_by_category"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #Create a dictionary with data for the job
    data = {
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id)
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


@webserver.route('/api/state_mean_by_category', methods=['POST'])
def state_mean_by_category_request():
    #log the request
    logger.info(f"api/state_mean_by_category Received request: {request.json}")
    #get the request
    req = request.json
    #set the operation as 'state_mean_by_category'
    operation = "state_mean_by_category"
    #get the job_id
    job_id = webserver.tasks_runner.job_id
    #Create a dictionary with data for the job
    data = {
        "question": req.get("question"),
        "operation": operation,
        "job_id": "job_id_" + str(job_id),
        'state': req.get("state")
    }
    #Add the job to the jobs queue
    webserver.tasks_runner.add_task(data)
    #log the response
    logger.info("api/states/mean returned 'job_id_%s'", str(webserver.tasks_runner.job_id-1))
    return jsonify({"job_id": "job_id_" + str(webserver.tasks_runner.job_id-1)}), 200


# You can check localhost in your browser to see what this displays
@webserver.route('/')
@webserver.route('/index')
def index():
    routes = get_defined_routes()
    msg = f"Hello, World!\n Interact with the webserver using one of the defined routes:\n"

    # Display each route as a separate HTML <p> tag
    paragraphs = ""
    for route in routes:
        paragraphs += f"<p>{route}</p>"

    msg += paragraphs
    return msg

def get_defined_routes():
    routes = []
    for rule in webserver.url_map.iter_rules():
        methods = ', '.join(rule.methods)
        routes.append(f"Endpoint: \"{rule}\" Methods: \"{methods}\"")
    return routes
