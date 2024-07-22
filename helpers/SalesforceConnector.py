import requests
from dotenv import load_dotenv
import os
import json
from flask import Flask, request, jsonify
import sys

load_dotenv()

CONSUMER_KEY = os.getenv('CONSUMER_KEY')
CONSUMER_SECRET = os.getenv('CONSUMER_SECRET')
USERNAME = os.getenv('USERNAME')
PASSWORD = os.getenv('PASSWORD')
DOMAIN = os.getenv('DOMAIN')

BASE_URL_SalesforceConnector = os.getenv('BASE_URL_SalesforceConnector')

app = Flask(__name__)

class SalesforceConnector:
    def __init__(self):
        self.access_token = self.generate_token()['access_token']
        self.headers = {'Authorization': 'Bearer ' + self.access_token}
        
    def generate_token(self):
        payload = {
            'grant_type':'password',
            'client_id': CONSUMER_KEY,
            'client_secret': CONSUMER_SECRET,
            'username': USERNAME,
            'password': PASSWORD
        }

        oauth_endpoint = '/services/oauth2/token'
        response = requests.post(DOMAIN + oauth_endpoint, data=payload)
        return response.json()

    def query(self, soql_query):
        try:
            endpoint = '/services/data/v52.0/query/'
            records = []
            response = requests.get(DOMAIN + endpoint, headers=self.headers, params={'q': soql_query})
            total_size = response.json()['totalSize']
            records.extend(response.json()['records'])
            while not response.json()['done']:
                response = requests.get(DOMAIN + endpoint + response.json()['nextRecordUrl'], headers=self.headers)
                records.extend(response.json()['records'])
            return {'record_size': total_size, 'records': records}
        except Exception as e:
            print(e)
            return
      

    def get_contact_by_email(self, email):
        soql_query = f"SELECT Id, FirstName, LastName, Email FROM Contact WHERE Email = '{email}'"
        contact_data = self.query(soql_query)
        return contact_data['records'][0] if contact_data['record_size'] > 0 else None

    
    def retrieve_object_metadata(self, object_id):
        endpoint = '/services/data/v52.0/sobjects/' + object_id + '/describe'
        response = requests.get(DOMAIN + endpoint, headers=self.headers)
        return response.json()

    def get_contacts(self):
        soql_query = "SELECT Id, FirstName, LastName, Email FROM Contact"
        contact_data = self.query(soql_query)
        print('Total Contacts:', contact_data['record_size'])
        return contact_data['records']

    def delete_contact(self, contact_id):
        try:
            endpoint = f'/services/data/v52.0/sobjects/Contact/{contact_id}'
            response = requests.delete(DOMAIN + endpoint, headers=self.headers)
            if response.status_code == 204:
                print(f'Contact {contact_id} deleted successfully.')
            else:
                print(f'Failed to delete contact {contact_id}:', response.json())
        except Exception as e:
            print(e)

    def clear_all_contacts(self):
        contact_data=self.get_contacts()
        print('Contacts to clear:', len(contact_data))
        for contact in contact_data:
            self.delete_contact(contact['Id'])

    def contact_exists(self, contact_id):
        soql_query = f"SELECT Id FROM Contact WHERE Id = '{contact_id}'"
        contact_data = self.query(soql_query)
        return contact_data['record_size'] > 0
    
    def get_contact_by_id(self, contact_id):
        soql_query = f"SELECT Id FROM Contact WHERE Id = '{contact_id}'"
        contact_data = self.query(soql_query)
        return contact_data
    
    def add_contact(self, contact):
        try:
            endpoint = '/services/data/v52.0/sobjects/Contact/'
            response = requests.post(DOMAIN + endpoint, headers=self.headers, json=contact)
            if response.status_code == 201:
                print('Contact created successfully:', response.json())
                return response.json()['id']
            else:
                print('Failed to create contact:', response.json())
        except Exception as e:
            print(e)

    def update_contact(self, contact_id, update_data):
        try:
            endpoint = f'/services/data/v52.0/sobjects/Contact/{contact_id}'
            response = requests.patch(DOMAIN + endpoint, headers=self.headers, json=update_data)
            if response.status_code == 204:
                print(f'Contact {contact_id} updated successfully.')
            else:
                print(f'Failed to update contact {contact_id}:', response.json())
        except Exception as e:
            print(e)
            
    
    def get_participants_ids(self, participants):
        """extract ids from participants, add new contacts if not exist"""
        ids = []
        for participant in participants:
            contact = self.get_contact_by_email(participant['email'])
            if contact == None:
                id = self.add_contact({'FirstName': participant['name'].split(' ')[0], 'LastName': participant['name'].split(' ')[1], 'Email': participant['email']})
                print(f"Contact {id} created successfully.")
                ids.append(id)
            else:
                print(f"Contact {contact['Id']} already exists.")
                ids.append(contact['Id'])
        return ids

    def get_info_by_id(self, contact_id):
        """
        get information about participants
        return: dict
        """
        soql_query = f"""
        SELECT Id, FirstName, LastName, Email, Phone, MobilePhone, Department, Title, MailingStreet, MailingCity, MailingState, MailingPostalCode, MailingCountry, Description
        FROM Contact
        WHERE Id = '{contact_id}'
        """
        contact = self.query(soql_query)
        return contact['records'][0]

    def get_info_and_clear(self, ids):
        contacts_details = []
        for id in ids:
            contact = self.get_info_by_id(id)
            for key in list(contact):
                if contact[key] == None:
                    del contact[key]
            contacts_details.append(contact)
        
        contacts_details = json.dumps(contacts_details)
        return contacts_details

    def update_contact_list(self, contacts):
        for contact in contacts:
            id = contact['Id']
            del contact['Id']
            self.update_contact(id, contact)
            
            
@app.route('/get_ids', methods=['POST'])
def get_ids():
    sc = SalesforceConnector()
    participants = request.json.get('participants', [])
    ids = sc.get_participants_ids(participants)
    return jsonify(ids)

@app.route('/get_cleared_info', methods=['POST'])
def get_cleared_info():
    sc = SalesforceConnector()
    ids = request.json.get('ids', [])
    contacts_details = sc.get_info_and_clear(ids)
    print(contacts_details)
    return contacts_details

@app.route('/update_contacts', methods=['POST'])
def update_contacts():
    sc = SalesforceConnector()
    contacts = request.json.get('contacts', [])
    sc.update_contact_list(contacts)
    return jsonify({'message': 'Contacts updated successfully.'})

@app.route('/clear_all_contacts', methods=['GET'])
def clear_all_contacts():
    sc = SalesforceConnector()
    sc.clear_all_contacts()
    return jsonify({'message': 'All contacts cleared successfully.'})

if __name__ == '__main__':
    host, port = BASE_URL_SalesforceConnector[:-4], BASE_URL_SalesforceConnector[-4:]
    app.run(port=port, host='localhost')
