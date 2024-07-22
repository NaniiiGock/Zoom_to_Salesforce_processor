# import requests
# import json

# BASE_URL_SalesforceConnector = 'http://localhost:8080'

# def get_ids(participants):
#     response = requests.post(f"{BASE_URL_SalesforceConnector}/get_ids", json={'participants': participants})
#     print('POST /get_ids')
#     return response.json()

# def get_cleared_info(ids):
#     response = requests.post(f"{BASE_URL_SalesforceConnector}/get_cleared_info", json={'ids': ids})
#     print('POST /get_cleared_info')
#     return response.json()

# def update_contacts(contacts):
#     response = requests.post(f"{BASE_URL_SalesforceConnector}/update_contacts", json={'contacts': contacts})
#     print('POST /update_contacts')
#     return response.json()

# if __name__ == '__main__':
#     # Test /get_ids
#     participants = [
#     {
#         "name": "John Doe",
#         "email": "john.doe@revenuegrid.com"
#     },
#     {
#         "name": "Jane Smith",
#         "email": "jane.smith@techinnovations.com"
#     },
#     {
#         "name": "Mark Lee",
#         "email": "mark.lee@techinnovations.com"
#     },
#     {
#         "name": "Susan Choi",
#         "email": "susan.choi@techinnovations.com"
#     }
# ]
#     ids = get_ids(participants)
#     print(ids)
#     # Assuming you get ids from /get_ids, e.g., ['003xx0000123456', '003xx0000654321']
#     # ids = ['003Qy000006ROyrIAG', '003Qy000006RP0TIAW']
    
#     # Test /get_cleared_info
#     cleared_info = get_cleared_info(ids)
#     print(cleared_info)
#     # Test /update_contacts
#     updated_contacts = [
#     {
#         "attributes": {
#             "type": "Contact",
#             "url": "/services/data/v52.0/sobjects/Contact/003Qy000006ROyrIAG"
#         },
#         "Id": "003Qy000006ROyrIAG",
#         "Email": "john.doe@revenuegrid.com",
#         "FirstName": "John",
#         "LastName": "Doe"
#     },
#     {
#         "attributes": {
#             "type": "Contact",
#             "url": "/services/data/v52.0/sobjects/Contact/003Qy000006RP0TIAW"
#         },
#         "Id": "003Qy000006RP0TIAW",
#         "Department": "Product",
#         "Email": "jane.smith@techinnovations.com",
#         "FirstName": "Jane",
#         "LastName": "Smith",
#         "Title": "Product Team"
#     },
#     {
#         "attributes": {
#             "type": "Contact",
#             "url": "/services/data/v52.0/sobjects/Contact/003Qy000006RP25IAG"
#         },
#         "Id": "003Qy000006RP25IAG",
#         "Department": "Sales",
#         "Email": "mark.lee@techinnovations.com",
#         "FirstName": "Mark",
#         "LastName": "Lee",
#         "Title": "VP of Sales"
#     },
#     {
#         "attributes": {
#             "type": "Contact",
#             "url": "/services/data/v52.0/sobjects/Contact/003Qy000006RP3hIAG"
#         },
#         "Id": "003Qy000006RP3hIAG",
#         "Department": "Sales",
#         "Email": "susan.choi@techinnovations.com",
#         "FirstName": "Susan",
#         "LastName": "Choi",
#         "Title": "Sales Manager"
#     }
# ]
#     update = update_contacts(updated_contacts)
#     print(update)



# BASE_URL_ZoomMeeting = 'http://localhost:8081'

# def get_participants(json_file_path):
#     with open(json_file_path, 'r') as file:
#         json_data = json.load(file)
#     response = requests.post(f"{BASE_URL_ZoomMeeting}/get_participants", json=json_data)
#     return response.json()

# # Example usage
# if __name__ == "__main__":
#     test_json_file_path = 'example/zoom_meeting.json'
#     print(test_zoom_meeting(test_json_file_path))




# BASE_URL_Openai = "http://localhost:8083"
# def processing(webvtt_file, zoom_json_file, participants):
#     response = requests.post(f"{BASE_URL_Openai}/process", json={'webvtt_file': webvtt_file, 'zoom_json_file': zoom_json_file, 'participants': participants})
#     return response

# resp = processing('example/transcript.webvtt', 'example/zoom_meeting.json', [
#     {
#         "email": "john.doe@revenuegrid.com",
#         "name": "John Doe"
#     },
#     {
#         "email": "jane.smith@techinnovations.com",
#         "name": "Jane Smith"
#     },
#     {
#         "email": "mark.lee@techinnovations.com",
#         "name": "Mark Lee"
#     },
#     {
#         "email": "susan.choi@techinnovations.com",
#         "name": "Susan Choi"
#     }
# ]
# )

# print(resp)


from helpers.MeetingPeopleExtractor import ZoomMeeting
import json
import requests

url = "http://localhost:8082"
def test_program():
    test_json_file_path = 'example/zoom_meeting.json'
    test_webvtt_file_path = 'example/transcript.webvtt'
    test_data = {
        'webvtt_file': test_webvtt_file_path,
        'zoom_json_file': test_json_file_path
    }
    
    response = requests.post(f"{url}/process", json=test_data)
    print(response.json())
    
if __name__ == "__main__":
    test_program()
