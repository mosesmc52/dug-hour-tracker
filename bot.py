from datetime import datetime
import json
import os
from flask import Flask, request
import gspread
from dotenv import load_dotenv

load_dotenv('.env')

'''
# https://github.com/burnash/gspread
gc = gspread.service_account(filename='./service_account.json')
wks = gc.open(os.environ['GSHEET_NAME']).sheet1
'''

app = Flask(__name__)

@app.route('/checkin', methods=['POST'])
def checkin():
    memory = json.loads(request.form['Memory'])
    print(memory)

    now = datetime.now()

    # open google sheet

    # lookup phone number

    # add checkin time

    return {
        'actions': [
            {'say': 'Great your checkin time has been logged. Approximately what time will you be checking out?'},
            {
    			"remember": {
    				"checkin_date": now.strftime("%m-%d-%Y")
    			}
    		},
            {
			         "listen": True
		    }
        ]
    }

@app.route('/checkout', methods=['POST'])
def checkout():
    memory = json.loads(request.form['Memory'])
    print(memory)
    print(request.form.get('CurrentTaskConfidence'))
    print(request.form.get('Field_time_Value'))

    # open google sheet

    # lookup phone number

    # add checkin time

    return {
        'actions': [
            {'say': 'Thank You'},
            {
			     "redirect": "task://goodbye"
		    }
        ]
    }

app.run(host='0.0.0.0', port=3000)
