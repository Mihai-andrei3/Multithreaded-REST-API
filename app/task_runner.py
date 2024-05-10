"""This module implements the threadpool used in processing the requests from webserver"""
from queue import Queue
from threading import Thread, Event
from logging.handlers import RotatingFileHandler
import time
import os
import json
import logging

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s:%(name)s:%(message)s')
formatter.converter = time.gmtime

file_handler =RotatingFileHandler("webserver.log", maxBytes=1000000, backupCount=10)
logger.addHandler(file_handler)

file_handler.setFormatter(formatter)

class ThreadPool:
    """Class that implements a thread pool"""

    def __init__(self,data_ingestor):
        """Constructor for the ThreadPool class"""
        self.data_ingestor = data_ingestor #initialize the data ingestor
        self.fin = {} #initialize the dictionary for finished jobs
        self.job_id = 1 #intialize the job counter
        self.jobs = Queue() #initialize the queue for jobs
        self.graceful_shutdown = Event() #initialize the event for graceful shutdown

        if os.getenv('TP_NUM_OF_THREADS'): #check if the environment variable is defined
            self.threads_number = os.getenv('TP_NUM_OF_THREADS')
        else: #if not defined
            self.threads_number=  os.cpu_count() #get the number of threads

        self.threads = [] #initialize the list for threads

        #create the threads and start them
        for i in range(self.threads_number):
            thread = TaskRunner(self, self.fin)
            thread.start()
            self.threads.append(thread) #add thread to the list

    def add_task(self, job):
        """Method to add a task to the queue"""

        if self.graceful_shutdown.is_set(): #don t accept new tasks if the shutdown event is set
            return
        self.jobs.put(job) #add task to the queue
        self.job_id += 1 #increment job id
        self.fin.update({job.get("job_id"): "running"}) #add job to the dictionary of finished jobs

    def shutdown(self):
        """Method to shutdown the thread pool"""

        #send a shutdown job to each thread
        shutdown_job = {"operation": "shutdown"}
        for i in range(self.threads_number):
            self.jobs.put(shutdown_job)

        #set the shutdown event and wait for the threads to finish
        self.graceful_shutdown.set()
        for i in range(self.threads_number):
            self.threads[i].join()


