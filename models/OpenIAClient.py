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
import logging
import os
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import jwt
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import re
from flask import Flask, request, jsonify
import os

load_dotenv()
BASE_URL_Openai = os.getenv('BASE_URL_Openai')


app = Flask(__name__)
# app.config['JWT_EXPIRATION_DELTA'] = timedelta(hours=1)
# app.config['SECRET_KEY'] = os.getenv['SECRET_KEY']


limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour"]
)

users = {}

# def token_required(f):
#     @wraps(f)
#     def decorated(*args, **kwargs):
#         token = request.headers.get('Authorization')
#         if not token:
#             return jsonify({'message': 'Token is missing!'}), 401
#         try:
#             data = jwt.decode(token, app.config['SECRET_KEY'], algorithms=["HS256"])
#             current_user = users.get(data['username'])
#         except:
#             return jsonify({'message': 'Token is invalid!'}), 401
#         return f(current_user, *args, **kwargs)
#     return decorated



logging.basicConfig(filename='app_logs/api_calls.log', level=logging.INFO,
                    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class Address(BaseModel):
    street: Optional[str] = Field(None, description="Street address")
    city: Optional[str] = Field(None, description="City")
    state: Optional[str] = Field(None, description="State or province")
    postalCode: Optional[str] = Field(None, description="Postal code")
    country: Optional[str] = Field(None, description="Country")

class SalesforceContact(BaseModel):
    FirstName: Optional[str] = Field(None, description="First name of the contact")
    LastName: str = Field(..., description="Last name of the contact")
    Title: Optional[str] = Field(None, description="Job title of the contact")
    Company: Optional[str] = Field(None, description="Company name (for AccountId)")
    Email: Optional[str] = Field(None, description="Email address")
    Phone: Optional[str] = Field(None, description="Phone number")
    MobilePhone: Optional[str] = Field(None, description="Mobile phone number")
    Department: Optional[str] = Field(None, description="Department within the company")
    MailingAddress: Optional[Address] = Field(None, description="Mailing address")
    Description: Optional[str] = Field(None, description="Additional notes or description of the contact, e.g. interests")
    LeadSource: Optional[str] = Field(None, description="Source of the lead")

class MeetingAnalysis(BaseModel):
    contacts: List[SalesforceContact] = Field(..., description="List of potential Salesforce contacts extracted from the meeting")

class APICallDetails(BaseModel):
    total_tokens: int = Field(..., description="Total number of tokens used in the API call")
    prompt_tokens: int = Field(..., description="Number of tokens in the prompt")
    completion_tokens: int = Field(..., description="Number of tokens in the completion")
    total_cost: float = Field(..., description="Total cost of the API call in USD")

class AnalysisResult(BaseModel):
    meeting_analysis: MeetingAnalysis = Field(..., description="Analysis of the meeting")
    api_call_details: APICallDetails = Field(..., description="Details of the API call")


class SalesforceContactAttributes(BaseModel):
    type: str = Field("Contact", const=True)
    url: str = Field(..., description="The URL of the Contact in Salesforce API")

class SalesforceContact(BaseModel):
    attributes: SalesforceContactAttributes
    Id: str = Field(..., description="Salesforce Contact Id")
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

class AnalysisResult(BaseModel):
    meeting_analysis: MeetingAnalysis = Field(..., description="Analysis of the meeting")
    api_call_details: APICallDetails = Field(..., description="Details of the API call")


def ensure_contact_attributes(contact: Dict) -> Dict:
    if 'attributes' not in contact or not isinstance(contact['attributes'], dict):
        contact['attributes'] = {
            "type": "Contact",
            "url": f"/services/data/v52.0/sobjects/Contact/{contact.get('Id', 'UNKNOWN')}"
        }
    return contact


llm = ChatOpenAI(model="gpt-3.5-turbo-0125")
json_parser = JsonOutputParser()

def analyze_meeting(transcript: str, meeting_details: str, existing_contacts: List[Dict]) -> AnalysisResult:
    """Analyze the meeting transcript and details to extract and update Salesforce contact information."""
    
    template = (
        "Analyze the following meeting transcript, details, and existing contact information:\n\n"
        "Transcript: {transcript}\n\n"
        "Meeting Details: {meeting_details}\n\n"
        "Existing Contacts: {existing_contacts}\n\n"
        "Extract and update  information about all participants (excluding the host) that could be used to create or update Salesforce contact records."
        "Focus on extracting and updating the following details for each participant:\n"
        "- First Name\n"
        "- Last Name\n"
        "- Email\n"
        "- Title\n"
        "- Department\n"
        "- Phone\n"
        "- Mobile Phone\n"
        "- Mailing Address (including City, Country, State, Street, and Postal Code)\n"
        "- Other Address (including City, Country, State, Street, and Postal Code)\n"
        "- Description\n"
        "- Lead Source\n"
        "- Any other relevant fields from the Salesforce Contact schema\n\n"
        "Provide the output in the JSON format\n\n"
        "Ensure your response is a valid JSON object. Don't include null fields. If certain information is not available or unchanged, omit those fields. "
        "Make sure to include all existing contacts in the output, updating their information as necessary based on the meeting data. "
        "For new contacts, generate a placeholder Id starting with '003' followed by 15 random alphanumeric characters."
    )
    
    prompt = ChatPromptTemplate.from_template(template)
    
    
    chain = RunnableSequence(
        prompt,
        llm,
        json_parser
    )
    
    try:
        start_time = time.time()
        with get_openai_callback() as cb:
            result = chain.invoke({
                "transcript": transcript,
                "meeting_details": meeting_details,
                "existing_contacts": json.dumps(existing_contacts)
            })
            
            if not isinstance(result, dict):
                raise ValueError(f"Expected a dictionary, but got {type(result)}")
            
            if 'contacts' not in result or not isinstance(result['contacts'], list):
                raise ValueError("Missing or invalid 'contacts' key in the result")
            
            valid_contacts = []
            for contact in result['contacts']:
                if contact is not None:
                    ensure_contact_attributes(contact)
                    valid_contacts.append(contact)
            
            if not valid_contacts:
                raise ValueError("No valid contacts found in the result")
            
            result['contacts'] = valid_contacts
            meeting_analysis = MeetingAnalysis(**result)
            end_time = time.time()
  
            api_call_details = APICallDetails(
                total_tokens=cb.total_tokens,
                prompt_tokens=cb.prompt_tokens,
                completion_tokens=cb.completion_tokens,
                total_cost=cb.total_cost
            )

            return AnalysisResult(
                meeting_analysis=meeting_analysis,
                api_call_details=api_call_details
            ), time.time() - start_time
    
    except json.JSONDecodeError as e:
        logger.error(f"Error decoding JSON: {e}. Raw output: {result}")
        raise
    except ValueError as e:
        logger.error(f"Invalid data structure: {e}")
        raise
    except Exception as e:
        raise
    
def process_meeting_data(webvtt_file: str, zoom_json_file: str, existing_contacts: List[Dict]) -> List[Dict]:
    """Process meeting data and update Salesforce contacts."""

    try:
        with open(webvtt_file, 'r') as f:
            transcript = f.read()

        with open(zoom_json_file, 'r') as f:
            zoom_json = f.read()

        [result, time_taken] = analyze_meeting(transcript, zoom_json, existing_contacts)
    
        updated_contacts = result.meeting_analysis.contacts
        call_data = result.api_call_details
        
        call_data = call_data.dict()
        call_data["total_time"] = time_taken
        call_data['tokens_per_second'] = call_data['total_tokens'] / call_data['total_time']
        call_data['cost_per_token'] = call_data['total_cost'] / call_data['total_time']
        
        logger.info(f"Processed meeting data from {webvtt_file} and {zoom_json_file}")
        logger.info(f"API Call Details: {json.dumps(call_data)}")
        
        return [contact.dict(exclude_unset=True) for contact in updated_contacts], call_data

    except FileNotFoundError as e:
        logger.error(f"File not found: {e}")
        return existing_contacts
    except json.JSONDecodeError as e:
        logger.error(f"JSON decoding error: {e}")
        return existing_contacts
    except ValueError as e:
        logger.error(f"Value error: {e}")
        return existing_contacts
    except Exception as e:
        logger.error(f"An unexpected error occurred while processing meeting data: {e}")
        return existing_contacts
    
    
@app.route('/process', methods=['POST'])
# @token_required
def process():
    data = request.get_json()
    
    required_fields = ['webvtt_file', 'zoom_json_file', 'participants']
    if not all(field in data for field in required_fields):
        return jsonify({'message': 'Missing required fields!'}), 400
    
    webvtt_file = data['webvtt_file']
    zoom_json_file = data['zoom_json_file']
    participants = data['participants']
    updated_contacts, call_data = process_meeting_data(webvtt_file, zoom_json_file, participants)
    result = {
        "updated_contacts": updated_contacts,
        "call_data": call_data
    }

    return jsonify(result)

if __name__ == "__main__":
    host, port = BASE_URL_Openai[:-4], BASE_URL_Openai[-4:]
    app.run(port=port, host='localhost')
