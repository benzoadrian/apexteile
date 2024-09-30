from django.shortcuts import render
from .forms import SearchForm
import boto3
import time
from concurrent.futures import ThreadPoolExecutor
from decouple import config
import os

# Initialize a session using environment variables for AWS credentials
session = boto3.Session(
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY'),
    region_name=os.getenv('AWS_REGION')
)

athena_client = session.client('athena')  # Create the Athena client using this session

def search_view(request):
    price_results = []
    description_results = []
    stock_results = []  # For multiple warehouse and availability results

    if request.method == 'POST':
        form = SearchForm(request.POST)
        if form.is_valid():
            ic_index = form.cleaned_data['ic_index']

            # Query execution functions
            def execute_query(query, database):
                response = athena_client.start_query_execution(
                    QueryString=query,
                    QueryExecutionContext={'Database': database},
                    ResultConfiguration={'OutputLocation': 's3://apexteilecsv/'}
                )
                query_execution_id = response['QueryExecutionId']
                
                # Wait for the query to complete
                while True:
                    query_execution = athena_client.get_query_execution(QueryExecutionId=query_execution_id)
                    status = query_execution['QueryExecution']['Status']['State']
                    if status in ['SUCCEEDED', 'FAILED', 'CANCELLED']:
                        break
                    time.sleep(1)
                
                # If the query succeeded, fetch the results
                if status == 'SUCCEEDED':
                    return athena_client.get_query_results(QueryExecutionId=query_execution_id)
                return None

            # Prepare queries
            price_query = f'SELECT wholesale_net_price FROM "apexteile_wholesalepricing_database"."apexteile_wholesalepricing" WHERE ic_index = \'{ic_index}\''
            description_query = f'SELECT description FROM "apexteile_productinformation_database"."apexteile_productinformation" WHERE ic_index = \'{ic_index}\''
            stock_query = f'SELECT warehouse, availability FROM "apexteile_stock_database"."apexteile_stock" WHERE ic_index = \'{ic_index}\''

            # Run queries in parallel
            with ThreadPoolExecutor() as executor:
                futures = {
                    'price': executor.submit(execute_query, price_query, 'apexteile_wholesalepricing_database'),
                    'description': executor.submit(execute_query, description_query, 'apexteile_productinformation_database'),
                    'stock': executor.submit(execute_query, stock_query, 'apexteile_stock_database')
                }

                # Collect results
                price_result = futures['price'].result()
                description_result = futures['description'].result()
                stock_result = futures['stock'].result()

            # Process the price result
            if price_result:
                try:
                    price_results.append(price_result['ResultSet']['Rows'][1]['Data'][0]['VarCharValue'])
                except IndexError:
                    price_results.append('No price found for the entered ic_index.')

            # Process the description result
            if description_result:
                try:
                    description_results.append(description_result['ResultSet']['Rows'][1]['Data'][0]['VarCharValue'])
                except IndexError:
                    description_results.append('No description found for the entered ic_index.')

            # Process the stock results
            if stock_result:
                for row in stock_result['ResultSet']['Rows'][1:]:  # Skip the header row
                    stock_data = row['Data']
                    try:
                        warehouse = stock_data[0]['VarCharValue']
                        availability = stock_data[1]['VarCharValue']
                        stock_results.append({'warehouse': warehouse, 'availability': availability})
                    except IndexError:
                        stock_results.append({'warehouse': 'Unknown', 'availability': 'Unknown'})
    
    else:
        form = SearchForm()

    return render(request, 'queries/search.html', {
        'form': form, 
        'price_results': price_results, 
        'description_results': description_results, 
        'stock_results': stock_results
    })

