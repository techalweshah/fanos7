import sqlite3

# Define the database file
DATABASE = 'sms_ai.db'

# Connect to the SQLite database
conn = sqlite3.connect(DATABASE)
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
    IsIncoming BOOLEAN NOT NULL,
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

# Commit changes and close the connection
conn.commit()
conn.close()

print("Database and tables created successfully!")
