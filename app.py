from flask import Flask, request, jsonify, abort
from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
import openai
import sqlite3
from datetime import datetime
app = Flask(__name__)

# Days data
days = [
    {"id": 1, "name": "Monday"},
    {"id": 2, "name": "Tuesday"},
    {"id": 3, "name": "Wednesday"},
    {"id": 4, "name": "Thursday"},
    {"id": 5, "name": "Friday"},
    {"id": 6, "name": "Saturday"},
    {"id": 7, "name": "Sunday"},
]
import sqlite3

# Define the database file
DATABASE: str = "sms_ai.db"

def create_tables():
    """Create all necessary tables in the SQLite database."""
    with sqlite3.connect(DATABASE) as conn:
        cursor = conn.cursor()

        # Create the Users table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Users (
            UserID INTEGER PRIMARY KEY AUTOINCREMENT,
            PhoneNumber TEXT NOT NULL UNIQUE,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        # Create the SMSMessages table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SMSMessages (
            MessageID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER NOT NULL,
            MessageText TEXT NOT NULL,
            IsIncoming INTEGER NOT NULL, -- BOOLEAN stored as INTEGER (1 or 0)
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        ''')

        # Create the AIReplies table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS AIReplies (
            ReplyID INTEGER PRIMARY KEY AUTOINCREMENT,
            MessageID INTEGER NOT NULL,
            ReplyText TEXT NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (MessageID) REFERENCES SMSMessages(MessageID)
        );
        ''')

        # Create the Conversations table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS Conversations (
            ConversationID INTEGER PRIMARY KEY AUTOINCREMENT,
            UserID INTEGER NOT NULL,
            Context TEXT,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UpdatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (UserID) REFERENCES Users(UserID)
        );
        ''')

        # Create the SMSTemplates table
        cursor.execute('''
        CREATE TABLE IF NOT EXISTS SMSTemplates (
            TemplateID INTEGER PRIMARY KEY AUTOINCREMENT,
            TemplateName TEXT NOT NULL,
            TemplateText TEXT NOT NULL,
            CreatedAt TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        ''')

        print("Database and tables created successfully!")


# Routes to handle days
@app.route("/", methods=["GET"])
def get_days():
    create_tables()
    return jsonify(days)

@app.route("/<int:day_id>", methods=["GET"])
def get_day(day_id):
    day = next((day for day in days if day["id"] == day_id), None)
    if day is None:
        abort(404)  # Return 404 if the day was not found
    return jsonify({"day": day})

@app.route("/", methods=["POST"])
def post_days():
    return jsonify({"reply": "sam"}), 201

# Twilio credentials
TWILIO_ACCOUNT_SID = 'your_twilio_account_sid'
TWILIO_AUTH_TOKEN = 'your_twilio_auth_token'
TWILIO_PHONE_NUMBER = 'your_twilio_phone_number'

# OpenAI credentials
openai.api_key = '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'

# Database setup
DATABASE = 'sms_ai.db'

# Connect to the SQLite database
def connect_to_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row  # Enable row factory for dict-like cursor results
    return conn

# Route to handle incoming SMS
@app.route('/sms', methods=['POST'])  # Use POST for Twilio Webhook
def sms_reply():
    incoming_msg = request.form.get('message')
    sender_phone = request.form.get('sender')

    if not incoming_msg or not sender_phone:
        return jsonify({"reply": "sam"}), 201

    conn = connect_to_db()
    cursor = conn.cursor()

    # Check if the user exists in the database
    cursor.execute('SELECT UserID FROM Users WHERE PhoneNumber = ?', (sender_phone,))
    user = cursor.fetchone()

    if not user:
        # Create a new user
        cursor.execute('INSERT INTO Users (PhoneNumber) VALUES (?)', (sender_phone,))
        conn.commit()
        user_id = cursor.lastrowid
    else:
        user_id = user['UserID']

    # Check if a conversation exists for the user
    cursor.execute('SELECT ConversationID FROM Conversations WHERE UserID = ?', (user_id,))
    conversation = cursor.fetchone()

    if not conversation:
        # Create a new conversation
        cursor.execute('INSERT INTO Conversations (UserID) VALUES (?)', (user_id,))
        conn.commit()
        conversation_id = cursor.lastrowid
    else:
        conversation_id = conversation['ConversationID']

    # Save the incoming message to the database
    cursor.execute(
        'INSERT INTO SMSMessages (UserID, MessageText, IsIncoming) VALUES (?, ?, ?)',
        (user_id, incoming_msg, False)
    )
    conn.commit()

    # Generate AI response using OpenAI
    ai_response = generate_ai_response(incoming_msg)

    # Save the AI response to the database
    cursor.execute(
        'INSERT INTO Messages (ConversationID, MessageText, IsFromAI) VALUES (?, ?, ?)',
        (conversation_id,ai_response , True)
    )
    conn.commit()

    # Send the AI response via SMS
 #   send_sms(sender_phone, ai_response)

    # Respond to Twilio
  #  response = MessagingResponse()
  #  response.message(ai_response)

    conn.close()

    return jsonify({"reply": ai_response), 201
   # return str(response)

# Function to generate AI response
def generate_ai_response(prompt):
    response = openai.Completion.create(
        engine="text-davinci-003",  # Use GPT-3.5
        prompt=prompt,
        max_tokens=150,
        temperature=0.7
    )
    return response.choices[0].text.strip()

# Function to send SMS using Twilio
def send_sms(to_phone, message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
    client.messages.create(
        body=message,
        from_=TWILIO_PHONE_NUMBER,
        to=to_phone
    )

if __name__ == '__main__':
    app.run(debug=True)
