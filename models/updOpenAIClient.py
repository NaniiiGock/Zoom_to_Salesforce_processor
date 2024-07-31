from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from langchain_core.runnables import RunnableSequence
from langchain_community.callbacks.manager import get_openai_callback
from typing import List, Dict, Optional
import json
import time
from openai import OpenAI
import logging
import os
from flask import Flask, request, jsonify
import re

load_dotenv()
BASE_URL_Openai = os.getenv('BASE_URL_Openai')

app = Flask(__name__)

logging.basicConfig(filename='app_logs/api_calls.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SalesforceContactAttributes(BaseModel):
    type: str = Field("Contact", const=True)
    url: str = Field(..., description="The URL of the Contact in Salesforce API")

class SalesforceContact(BaseModel):
    attributes: SalesforceContactAttributes
    Id: Optional[str] = Field(None, description="Salesforce Contact Id")
    AccountName: Optional[str] = Field(None, description="The account that the contact is linked to")
    AllowCustomerPortalSelfRegistration: Optional[bool] = Field(None, description="Allows contacts to self-register for customer portal")
    Assistant: Optional[str] = Field(None, description="The contact's assistant")
    AssistantPhone: Optional[str] = Field(None, description="The assistant's phone number")
    Birthdate: Optional[str] = Field(None, description="The contact's birthday")
    Department: Optional[str] = Field(None, description="The associated business or organizational unit")
    Description: Optional[str] = Field(None, description="The contact's description, you can pass contacts interests during the call here")
    Email: Optional[str] = Field(None, description="The contact's email address")
    EmailOptOut: Optional[bool] = Field(None, description="Whether the contact wants to receive email")
    Fax: Optional[str] = Field(None, description="The contact's fax number")
    FirstName: Optional[str] = Field(None, description="The contact's first name")
    GenderIdentity: Optional[str] = Field(None, description="The contact's gender identity")
    HomePhone: Optional[str] = Field(None, description="The contact's home phone number")
    LastName: str = Field(..., description="The contact's last name")
    LeadSource: Optional[str] = Field(None, description="The record source")
    MailingCity: Optional[str] = Field(None, description="The city in the mailing address")
    MailingCountry: Optional[str] = Field(None, description="The country in the mailing address")
    MailingState: Optional[str] = Field(None, description="The state or province in the mailing address")
    MailingStreet: Optional[str] = Field(None, description="The street in the mailing address")
    MailingPostalCode: Optional[str] = Field(None, description="The zip or postal code in the mailing address")
    MiddleName: Optional[str] = Field(None, description="The contact's middle name")
    MobilePhone: Optional[str] = Field(None, description="The contact's mobile phone number")
    OtherCity: Optional[str] = Field(None, description="The city in another address for the contact")
    OtherCountry: Optional[str] = Field(None, description="The country in another address for the contact")
    OtherState: Optional[str] = Field(None, description="The state or province in another address for the contact")
    OtherStreet: Optional[str] = Field(None, description="The street address in another address for the contact")
    OtherPostalCode: Optional[str] = Field(None, description="The zip or postal code in another address for the contact")
    OtherPhone: Optional[str] = Field(None, description="Another phone number for the contact")
    Phone: Optional[str] = Field(None, description="The contact's primary phone number")
    Pronouns: Optional[str] = Field(None, description="The contact's personal pronouns")
    ReportsTo: Optional[str] = Field(None, description="The name of the contact's manager")
    Salutation: Optional[str] = Field(None, description="The title for addressing the contact")
    Suffix: Optional[str] = Field(None, description="The suffix in the contact's name")
    Title: Optional[str] = Field(None, description="The contact's position within his organization, e.g. CEO")

class MeetingAnalysis(BaseModel):
    contacts: List[SalesforceContact] = Field(..., description="List of Salesforce contacts extracted from the meeting")

class APICallDetails(BaseModel):
    total_tokens: int = Field(..., description="Total number of tokens used in the API call")
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_cost: float = Field(..., description="Total cost of the API call in USD")
    total_time: float = Field(..., description="Total time taken for the API call")
    tokens_per_second: float = Field(..., description="Tokens processed per second")
    cost_per_token: float = Field(..., description="Cost per token")

class AnalysisResult(BaseModel):
    meeting_analysis: MeetingAnalysis = Field(..., description="Analysis of the meeting")
    api_call_details: APICallDetails = Field(..., description="Details of the API call")

def chunk_text(text: str, chunk_size: int = 4000) -> List[str]:
    return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

def parse_webvtt(vtt_content: str) -> str:
    lines = vtt_content.split('\n')
    content_lines = [line for line in lines if line.strip() and not line.strip().isdigit() and '-->' not in line]
    return ' '.join(content_lines)


def analyze_meeting(transcript: str, meeting_details: str, existing_contacts: List[Dict]) -> AnalysisResult:
    client = OpenAI(api_key=os.getenv('OPENAI_API_KEY'))
    
    function_schema = {
        "name": "extract_contact_info",
        "description": "Extract contact information from the meeting transcript and details",
        "parameters": {
            "type": "object",
            "properties": {
                "contacts": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "properties": {
                            "FirstName": {"type": "string"},
                            "LastName": {"type": "string"},
                            "Email": {"type": "string"},
                            "Phone": {"type": "string"},
                            "MobilePhone": {"type": "string"},
                            "Title": {"type": "string"},
                            "AccountName": {"type": "string"},
                            "Department": {"type": "string"},
                            "MailingStreet": {"type": "string"},
                            "MailingCity": {"type": "string"},
                            "MailingState": {"type": "string"},
                            "MailingPostalCode": {"type": "string"},
                            "MailingCountry": {"type": "string"},
                            "Description": {"type": "string"},
                            "LeadSource": {"type": "string"}
                        },
                        "required": ["LastName"]
                    }
                }
            },
            "required": ["contacts"]
        }
    }

    system_prompt = """
    You are an AI assistant specialized in analyzing meeting transcripts and extracting relevant information 
    for Salesforce contact records. Your task is to carefully review the provided meeting transcript and details, 
    and extract or update information about all participants that could be used to create or update Salesforce contact records. 
    Pay special attention to new information or changes in existing contact details.
    """

    transcript_chunks = chunk_text(parse_webvtt(transcript))
    all_contacts_data = {}
    total_tokens = 0
    total_cost = 0
    start_time = time.time()

    try:
        for chunk in transcript_chunks:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": f"Analyze the following meeting transcript chunk and details:\n\nTranscript Chunk: {chunk}\n\nMeeting Details: {meeting_details}\n\nExisting Contacts: {json.dumps(existing_contacts)}"}
            ]

            response = client.chat.completions.create(
                model="gpt-4",
                messages=messages,
                functions=[function_schema],
                function_call={"name": "extract_contact_info"}
            )

            result = json.loads(response.choices[0].message.function_call.arguments)

            if not isinstance(result, dict) or 'contacts' not in result or not isinstance(result['contacts'], list):
                raise ValueError("Invalid response format from OpenAI")

            for contact in result['contacts']:
                email = contact.get('Email', '').lower()
                if email in all_contacts_data:
                    all_contacts_data[email] = {**all_contacts_data[email], **contact}
                else:
                    all_contacts_data[email] = contact

            total_tokens += response.usage.total_tokens
            total_cost += (response.usage.prompt_tokens * 0.03 + response.usage.completion_tokens * 0.06) / 1000  # Adjust pricing as needed

        salesforce_contacts = []
        for contact_data in all_contacts_data.values():
            existing_contact = next((contact for contact in existing_contacts if contact['Email'].lower() == contact_data.get('Email', '').lower()), None)
            
            salesforce_contact = SalesforceContact(
                attributes=SalesforceContactAttributes(
                    type="Contact",
                    url=f"/services/data/v52.0/sobjects/Contact/{existing_contact['Id'] if existing_contact else '[NEW]'}"
                ),
                Id=existing_contact['Id'] if existing_contact else None,
                **{k: v for k, v in contact_data.items() if k in SalesforceContact.__fields__ and v is not None}
            )
            salesforce_contacts.append(salesforce_contact)

        meeting_analysis = MeetingAnalysis(contacts=salesforce_contacts)

        total_time = time.time() - start_time
        api_call_details = APICallDetails(
            total_tokens=total_tokens,
            prompt_tokens=0,
            completion_tokens=0,
            total_cost=total_cost,
            total_time=total_time,
            tokens_per_second=total_tokens / total_time if total_time > 0 else 0,
            cost_per_token=total_cost / total_tokens if total_tokens > 0 else 0
        )

        return AnalysisResult(
            meeting_analysis=meeting_analysis,
            api_call_details=api_call_details
        )

    except Exception as e:
        logger.error(f"An unexpected error occurred: {str(e)}")
        raise
    