class TaskRunner(Thread):
    """Class that implements a thread that executes a job from the queue"""

    def __init__(self, thread_pool, fin):
        """Constructor for the TaskRunner class"""

        super().__init__() #call the constructor of the parent class
        self.job = None #initialize the job as None
        self.thread_pool = thread_pool #pass the thread pool to the thread
        self.graceful_shutdown = thread_pool.graceful_shutdown #pass the shutdown event
        self.fin = fin #pass the dictionary for finished jobs

    def run(self):
        """Method that runs the thread"""

        while True: #run the thread in a loop
            #get a job from the queue
            self.job = self.thread_pool.jobs.get()
            #execute the job
            self._execute_job(self.job)
            #break the loop if the shutdown event is set
            if self.graceful_shutdown.is_set():
                break

    def _execute_job(self, job):
        """Method that executes a job"""

        job_id = job.get('job_id') #get the job id
        results_dir = "results/" #define the directory for the results

        # Create the directory if it doesn't exist
        os.makedirs(results_dir, exist_ok=True)

        # Open the output file for the job
        file = open(f"{results_dir}/{job_id}.json", "a", encoding="utf-8")
        result = None

        #Check the operation of the job and execute the corresponding method

        if job.get("operation") == "state_mean":
            result = self._state_mean_request(job)
            data = {str(job.get("state")): result}
            json.dump(data, file)

        elif job.get("operation") == "states_mean":
            result = self._states_mean_request(job)
            json.dump(result, file)

        elif job.get("operation") == "best5":
            result = self._best5_request(job)
            json.dump(result, file)

        elif job.get("operation") == "worst5":
            result = self._best5_request(job)
            json.dump(result, file)

        elif job.get("operation") == "global_mean":
            result = self._global_mean_request(job)
            data = {"global_mean": result}
            json.dump(data, file)

        elif job.get("operation") == "state_diff_from_mean":
            result = self._state_diff_from_mean_request(job)
            json.dump(result,file)

        elif job.get("operation") == "diff_from_mean":
            result = self._diff_from_mean_request(job)
            json.dump(result, file)

        elif job.get("operation") == "state_mean_by_category":
            result = self._state_mean_by_category(job)
            json.dump(result, file)

        elif job.get("operation") == "mean_by_category":
            result = self._mean_by_category_request(job)
            json.dump(result, file)

        elif job.get("operation") == "shutdown":
            file.close()
            return

        file.close()
        #add the job to the list of done jobs
        status = "done"
        self.fin.update({job_id: status})
        #reinitialize the job
        self.job = None


    def _state_mean_request(self,job):
        #log the parameters of the method
        logger.info("Executing state_mean_request with job: %s", job)
        #get the entries for the state
        state_entries = self.thread_pool.data_ingestor.state_entries(job.get("state"))
        #initialize the sum and count as 0
        data_sum = 0
        count = 0
        #iterate through the entries
        for i in range(len(state_entries)):
            if state_entries[i].get("Question") == job.get("question"):
                #add the value to the sum and increment the count
                data_sum += float(state_entries[i].get("Data_Value"))
                count += 1.0
        if count == 0:
            return 0 #return 0 if there are no entries

        #log the result of the method
        logger.info("state_mean_request result: %s", data_sum/count)

        #return the mean
        return data_sum/count

    def _states_mean_request(self,job):
        #log the parameters of the method
        logger.info("Executing states_mean_request with job: %s", job)
        #get the list of states
        states = self.thread_pool.data_ingestor.list_of_states
        #initialize the job as a copy
        job_aux = job.copy()
        #initialize the result list as an empty dictionary
        result_list = {}
        #iterate through the states
        for key in states:
            job_aux.update({"state": key}) #add the state to the job
            if self._state_mean_request(job_aux) != 0: #check if the mean is not 0
                #add the state and the mean to the result list
                result_list.update({key: self._state_mean_request(job_aux)})

        #sort the result list by the values
        sorted_list = sorted(result_list.items(), key=lambda x:x[1])
        #convert the sorted list to a dictionary
        result = dict(sorted_list)
        #log the result of the method
        logger.info("states_mean_request result: %s", result)
        return result

    def _best5_request(self,job):
        #log the parameters of the method
        logger.info("Executing best5_request with job: %s", job)
        #get the list for the mean of the states
        states_mean = self._states_mean_request(job)
        #check the sorting direction
        if job.get('direction') == 'asc': #if ascending
            #get the first 5 states and log the result
            logger.info("best5_request result: %s", dict(list(states_mean.items())[0:5]))
            return dict(list(states_mean.items())[0:5])

        #if descending, revert the list and get the first 5 states
        sorted_list = sorted(states_mean.items(), key=lambda x:x[1], reverse=True)
        logger.info("best5_request result: %s", dict(sorted_list[0:5]))
        return dict(sorted_list[0:5])

    def _worst5_request(self,job):
        #log the parameters of the method
        logger.info("Executing worst5_request with job: %s", job)
        #get the list for the mean of the states
        states_mean = self._states_mean_request(job)
        #check the sorting direction
        if job.get('direction') == 'asc': #if ascending
            #sort the list and get the first 5 states
            logger.info("worst5_request result: %s", dict(list(states_mean.items())[0:5]))
            return dict(list(states_mean.items())[0:5])

        #if descending, revert the list and get the first 5 states
        sorted_list = sorted(states_mean.items(), key=lambda x:x[1], reverse=True)
        logger.info("worst5_request result: %s", dict(sorted_list[0:5]))
        return dict(sorted_list[0:5])

    def _global_mean_request(self,job):
        #log the parameters of the method
        logger.info("Executing global_mean_request with job: %s", job)
        #initialize the sum and count as 0
        data_sum = 0
        count = 0
        #get the list of states
        states = self.thread_pool.data_ingestor.list_of_states
        #initialize the job as a copy
        job_aux = job.copy()
        #iterate through the states
        for key in states:
            #add the state to the job
            job_aux.update({"state": key})
            #get the entries for the state
            state_entries = self.thread_pool.data_ingestor.state_entries(key)
            #iterate through the entries
            for i in range(len(state_entries)):
                #check if the entry question is the same as the job question
                if state_entries[i].get("Question") == job.get("question"):
                    #add the value to the sum and increment the count
                    data_sum += float(state_entries[i].get("Data_Value"))
                    count += 1.0
            #reinitialize the state entries
            state_entries.clear()

        #Log the result of the method
        logger.info("global_mean_request result: %s", data_sum/count)
        return data_sum/count

    def _state_diff_from_mean_request(self,job):
        #log the parameters of the method
        logger.info("Executing state_diff_from_mean_request with job: %s", job)
        #calculate the global mean
        global_mean = self._global_mean_request(job)
        #calculate the state mean
        state_mean = self._state_mean_request(job)
        #initialize the result as an empty dictionary
        result = {}
        #add the state and the difference from the global mean to the result
        result.update({job.get("state"): global_mean - state_mean})
        #log the result of the method
        logger.info("state_diff_from_mean_request result: %s", result)
        return result

    def _diff_from_mean_request(self,job):
        #log the parameters of the method
        logger.info("Executing diff_from_mean_request with job: %s", job)
        #calculate the global mean
        global_mean = self._global_mean_request(job)
        #get the list of states
        states = self.thread_pool.data_ingestor.list_of_states
        #initialize the job as a copy
        job_aux = job.copy()
        #initialize the result as an empty dictionary
        result_list = {}
        #iterate through the states
        for key in states:
            #add the state to the job
            job_aux.update({"state": key})
            #calculate the state mean
            state_mean = self._state_mean_request(job_aux)
            #add the state and the difference from the global mean to the result
            if state_mean != 0:
                result_list.update({str(key): global_mean - state_mean})

        #log the result of the method
        logger.info("diff_from_mean_request result: %s", result_list)
        return result_list

    def _get_category_entries(self, job, category):
        #log the parameters of the method
        logger.info("Executing get_category_entries with job: %s and category %s", job, category)
        #get the entries for the state
        state_entries = self.thread_pool.data_ingestor.state_entries(job.get("state"))
        #initialize the list of values of the category
        values = []
        #iterate through the entries
        for i in range(len(state_entries)):
            #store the question and the stratification category
            question = state_entries[i].get("Question")
            stratification_category = state_entries[i].get("StratificationCategory1")
            #check if the question and the stratification category
            # are the same as the job question and category
            if(question == job.get("question") and stratification_category== category):
                #add the entry to the list of values
                values.append(state_entries[i])

        #log the result of the method
        logger.info("get_category_entries result: %s", values)
        return values

    def _get_category_stratification(self, category_entries):
        #log the parameters of the method
        logger.info("Executing get_category_stratification with category_entries: %s", category_entries)
        #initialize the result as an empty set
        result = set()
        #iterate through the category entries
        for i in range(len(category_entries)):
            #add the stratification category to the result set
            result.add(category_entries[i].get("Stratification1"))

        #log the result of the method
        logger.info("get_category_stratification result: %s", result)
        return result

    def _mean_by_category(self,job,category):
        #log the parameters of the method
        logger.info("Executing mean_by_category with job: %s", job)
        #get the entries for the category
        category_entries = self._get_category_entries(job, category)
        #get the stratification categories
        sub_categories = self._get_category_stratification(category_entries)
        #initialize the result as an empty dictionary
        result = {}
        #iterate through the stratification categories
        for category in sub_categories:
            #initialize the sum and count as 0
            data_sum = 0
            count = 0
            #iterate through the category entries
            for i in range(len(category_entries)):
                #check if the stratification category is the same as the category
                if category_entries[i].get("Stratification1") == category:
                    #add the value to the sum and increment the count
                    data_sum += float(category_entries[i].get("Data_Value"))
                    count += 1.0
            if count == 0:
                result.update({category: 0}) #add 0 to the result if there are no entries
            else:
                result.update({category: data_sum/count}) #add the category and it's mean to the result

        #log the result of the method
        logger.info("mean_by_category result: %s", result)
        return result

    def _get_all_categories(self,job):
        #log the parameters of the method
        logger.info("Executing get_all_categories with job: %s", job)
        #get the entries for the state
        state_entries = self.thread_pool.data_ingestor.state_entries(job.get("state"))
        #initialize the result as an empty set
        result = set()
        #iterate through the entries
        for i in range(len(state_entries)):
            #check if the question is the same as the job question
            if state_entries[i].get("Question") == job.get("question"):
                #add the category to the result set
                if state_entries[i].get("StratificationCategory1") != "":
                    #add the category to the result set
                    result.add(state_entries[i].get("StratificationCategory1"))

        return result

    def _state_mean_by_category(self,job):
        #log the parameters of the method
        logger.info("Executing state_mean_by_category with job: %s", job)
        #get all the categories for the state
        categories = self._get_all_categories(job)
        categories_mean = { }
        #iterate through the categories
        for category in categories:
            #add the category and it's mean to the result
            categories_mean.update({category: self._mean_by_category(job, category)})

        #sort the result by the keys
        categories_mean = dict(sorted(categories_mean.items()))
        result = {}
        #iterate through the categories 
        for key in categories_mean:
            #iterate through the stratification categories
            for second_key in categories_mean[key]:
                #add the category, stratification category and it's mean to the result
                dict_key = '(\'' + str(key) +'\'' + ', ' + '\'' + str(second_key) + '\')'
                result.update({dict_key: categories_mean[key][second_key]})

        #log the result of the method
        logger.info("state_mean_by_category result: %s", result)
        return {job.get("state"): result}

    def _state_mean_by_category_aux(self,job):
        #method to calculate the mean by category for a state
        #used in the mean_by_category method
        categories = self._get_all_categories(job)
        categories_mean = { }
        for category in categories:
            categories_mean.update({category: self._mean_by_category(job, category)})
        result = {}
        for key in categories_mean:
            for second_key in categories_mean[key]:
                result.update({(key, second_key): categories_mean[key][second_key]})

        return {job.get("state"): result}

    def _mean_by_category_request(self,job):
        #log the parameters of the method
        logger.info("Executing mean_by_category_request with job: %s", job)
        #get the list of states
        states = self.thread_pool.data_ingestor.list_of_states
        #initialize the job as a copy
        job_aux = job.copy()
        #initialize the result list as an empty dictionary
        result_list = {}
        #iterate through the states
        for key in states:
            #add the state to the job
            job_aux.update({"state": key})
            #add the state and the mean by category to the result list
            result_list.update({key: self._state_mean_by_category_aux(job_aux)})

        result = {}
        #iterate through the states in the result list
        for key in result_list:
            #iterate through the categories
            for second_key in result_list[key]:
                #iterate through the stratification categories
                for third_key in result_list[key][second_key]:
                    #form the key for the dictionary with 
                    #state, category and stratification category
                    dict_key = '(\'' + str(second_key) +'\'' + ', '
                    dict_key += '\'' + str(third_key[0]) + '\'' + ', ' + '\''
                    dict_key += str(third_key[1]) +'\')'
                    #add the key and the mean to the result
                    result.update({dict_key: result_list[key][second_key][third_key]})

        #sort the result by the keys
        result = dict(sorted(result.items()))
        #log the result of the method
        logger.info("mean_by_category_request result: %s", result)
        return result
