
from __future__ import print_function
from future.standard_library import install_aliases
install_aliases()

from urllib.parse import urlparse, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError

import json
import os

from flask import Flask
from flask import request
from flask import make_response

# Flask app should start in global layout
app = Flask(__name__)


@app.route('/webhook', methods=['POST'])
def webhook():
    req = request.get_json(silent=True, force=True)

    print("Request:")
    print(json.dumps(req, indent=4))

    res = processRequest(req)

    res = json.dumps(res, indent=4)
    # print(res)
    r = make_response(res)
    r.headers['Content-Type'] = 'application/json'
    return r


def processRequest(req):

    if req.get("result").get("action") == "yahooWeatherForecast":
        yql_query = makeYqlQuery(req)
        if yql_query is None:
            return {}
        yql_url = baseurl + urlencode({'q': yql_query}) + "&format=json"
        result = urlopen(yql_url).read()
        data = json.loads(result)

        res = makeWebhookResultForWeather(data)
        return res

    elif req.get("result").get("action") == "inquiry":
        
        result = req.get("result")
        parameters = result.get("parameters")
        roomtype = parameters.get("RoomType")
        date_period = parameters.get("date-period")

        print("##################################################")
        res = makeWebhookResultForInquiry(roomtype, date_period)
        return res

    elif req.get("result").get("action") == "booking":
        
        result = req.get("result")
        parameters = result.get("parameters")
        roomtype = parameters.get("RoomType")
        date_period = parameters.get("date-period")

        print("##################################################")
        res = makeWebhookResultForBooking(roomtype, date_period)
        return res

    else:
        return {}


def makeYqlQuery(req):
    result = req.get("result")
    parameters = result.get("parameters")
    city = parameters.get("geo-city")
    if city is None:
        return None

    return "select * from weather.forecast where woeid in (select woeid from geo.places(1) where text='" + city + "')"

def makeWebhookResultForInquiry(roomtype, date_period):
    
    speech = "Yes we have some " + roomtype + " rooms available for " + date_period

    return {
        "speech": speech,
        "displayText": speech,
        "source": "my-hotel"
    }

def makeWebhookResultForWeather(data):
    query = data.get('query')
    if query is None:
        return {}

    result = query.get('results')
    if result is None:
        return {}

    channel = result.get('channel')
    if channel is None:
        return {}

    item = channel.get('item')
    location = channel.get('location')
    units = channel.get('units')
    if (location is None) or (item is None) or (units is None):
        return {}

    condition = item.get('condition')
    if condition is None:
        return {}

    # print(json.dumps(item, indent=4))

    speech = "Today the weather in " + location.get('city') + ": " + condition.get('text') + \
             ", And the temperature is " + condition.get('temp') + " " + units.get('temperature')

    print("Response:")
    print(speech)

    return {
        "speech": speech,
        "displayText": speech,
        # "data": data,
        # "contextOut": [],
        "source": "apiai-weather-webhook-sample"
    }


if __name__ == '__main__':
    port = int(os.getenv('PORT', 5001))

    print("Starting app on port %d" % port)

    app.run(debug=False, port=port, host='0.0.0.0')