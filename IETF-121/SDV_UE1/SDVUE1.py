import requests
import random
from flask import Flask, request, Response
import pytz
from datetime import datetime
import subprocess  # For running system commands
import re  # For regular expression operations
from xml.dom.minidom import parseString  # For formatting XML


#CloudServer IP, SDVUE1 port
CloudServer_IP = "10.60.0.2"
CloudServer_port1 = 9090
UE1port = 8080

# speed
target_speed = 50
current_speed = 0

# Initialize the Flask application
app = Flask(__name__)

# Define a route to handle POST requests to '/receive_message'
@app.route('/receive_message', methods=['POST'])
def receive_message():
    global target_speed
    global current_speed

    # Set the timezone
    timezone_now = pytz.timezone('Asia/Seoul')

    # Get the current time in the specified timezone
    current_time = datetime.now(timezone_now).strftime('%Y-%m-%d %H:%M:%S')

    # Read and decode the XML data from the request
    print("\n")
    print("=========new message start==============")
    print("Received XML from SDVUser:")
    xml_data = request.data.decode('utf-8')
    dom = parseString(xml_data)
    pretty_xml = dom.toprettyxml()
    print(pretty_xml)

    # Create a message with the current speed and time
    base_increase = 2  # 기본 증가량을 낮춰 변화 폭 감소
    # 목표 속도에 가까워질수록 증가량을 줄이기, 부드러운 변화
    speed_change = base_increase + random.uniform(-4, 6) * (1 - (abs(current_speed - target_speed) / target_speed))

    # 목표 속도에 비례한 조정 인자를 추가하여 변화율을 점진적으로 줄이기
    proportional_adjustment = (target_speed - current_speed) * 0.1
    speed_change += proportional_adjustment
    current_speed += int(speed_change)


    message = f"SDV1 speed is {current_speed}km/h and location is at {current_time}"
    print(message)
    print()

    # URL of CloudServer where the speed message will be sent
    url = f"http://{CloudServer_IP}:{CloudServer_port1}/receive_message"
    try:
        # Send the message to CloudServer
        response = requests.post(url, data=message, headers={'Content-Type': 'text/plain'})
        # Print the status code and response from CloudServer
        print(f"Sent '{message}' to CloudServer: {response.status_code}")
        print("Response from CloudServer:")
        print(response.text)
    except requests.exceptions.RequestException as e:
        # Print an error message if the request fails
        print(f"Failed to send message to CloudServer: {e}")

    # Return a response indicating that the message was received
    return Response("Message received", status=200)


# Function to get the IP address of a specified network interface
def get_ip_address(interface):
    try:
        # Run the 'ifconfig' command for the specified interface
        result = subprocess.run(['ifconfig', interface], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        if result.returncode != 0:
            raise ValueError(f"Failed to get ifconfig info for {interface}")

        # Decode the output from the command
        output = result.stdout.decode('utf-8')
        # Use regular expression to find the IP address in the output
        match = re.search(r'inet (\d+\.\d+\.\d+\.\d+)', output)
        if match:
            return match.group(1)
        else:
            raise ValueError(f"No IP address found for {interface}")
    except Exception as e:
        # Print an error message if any exception occurs
        print(f"Error: {e}")
        return None

# Main block to run the Flask app
if __name__ == '__main__':
    # Get the IP address of the 'uesimtun0' 5G network interface
    interface_ip = get_ip_address('uesimtun0')
    if interface_ip:
        # Print the IP address and start the Flask app
        print(f"Starting Flask app on IP address: {interface_ip}")
        app.run(debug=True, host=interface_ip, port=UE1port)
    else:
        # Print an error message and exit if the IP address is not found
        print("Could not find the IP address for the interface. Exiting.")