import csv
import re
import os
import argparse

def query_times(file_path):
    data = []

    with open(file_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile, delimiter=';')
        
        # for table output
        print(f"{'Name':10} | {'error':10} | {'results':10} | {'httpRequests':10} | {'time':10}")
        print("-" * 60)

        for row in reader:
            raw_name = row.get("name", "").strip()

            if 'input/' in raw_name:
                # display query name as just a number
                match = re.search(r'\b(\d+[a-zA-Z]?)\b', raw_name)
                if match == None:
                    match = re.search(r'(\d+[a-zA-Z]?)', raw_name)
                name = match.group(1) if match else raw_name

                # error column
                error = row.get("error", "")
                
                #results column
                try:
                    results = int(row.get("results") or -1)
                except (ValueError, TypeError):
                    results = -1
                
                # httpRequests column
                try:
                    http_requests = int(row.get("httpRequests") or -1)
                except (ValueError, TypeError):
                    http_requests = -1
                
                # time column
                try:
                    time = float(row.get("time") or -1)
                except (ValueError, TypeError):
                    time = -1

                # result row added to list of results
                data.append({
                    "query": name,
                    "results": results,
                    "error": error,
                    "httpRequests": http_requests,
                    "time": time
                })
                print(f"{name:10} | {error:10} | {results:10} | {http_requests:10} | {time}")


def sparql_endpoint_comunica(file_path):
    split_query_pattern = "[200] GET to /sparql"
    split_within_query_pattern = 'Worker'

    all_queries = []
    current_query = []
    current_http = []

    within_query = False
    within_http = False
    location = 0
    
    with open(file_path, 'r', encoding='utf-8') as nf:
        f = nf.readlines()
        for line in f:
            line = line.rstrip()
            # start of a new query
            if split_query_pattern in line:
                if (len(current_query) > 0) & (len(current_http) > 0):
                    all_queries.append({
                        "query": current_query,
                        "http_requests": current_http
                    })
                current_query = []
                current_http = []
                within_query = True
                within_http = False
                
            elif split_within_query_pattern in line:
                within_query = False
                within_http = True

            elif within_query:
                current_query.append(line)

            elif within_http:
                current_http.append(line)
            else:
                print(f"Unexpected line: {line}")
                
            if location == len(f) - 1:
                all_queries.append({
                    "query": current_query,
                    "http_requests": current_http
                })
            location += 1
    
    print(f"{'Query':10} | {'Approx. HTTP requests':20}")
    print("-" * 30)
    for query in all_queries:
        print(f"{all_queries.index(query)+1:10} | {len(query['http_requests']):20}")
    return all_queries


# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse experiment query-times.csv results.")
    parser.add_argument("-q", "--query-times", required=False, help="Path to the 'query-times.csv' file (semicolon-delimited)")
    parser.add_argument("-s", "--sparql-endpoint", required=False, help="Path to the '/logs/sparql-endpoint-comunica.txt' file (tab delimited)")
    args = parser.parse_args()

    if args.query_times:
        query_times(args.query_times)
    elif args.sparql_endpoint:
        sparql_endpoint_comunica(args.sparql_endpoint)
    else:
        print("Please provide either --query-times or --sparql-endpoint.")