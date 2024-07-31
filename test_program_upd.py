import json
from typing import List, Dict
from pydantic import BaseModel

from models.updOpenIAClient import analyze_meeting, AnalysisResult, SalesforceContact, APICallDetails

mock_meeting_details = {
    "uuid": "def456",
    "id": 9876543210,
    "host_id": "sarah.johnson@cloudsync.com",
    "topic": "Data Management Solutions Discussion: CloudSync <> GreenLeaf Enterprises",
    "type": 2,
    "start_time": "2023-07-15T09:00:00Z",
    "duration": 90,
    "timezone": "UTC",
    "agenda": "Explore how CloudSync can improve GreenLeaf Enterprises' data management processes",
    "created_at": "2023-07-08T14:30:00Z",
    "join_url": "https://zoom.us/j/9876543210",
    "participants": [
        {
            "name": "Sarah Johnson",
            "email": "sarah.johnson@cloudsync.com",
            "role": "Host"
        },
        {
            "name": "Tom Chen",
            "email": "tom.chen@cloudsync.com",
            "role": "Presenter"
        },
        {
            "name": "Lisa Patel",
            "email": "lisa.patel@cloudsync.com",
            "role": "Presenter"
        },
        {
            "name": "Michael Rodriguez",
            "email": "michael.rodriguez@greenleaf.com",
            "role": "Participant"
        },
        {
            "name": "Amanda Foster",
            "email": "amanda.foster@greenleaf.com",
            "role": "Participant"
        },
        {
            "name": "Robert Kim",
            "email": "robert.kim@greenleaf.com",
            "role": "Participant"
        }
    ]
}

mock_transcript = """WEBVTT

00:00:00.000 --> 00:00:05.000
Sarah Johnson: Welcome everyone to our discussion on Data Management Solutions. Let's start with introductions.

00:00:05.500 --> 00:00:10.500
Tom Chen: Hi, I'm Tom Chen from CloudSync's technical team. I'll be presenting our core data management features.

00:00:11.000 --> 00:00:16.000
Lisa Patel: Hello, Lisa Patel here. I'm the account manager for GreenLeaf Enterprises. Excited to explore how we can help.

00:00:16.500 --> 00:00:21.500
Michael Rodriguez: Michael Rodriguez, IT Director at GreenLeaf. Looking forward to understanding CloudSync's capabilities.

00:00:22.000 --> 00:00:27.000
Amanda Foster: Amanda Foster, Data Analyst at GreenLeaf. Keen to see how CloudSync can streamline our processes.

00:00:27.500 --> 00:00:32.500
Robert Kim: Robert Kim, Operations Manager at GreenLeaf. Interested in the potential efficiency gains.

00:00:33.000 --> 00:00:40.000
Sarah Johnson: Great, thanks everyone. Tom, can you start by giving an overview of CloudSync's data management solutions?

00:00:40.500 --> 00:01:00.500
Tom Chen: Certainly, Sarah. CloudSync offers a comprehensive suite of data management tools. Our platform integrates seamlessly with existing systems, provides real-time data synchronization, and offers advanced analytics capabilities. For GreenLeaf, this could mean more efficient data processing and improved decision-making processes.

00:01:01.000 --> 00:01:10.000
Michael Rodriguez: That sounds promising. How does CloudSync handle data security and compliance? We deal with sensitive customer information.

00:01:10.500 --> 00:01:30.500
Lisa Patel: Great question, Michael. Security is a top priority for us. We employ end-to-end encryption, regular security audits, and comply with major data protection regulations. We also offer granular access controls, allowing you to manage who has access to what data. I can send you our detailed security whitepaper after the meeting.

00:01:31.000 --> 00:01:40.000
Amanda Foster: I'm particularly interested in the analytics capabilities. Can you elaborate on how this could help with our data analysis processes?

00:01:40.500 --> 00:02:00.500
Tom Chen: Absolutely, Amanda. Our analytics suite includes predictive modeling, trend analysis, and customizable dashboards. For a data analyst like yourself, this means you can derive insights faster and more accurately. We also offer integration with popular data visualization tools, which can streamline your reporting processes.

00:02:01.000 --> 00:02:10.000
Robert Kim: How about implementation and training? What kind of support does CloudSync provide during the transition phase?

00:02:10.500 --> 00:02:30.500
Lisa Patel: We offer comprehensive support throughout the implementation process, Robert. This includes a dedicated implementation team, customized training sessions for your staff, and 24/7 technical support. We typically assign a project manager to oversee the entire transition, ensuring a smooth integration with your existing operations.

00:02:31.000 --> 00:02:40.000
Sarah Johnson: Thank you, everyone. This has been a productive discussion. Any final questions before we wrap up?

00:02:40.500 --> 00:02:50.500
Michael Rodriguez: Yes, I'd like to discuss pricing options. Lisa, could you send over a detailed quote based on our company size and data volume?

00:02:51.000 --> 00:03:01.000
Lisa Patel: Of course, Michael. I'll prepare a customized quote and send it to your email by tomorrow. Would you prefer I cc anyone else from your team?

00:03:01.500 --> 00:03:06.500
Michael Rodriguez: Yes, please include Amanda and Robert as well.

00:03:07.000 --> 00:03:20.000
Sarah Johnson: Great, thanks everyone for your time today. We'll follow up with the requested information and schedule a follow-up meeting to address any additional questions. Have a great day!
"""

# mock_existing_contacts: List[Dict] = [
#     {
#         "attributes": {"type": "Contact", "url": "/services/data/v52.0/sobjects/Contact/003ABCDEFGHIJKL"},
#         "Id": "003ABCDEFGHIJKL",
#         "FirstName": "Michael",
#         "LastName": "Rodriguez",
#         "Email": "m.rodriguez@oldmail.com",
#         "Title": "IT Manager",
#         "Department": "Information Technology",
#         "Phone": "555-987-6543"
#     },
#     {
#         "attributes": {"type": "Contact", "url": "/services/data/v52.0/sobjects/Contact/003MNOPQRSTUVWX"},
#         "Id": "003MNOPQRSTUVWX",
#         "FirstName": "Amanda",
#         "LastName": "Foster",
#         "Email": "amanda.foster@oldmail.com",
#         "Title": "Junior Analyst",
#         "Department": "Data Analysis",
#         "Phone": "555-456-7890"
#     }
# ]

def run_test():
    print("Running Correctly Formatted Meeting Analysis Test")
    print("------------------------------------------------")

    try:
        result = analyze_meeting(mock_transcript, json.dumps(mock_meeting_details), [])
        
        print("\nAnalysis Results:")
        print("----------------")
        for contact in result.meeting_analysis.contacts:
            for key, value in contact.dict().items():
                if value:
                    print(f"{key}: {value}")
            print("----------------")
                

        print("\nAPI Call Details:")
        print("-----------------")
        print(f"Total Tokens: {result.api_call_details.total_tokens}")
        print(f"Total Cost: ${result.api_call_details.total_cost:.4f}")
        print(f"Total Time: {result.api_call_details.total_time:.2f} seconds")
        print(f"Tokens per Second: {result.api_call_details.tokens_per_second:.2f}")
        print(f"Cost per Token: ${result.api_call_details.cost_per_token:.6f}")

    except Exception as e:
        print(f"An error occurred during the test: {str(e)}")

if __name__ == "__main__":
    run_test()