# @app.route('/process', methods=['POST'])
# def process():
#     data = request.get_json()

#     required_fields = ['webvtt_file', 'zoom_json_file', 'participants']
#     if not all(field in data for field in required_fields):
#         return jsonify({'message': 'Missing required fields!'}), 400
    
#     webvtt_file = data['webvtt_file']
#     zoom_json_file = data['zoom_json_file']
#     participants = data['participants']

#     try:
#         with open(webvtt_file, 'r') as f:
#             transcript = f.read()

#         with open(zoom_json_file, 'r') as f:
#             meeting_details = f.read()

#         result = analyze_meeting(transcript, meeting_details, participants)
    
#         updated_contacts = [contact.dict(exclude_unset=True) for contact in result.meeting_analysis.contacts]
#         call_data = result.api_call_details.dict()
        
#         logger.info(f"Processed meeting data from {webvtt_file} and {zoom_json_file}")
#         logger.info(f"API Call Details: {json.dumps(call_data)}")
        
#         response = {
#             "updated_contacts": updated_contacts,
#             "call_data": call_data
#         }

#         return jsonify(response)

#     except FileNotFoundError as e:
#         logger.error(f"File not found: {e}")
#         return jsonify({'message': 'File not found!'}), 404
#     except json.JSONDecodeError as e:
#         logger.error(f"JSON decoding error: {e}")
#         return jsonify({'message': 'Invalid JSON in input files!'}), 400
#     except Exception as e:
#         logger.error(f"An unexpected error occurred: {e}")
#         return jsonify({'message': 'An unexpected error occurred!'}), 500

# if __name__ == "__main__":
#     app.run(port=int(BASE_URL_Openai[-4:]), host='localhost')
