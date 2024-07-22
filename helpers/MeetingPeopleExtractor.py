import json
from flask import Flask, request, jsonify
from dotenv import load_dotenv
import os
import sys

load_dotenv()

BASE_URL_ZoomMeeting = os.getenv('BASE_URL_ZoomMeeting')
app = Flask(__name__)

class ZoomMeeting:
    def __init__(self, data):
        self.data = data
        self.uuid = self.data.get('uuid')
        self.id = self.data.get('id')
        self.host_id = self.data.get('host_id')
        self.topic = self.data.get('topic')
        self.type = self.data.get('type')
        self.start_time = self.data.get('start_time')
        self.duration = self.data.get('duration')
        self.timezone = self.data.get('timezone')
        self.agenda = self.data.get('agenda')
        self.created_at = self.data.get('created_at')
        self.join_url = self.data.get('join_url')
        self.participants = self._extract_participants()

    def _extract_participants(self):
        participants = self.data.get('participants', [])
        return [
            {
                'name': participant.get('name'),
                'email': participant.get('email'),
            } for participant in participants
        ]

    def get_participants(self):
        return self.participants

@app.route('/get_participants', methods=['POST'])
def get_participants():
    zm = ZoomMeeting(request.json)
    participants = zm.get_participants()
    print(participants)
    return jsonify(participants)

if __name__ == '__main__':
    host, port = BASE_URL_ZoomMeeting[:-4], BASE_URL_ZoomMeeting[-4:]
    app.run(port=port, host='localhost')
