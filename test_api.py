import requests
import json
from datetime import datetime, timedelta

# this file is used to test the CIMIS API. not part of the homework

api_key = '1b89487e-3945-4c58-8545-94b9c35d6a26'

def get_humidity_from_CIMIS(app_key, targets, start_date, end_date) -> list:
    # TODO: implement function to retrieve humidity data from CIMIS system
    base_url = 'http://et.water.ca.gov/api/data'
    params = {
        'appKey': app_key,
        'targets': targets,
        'startDate': start_date,
        'endDate': end_date
    }

    response = requests.get(base_url, params=params)

    # Check if the request was successful
    if response.status_code == 200:
        print(response.text)
        # Load the data as JSON
        data = json.loads(response.text)
        
        # Get the 'Providers' list
        providers = data.get('Data', {}).get('Providers', [])
        
        # Initialize an empty list to store the DayRelHumAvg values
        day_rel_hum_avg_values = []

        # Iterate over each provider
        for provider in providers:
            # Get the 'Records' list
            records = provider.get('Records', [])
            
            # Iterate over each record
            for record in records:
                # Get the 'DayRelHumAvg' value
                day_rel_hum_avg = record.get('DayRelHumAvg', {}).get('Value')
                
                # If 'DayRelHumAvg' value exists, add it to the list
                if day_rel_hum_avg is not None:
                    day_rel_hum_avg_values.append(day_rel_hum_avg)

        return int(day_rel_hum_avg_values[0])

    else:
        print(f"Request failed with status code {response.status_code}")
        return None
    
if __name__ == '__main__':
    now = datetime.now() - timedelta(days=1)
    formatted_date = now.strftime('%Y-%m-%d')
    print(formatted_date)
    print(get_humidity_from_CIMIS(api_key, '75', '2023-01-01', '2023-01-01'))