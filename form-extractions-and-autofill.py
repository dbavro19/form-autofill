import streamlit as st
import pandas
import json
import boto3
import datetime

### Title displayed on the Streamlit Web App
st.set_page_config(page_title="Form Extraction", page_icon=":tada", layout="wide")


#Header and Subheader dsiplayed in the Web App
with st.container():
    st.header("Extract Form Data")
    st.subheader("")
    st.title("Form AutoFill")

def upload_to_s3(file_name, object_name):
    bucket="dbavaro-landing-bucket"


    s3 =boto3.client('s3')
    response = s3.upload_fileobj(file_name, bucket, object_name)

    return object_name

def upload_file(file):
    object_name = upload_to_s3(file, file.name)
    return object_name
    

def get_metadata_from_bedrock_claude(file):

    #Setup bedrock client
    bedrock = boto3.client('bedrock-runtime' , 'us-east-1', endpoint_url='https://bedrock-runtime.us-east-1.amazonaws.com')
    
    filename = file.name

    if ".csv" in filename:
        #convert csv to pandas dataframe
        df = pandas.read_csv(file)
    elif ".xls" in filename:
        df=pandas.read_excel(file)
    
    print(df)

    date = datetime.datetime.now()
    date2=date.strftime('%Y-%m-%d')
    print(date2)

    prompt_data = f"""

Human:

You are an AI assitant that will help our company Vault Insurance categorize and help fill out  questionnaire's
Extract the following information from the provided document:
    Date 
    Customer Prepared for
    Document Type

The docuement type should be one of the provided in <valid_doc_types>
###
<Document>
{df}
</Document>
###
<filename>
{filename}
</filename>
###
<valid_doc_types>
Completed  Questionnaire
Uncompleted Questionnaire
Internal Documentation
Undefined (use this if unsure)
</valid_doc_types>
###

To be a valid Doc Type of "Completed Questionnaire" Should have questions AND answers, "Uncompleted Questionnaire" will only have questions, not answers
If no was provided use {date}
Provide only the Filename, Date (in MM/DD/YYYY format), Document Type, and "Customer Prepared for".
Provide the output in in JSON Format

###
<example_output>
{{"filename":"filename", "date":"MM/DD/YYYY", "DocType":"DocumentType",  "customer":"Customer"}}
</example_output>

Assistant:

"""
    body = json.dumps({"prompt": prompt_data,
                 "max_tokens_to_sample":5000,
                 "temperature":.2,
                 "stop_sequences":[]
                  }) 
    
    #Run Inference
    modelId = "anthropic.claude-instant-v1"  # change this to use a different version from the model provider if you want to switch 
    accept = "application/json"
    contentType = "application/json"
    #Call the Bedrock API
    response = bedrock.invoke_model(
        body=body, modelId=modelId, accept=accept, contentType=contentType
    )

    #Parse the Response
    response_body = json.loads(response.get('body').read())
    llmOutput=response_body.get('completion')

    print(llmOutput)

    #Return the LLM response
    return llmOutput


#Upload Audio File
uploaded_file = st.file_uploader("Choose a file")



result=st.button("Upload File and Get Metadata")
if result:
    filename= uploaded_file
    metadata=get_metadata_from_bedrock_claude(filename)
    #st.write(metadata)
    json_md=json.loads(metadata)
    st.write(json_md)
    for key in json_md:
        value = json_md[key]
        st.text_input(key,value)