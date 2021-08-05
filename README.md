# Stress Testing

## Installation steps
Step 1: Cloning of git repository
>> git clone https://github.com/SainMohit/StressTesting.git

Step 2: Creation of virtual environment
>> python3 -m venv venv

Step 3: Activate virtual environment
>> source venv\bin\activate

Step 4: Install python dependencies
>> pip install -r requirements.txt

Step 5: Run Locust Server
>> locust -f locustfile.py


## Output

To view output open browser and put below link

http://{server_ip}:8089

Please make sure 8089 port is open so you can access locust web ui.