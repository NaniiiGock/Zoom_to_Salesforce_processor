# ZOOM Meeting Analyzer



In the sales process any meeting is a valuable source of information about the customer. Sales executive usually must fill this information into CRM manually. 

This Flask application analyses data(.json) and transcript(.webvtt) of the Zoom meeting using OpenAI LLM model and updates contacts on Salesforce.

Workflow:
- contacts extraction from zoom json file
- checking if needed participants are already among Salesforce contacts, creating a new ones with basic data if not
-  extracting valuable information about customers with Large Language Models to process Zoom meeting data (meeting information and WEBVTT files). 
- creating/updating records in CRM, taking into account the existing data about the user


# Deliverables

- Source code for the solution.
- Documentation explaining the implementation, setup, and usage.
- Test cases to validate the solution.
- Deployment requirements: models, platform, etc.


## Implementation

There are 4 microservices: SalesforceConnector, MeetingPeopleExtractor, OpenAIClient and Main.

MeetingPeopleExtractor:
- reads .json file about the meeting
- extracts user names and emails
- forms them into fitting json for the next steps

SalesforceConnector consists of the methods needed to:
- connect to Salesforce Account (OAuth 2.0)
- create, modify, delete, and read contacts

OpenAIClient:

- 
