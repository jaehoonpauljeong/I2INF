from flask import Flask, request, Response  # Import necessary components from the Flask framework.
import xml.etree.ElementTree as ET  # Import XML handling library for creating XML data.
import xml.dom.minidom  # Import for pretty-printing XML.
import requests  # Import requests library to send HTTP requests.
import threading  # Import threading to manage multiple threads.
import subprocess  # Import subprocess to execute shell commands.
import re  # Import regular expressions library to match text patterns.

app = Flask(__name__)  # Initialize the Flask application.


# Dictionary containing IP addresses and ports for two vehicles.
vehicle_database = {
    "vehicle_1": {"ip_address": "10.60.0.9", "port": 8080},
    "vehicle_2": {"ip_address": "10.60.0.8", "port": 8081}
}

# Destination info
destination_info = {"ip_address": "203.50.23.1", "port": 7777}


# Function to create an XML policy with source, destination, and action.
def create_policy_xml(src_ip, dst_ip, action):
    policy = ET.Element('policy')  # Create the root element.
    ET.SubElement(policy, 'src').text = src_ip  # Add a source element.
    ET.SubElement(policy, 'dst').text = dst_ip  # Add a destination element.
    ET.SubElement(policy, 'action').text = action  # Add an action element.
    return ET.tostring(policy, encoding='unicode')  # Convert the XML tree to a string.

# Function to pretty print XML strings.
def pretty_print_xml(xml_str):
    xml_dom = xml.dom.minidom.parseString(xml_str)  # Parse the XML string.
    return xml_dom.toprettyxml()  # Return a nicely formatted XML string.

# Function to send a message to a specified vehicle.
def send_message_to_vehicle(vehicle_id, message):
    vehicle_info = vehicle_database.get(vehicle_id)  # Retrieve vehicle info from the database.
    if vehicle_info:
        url = f"http://{vehicle_info['ip_address']}:{vehicle_info['port']}/receive_message"  # Create URL.
        try:
            response = requests.post(url, data=message, headers={'Content-Type': 'application/xml'})
            print("==============")
            print(f"Sent message to {vehicle_id} at {url}: {response.status_code}")  # Log response status.
            print(pretty_print_xml(message))  # Print the formatted XML message.
        except requests.exceptions.RequestException as e:
            print(f"Failed to send message to {vehicle_id} at {url}: {e}")  # Handle request exceptions.


# Flask route to handle incoming messages on the '/send_message' endpoint.
@app.route('/send_message', methods=['POST'])
def send_message():
    file = request.files['file']  # Access the file sent in the request.
    xml_data = file.read().decode('utf-8')  # Read and decode the file content.
    print("\n")
    print("=========new message start=========")
    print("Received XML:")  # Log that XML was received.
    print(xml_data)  # Print the received XML data.

    # Generate messages to send to each vehicle.
    message1 = create_policy_xml(vehicle_database["vehicle_1"]["ip_address"], destination_info["ip_address"], "remote-speech")
    message2 = create_policy_xml(vehicle_database["vehicle_2"]["ip_address"], destination_info["ip_address"], "remote-speech")

    # Create threads for sending messages concurrently.
    threads = []
    threads.append(threading.Thread(target=send_message_to_vehicle, args=("vehicle_1", message1)))
    threads.append(threading.Thread(target=send_message_to_vehicle, args=("vehicle_2", message2)))

    # Start all threads.
    for thread in threads:
        thread.start()

    # Wait for all threads to complete.
    for thread in threads:
        thread.join()

    return Response("Messages processed", mimetype='text/plain'), 200  # Return a successful response.

# Function to retrieve the IP address from the 'uesimtun0' network interface.
def get_ip_address(interface_name='uesimtun0'):
    """ Retrieve IP address from ifconfig based on the interface name. """
    try:
        cmd_result = subprocess.run(['ifconfig', interface_name], capture_output=True, text=True)  # Execute ifconfig.
        ip_pattern = r'inet (\d+\.\d+\.\d+\.\d+)'  # Regex pattern for matching an IP address.
        ip_match = re.search(ip_pattern, cmd_result.stdout)  # Search for the IP pattern.
        return ip_match.group(1) if ip_match else None  # Return the matched IP address or None.
    except subprocess.CalledProcessError:
        print("Failed to get IP address")  # Handle errors in the subprocess.
        return None

# Main block to start the Flask app.
if __name__ == '__main__':
    ip_address = get_ip_address()  # Get the IP address of the specified interface.

    if ip_address:
        print(f"Running on IP: {ip_address}")  # Log the IP address.
        app.run(debug=True, host=ip_address, port=5000)  # Start the app on the retrieved IP address.
    else:
        print("No IP address found for interface uesimtun0. Exiting.")  # Exit if no IP address is found.

