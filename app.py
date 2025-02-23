from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import openai
import sqlite3
from datetime import datetime 

from flask import Flask, jsonify, abort

app = Flask(__name__) 
days = [
    {"id": 1, "name": "Monday"},
    {"id": 2, "name": "Tuesday"},
    {"id": 3, "name": "Wednesday"},
    {"id": 4, "name": "Thursday"},
    {"id": 5, "name": "Friday"},
    {"id": 6, "name": "Saturday"},
    {"id": 7, "name": "Sunday"},
]



@app.route("/", methods=["GET"])
def get_days():
    return jsonify(days)


@app.route("/<int:day_id>", methods=["GET"])
def get_day(day_id):
    day = [day for day in days if day["id"] == day_id]
    if len(day) == 0:
        abort(404)
    return jsonify({"day": day[0]})

@app.route("/", methods=["POST"])
def post_days():
    return jsonify({"reply": "sam"}), 201


# Twilio credentials
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number' 

# OpenAI credentials
openai.api_key = 'your_openai_api_key' 

# Database setup
# Define the database file
DATABASE = 'sms_ai.db'



print("Database and tables created successfully!")
def get_db_connection():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn 

@app.route('/sms', methods=['GET'])
def sms_reply():
    # Get incoming message details
    incoming_msg = request.form.get('Body')
    sender_phone = request.form.get('From') 

    # Save the incoming message to the database
    conn = get_db_connection()
    cursor = conn.cursor() 

    # Check if the user exists
    cursor.execute('SELECT UserID FROM Users WHERE PhoneNumber = ?', (sender_phone,))
    user = cursor.fetchone() 

    if not user:
        # Create a new user
        cursor.execute('INSERT INTO Users (PhoneNumber) VALUES (?)', (sender_phone,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['UserID'] 

    # Create a new conversation if it doesn't exist
    cursor.execute('SELECT ConversationID FROM Conversations WHERE UserID = ?', (user_id,))
    conversation = cursor.fetchone() 

    if not conversation:
        cursor.execute('INSERT INTO Conversations (UserID) VALUES (?)', (user_id,))
        conn.commit()
        conversation_id = cursor.lastrowid
    else:
        conversation_id = conversation['ConversationID'] 

    # Save the incoming message
    cursor.execute('INSERT INTO Messages (ConversationID, MessageText, IsFromAI) VALUES (?, ?, ?)',
                   (conversation_id, incoming_msg, False))
    conn.commit() 

    # Generate AI response
    ai_response = generate_ai_response(incoming_msg) 

    # Save the AI response
    cursor.execute('INSERT INTO Messages (ConversationID, MessageText, IsFromAI) VALUES (?, ?, ?)',
                   (conversation_id, ai_response, True))
    conn.commit() 

    # Send the AI response via SMS
    send_sms(sender_phone, ai_response) 

    conn.close() 

    # Respond to Twilio
    response = MessagingResponse()
    return str(response) 

def generate_ai_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use GPT-3.5
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip() 

def send_sms(to_phone, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=to_phone
    )

if __name__ == '__main__':
    app.run(debug=True)
