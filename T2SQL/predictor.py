import os
import re
import boto3
import json
import logging
import subprocess
import pandas as pd
from dotenv import load_dotenv
from datetime import datetime, timezone
from flask import Flask, request, jsonify
# Custom libraries
from preprocess import *
from rag import load_or_ingest
from prompt_generation import generate_prompt
from sql_generator import SQLGenerator
from text_replacer import format_criteria
from sql_processor import SQLProcessor
from secret_manager import create_dotenv

#Create enviroment varibales
create_dotenv()
# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


prefix = '/opt/ml/'
model_path = os.path.join(prefix, 'model')
logging.info("Model Path" + str(model_path))

# Initialize Flask app
app = Flask(__name__)

# Initialize SQLGenerator
os.environ["SSL_CERT_FILE"]="root.pem"
BASE_URL=os.environ["BASE_URL"] 
OPENAI_API_KEY=os.environ["OPENAI_API_KEY"]

if not OPENAI_API_KEY:
    raise ValueError("OPENAI_API_KEY environment variable not set")
    
sql_generator = SQLGenerator(base_url=BASE_URL,api_key=OPENAI_API_KEY)

def T2SQL(query, sql_generator, index_name='table_info', k=50, data_frame=None):
    """
    Generate a SQL query based on the user's query using the provided SQL generator.

    :param query: The user's query.
    :param sql_generator: An instance of the SQLGenerator class.
    :param index_name: The name of the index to use for document retrieval.
    :param k: The number of documents to retrieve.
    :param data_frame: DataFrame for ingestion.
    :return: The generated SQL query.
    """
    try:
        # Load or ingest the index
        RAG = load_or_ingest(index_name=index_name, data_frame=data_frame)

        processed_criteria = process_criteria(query)
        print("preprocessed criteria : ",processed_criteria)
        processed_query  = ";".join(processed_criteria.keys())

        # Search for relevant documents
        docs = RAG.search_documents(query=processed_query, k=k, index_name=index_name)

        # Generate the prompt
        prompt = generate_prompt(rag_output_docs=docs, user_question=query, config_file='config.json')

        # Generate the SQL query
        sql_query = sql_generator.generate_response(prompt)

        return sql_query

    except Exception as e:
        logger.error(f"Error in T2SQL function: {e}")
        return f"Error in T2SQL function: {e}"
def upsert_record_in_metric_table(table_name, region_name, input_token_count, output_token_count):
    ddb_tbl_res = boto3.resource('dynamodb', region_name=region_name).Table(table_name)

    current_date = datetime.now(timezone.utc).strftime("%Y-%m-%d")
    # Check if entry already exists in DynamoDB
    ddb_resp = ddb_tbl_res.get_item(Key={"entityType": "CA_gpt-4o-0513", "createdDate": current_date}).get("Item", {})
    if ddb_resp:
        ddb_tbl_res.update_item(Key={"entityType": "CA_gpt-4o-0513", "createdDate": current_date},
                                UpdateExpression="SET apiCount = :val1, inputTokenCount = :val2, outputTokenCount = :val3, totalTokenCount = :val4",
                                ExpressionAttributeValues={
                                    ":val1": ddb_resp.get("apiCount") + 1,
                                    ":val2": ddb_resp.get("inputTokenCount") + input_token_count,
                                    ":val3": ddb_resp.get("outputTokenCount") + output_token_count,
                                    ":val4": ddb_resp.get("totalTokenCount") + input_token_count + output_token_count,
                                })
        logger.info("Updated API Token Counts in DynamoDB")
    else:
        ddb_tbl_res.put_item(Item={"entityType": "CA_gpt-4o-0513", "createdDate": current_date, "apiCount": 1,
                                   "inputTokenCount": input_token_count, "outputTokenCount": output_token_count,
                                   "totalTokenCount": input_token_count + output_token_count})
        logger.info("Added API Token Counts in DynamoDB")
    return "SUCCESS"

def upsert_record_in_session_table(table_name, region_name, user_id, request_time,ticketId,
                                   sql_query,status,comments,report_s3_file_path="snowflakeReport"):
    report_s3_file_path = f"{report_s3_file_path}/{ticketId}_{request_time}.csv" if status=='SUCCESS' and ticketId else "" 
    ddb_tbl_res = boto3.resource('dynamodb', region_name=region_name).Table(table_name)
    ddb_tbl_res.update_item(Key={"userId": user_id, "createdTimestamp": request_time},
                            UpdateExpression="SET claimRequestStatus = :val1, claimRequestOutput = :val2",
                            ExpressionAttributeValues={
                                ":val1": status.upper(),
                                ":val2": {"report_file_path": report_s3_file_path,
                                          "sql_query": sql_query,"comments":comments}})
    logger.info("Updated session table with sql query in DynamoDB")
    return "SUCCESS"

def copy_index_files(source_folder, destination_folder,static_folder='.ragatouille'):
    
    source_path = os.path.join(source_folder, static_folder)
    destination_path = os.path.join(destination_folder, static_folder)

    # Construct the AWS CLI command
    command = [
            'aws', 's3', 'cp',
            source_path,
            destination_path,
            '--recursive'
             ]

    # Run the command
    try:
        result = subprocess.run(command, capture_output=True, text=True, check=True)
        logger.info(f"Copying index files from {source_path} to {destination_path} successful!")
    except subprocess.CalledProcessError as e:
        logger.info(f"Error occurred while copying index files from {source_path} to {destination_path}:")
        return e.stderr  # Return error message from the command

