from datetime import datetime, timedelta
import json
import os
from flask import Flask, request
import gspread
from dotenv import load_dotenv
from utils import ( phone_format )

load_dotenv('.env')

# load google sheet
gc = gspread.service_account(filename='./service_account.json')
sh = gc.open('Volunteer Hours')
ws_members = sh.worksheet("Members")
MEMBERS_COL_FIRST_NAME = 0
MEMBERS_COL_LAST_NAME = 1
MEMBERS_COL_PHONE = 2

ws_vhours = sh.worksheet("Hours")

app = Flask(__name__)

@app.route('/', methods=['GET'])
def helloworld():
	return 'Hello, DUG Bot!'

@app.route('/greeting', methods=['POST'])
def greeting():
	memory = json.loads(request.form['Memory'])
	phone = phone_format( memory['twilio']['sms']['From'].replace('+1', ''))
	rows = ws_members.get_all_values()
	rows_count = len( rows )
	del rows[0]
	for row in rows:
		if row[MEMBERS_COL_PHONE] == phone:

			return {
					"actions": [
							{
								"say": "Hi {0}, it's farmer Doug again, are you checking in now to volunteer?".format( row[MEMBERS_COL_FIRST_NAME] )
							},
							{
								"remember": {
									"phone": phone,
									"first_name": row[MEMBERS_COL_FIRST_NAME],
									"last_name": row[MEMBERS_COL_LAST_NAME],
									"member_rows_count": rows_count
								 }
							},
							{
								"listen": True
							}
						]
					}

	return {
				"actions": [
					{
						"say": "You're new!  I'm farmer Doug. Welcome to Denver Urban Gardens (DUG) community volunteer time tracker. Before I log your time, I need to know your full name."
					},
					{
					"collect": {
						"name":"fullname",
						"questions":[
						  {
							"question":"What is your first name?",
							"name":"first_name",
							"type": "Twilio.FIRST_NAME"
						  },
							{
							  "question":"What is your last name?",
							  "name":"last_name",
							  "type": "Twilio.LAST_NAME"
							},
						 ],
						 "on_complete": {
							"redirect": "task://full_name"
						}
						}
					},
					{
						"remember": {
							"phone": phone,
							"member_rows_count": rows_count
						}
					},
					{
							 "listen": True
					}
				]
			}

@app.route('/fullname', methods=['POST'])
def fullname():
	memory = json.loads(request.form['Memory'])
	first_name = memory['twilio']['collected_data']['fullname']['answers']['first_name']['answer']
	last_name = memory['twilio']['collected_data']['fullname']['answers']['last_name']['answer']
	phone = memory.get('phone')
	member_rows_count = memory.get('member_rows_count')

	# add row
	ws_members.update('A{0}'.format( member_rows_count + 1 ), first_name.capitalize() )
	ws_members.update('B{0}'.format( member_rows_count + 1 ), last_name.capitalize() )
	ws_members.update('C{0}'.format( member_rows_count + 1 ), phone)

	return {
			"actions": [
					{
						"say": "Okay {0}, let's get started. Are you checking in now to volunteer?".format( first_name )
					},
					{
						"remember": {
							"first_name": first_name.capitalize(),
							"last_name": last_name.capitalize()
						}
					},
					{
						"listen": True
					}
				]
			}

@app.route('/checkin', methods=['POST'])
def checkin():
	memory = json.loads(request.form['Memory'])

	now = datetime.now() - timedelta( hours = int(os.environ['OFFSET_HOURS']))

	return {
		'actions': [
			{'say': 'Great your checkin time has been logged. Approximately, what time will you be checking out? (Enter time in format such as 5pm or 5:30pm)'},
			{
				"remember": {
					"checkin_time": now.strftime("%m-%d-%Y %H:%M")
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
	rows_count = len( ws_vhours.get_all_values() )

	if not request.form.get('Field_time_Value'):
		return {
			'actions': [
				{ 'say': 'I\'m sorry. I didn\'t understand. Can you input your checkout time again?' },
				{
						 "listen": True
				},
				{
					 "redirect": "task://checkout"
				}
			]
		}


	# format date time
	checkin_date = memory['checkin_time'].split(' ')[0]
	checkin_time = datetime.strptime( memory['checkin_time'], '%m-%d-%Y %H:%M')
	checkout_time = datetime.strptime('{0} {1}'.format( checkin_date, request.form.get('Field_time_Value')), '%m-%d-%Y %H:%M' )
	if checkout_time < checkin_time:
		checkout_time = checkout_time + timedelta(hours = 12 )

	hours = round((checkout_time - checkin_time).seconds / ( 60 * 60 ), 2)

	# add row
	ws_vhours.update('A{0}'.format( rows_count + 1 ), memory['first_name'] )
	ws_vhours.update('B{0}'.format( rows_count + 1 ), memory['last_name'] )
	ws_vhours.update('C{0}'.format( rows_count + 1 ), checkin_date )
	ws_vhours.update('D{0}'.format( rows_count + 1 ), checkin_time.strftime("%l:%M %p") )
	ws_vhours.update('E{0}'.format( rows_count + 1 ), checkout_time.strftime("%l:%M %p") )
	ws_vhours.update('F{0}'.format( rows_count + 1 ), hours )

	return {
		'actions': [
			{'say': '{0} hours has been logged as your volunteer time.'.format(hours)},
			{
				 "redirect": "task://goodbye"
			}
		]
	}

if __name__ == '__main__':
	app.run()