@app.after_request
def add_security_headers(response):
    """Apply security headers to the response."""
    # Apply HSTS
    response.headers['Strict-Transport-Security'] = 'max-age=63072000; includeSubDomains; preload'
    return response

@app.route('/ping', methods=['GET'])
def ping():
    try:
        status = 200
        logging.info("Status : 200")
    except:
        status = 400
    return jsonify(response=json.dumps(' '), status=status, mimetype='application/json')

@app.route('/invocations', methods=['POST'])
def transformation():
    """
    Endpoint to generate SQL query from user query.

    :return: JSON response containing the generated SQL query.
    """
    #Input fields to update metric tables
    user_id = None
    insightTbl = None
    sessionTbl = None
    region_name = None
    request_time = None
    ticketId = ""
    claim_criteria = None
    sql_query = ""
    status = "FAILED"
    try:
        input_json = request.get_json()
        if not input_json:
            return jsonify({"error": "Input JSON is required"}), 400

        if 'Records' in input_json:
            # Handle S3 put event
            s3_event = input_json['Records'][0]['s3']
            bucket_name = s3_event['bucket']['name']
            key = s3_event['object']['key']
            
            #Input fields to update metric tables
            input_json = input_json['Records'][0]
            user_id = input_json.get('user_id',None)
            sessionTbl = input_json.get('sessionTbl',None)
            region_name = input_json.get('regionNm',None)
            request_time = input_json.get('request_time',None)
            
            # Read the CSV file from S3
            s3 = boto3.client('s3')
            obj = s3.get_object(Bucket=bucket_name, Key=key)
            data_frame = pd.read_csv(obj['Body'])

            # Perform ingestion
            load_or_ingest(index_name='table_info', data_frame=data_frame)
            
            # copy index files from local to s3
            copy_index_files(".",f"s3://{bucket_name}/mapping_index/")
            
            status = "SUCCESS"
            comments = 'Index created successfully'
            upsert_record_in_session_table(sessionTbl,region_name, user_id,request_time,ticketId,sql_query,status,comments)
            
            return jsonify({"status":status,'message': comments})
        else:
            # Concatinate claim id with criteria
            if input_json.get('claim_id',""):
               input_json.update({"claim_criteria":"claim_number : "+str(input_json['claim_id'])+"; "+str(input_json['claim_criteria'])})
            input_json.update({"claim_criteria":input_json.get('claim_criteria').replace("=",":")+";"})
            # Handle query input
            query = input_json.get('claim_criteria')
            if not query:
                return jsonify({"status":400,"error": "claim_criteria parameter is required"})
            print(query)
            
            #Input fields to update metric tables
            user_id = input_json['user_id']
            insightTbl = input_json['insightTbl']
            sessionTbl = input_json['sessionTbl']
            region_name = input_json['regionNm']
            request_time = input_json['request_time']
            ticketId = input_json['ticket_id']
            claim_criteria = input_json['claim_criteria']
            replace_dict = input_json.get('replace_dict','')
            
            # copy index files from s3 to local
            copy_index_files(f"s3://{input_json.get('clmBucket','')}/mapping_index/",".")
            
            # Format User Criteria
            formed_query = format_criteria(query)
            print(formed_query)

            # Generate LLM reponse
            reponse = T2SQL(formed_query, sql_generator)
                                    
            input_token_count = reponse['input_token_count']
            output_token_count = reponse['output_token_count']
            sql_query = reponse['sql_query']
            
            modified_query = sql_query

            # Only perform replacement if replace_dict is not empty
            if replace_dict:
                # Create a regular expression pattern
                pattern = re.compile("|".join(re.escape(key) for key in replace_dict.keys()))

                # Define a function to use in re.sub
                def replace_match(match):
                    return replace_dict[match.group(0)]

                # Replace using re.sub with the compiled pattern
                modified_query = pattern.sub(replace_match, modified_query)
                
            print("\nmodified sql query:\n",sql_query)
            # update LLM reponse in input event
            input_json.update(reponse)

            # Update Insights table 
            upsert_record_in_metric_table(insightTbl,region_name,input_token_count,output_token_count)
            
            # Perform postprocess on SQL Query
            sql_processor = SQLProcessor(input_json)
            status,comments = sql_processor.process_query(modified_query)
            # Update Session Table with input criteria and LLM Response
            upsert_record_in_session_table(sessionTbl,region_name, user_id,request_time,ticketId,sql_query,status,comments)

            return jsonify(input_json)
            # return jsonify({"Status" : 200,"Message":"Query processed and report generated sucessfully"})

    except Exception as e:
        logger.error(f"Error in /invocations endpoint: {e}")
        comments = f"An error occurred while processing the request : {e}"
        upsert_record_in_session_table(sessionTbl,region_name, user_id,request_time,ticketId,sql_query,status,comments)
        return jsonify({"status":500,"error": comments})

if __name__ == '__main__':
    app.run(host="0.0.0.0", port=8080, debug=False)