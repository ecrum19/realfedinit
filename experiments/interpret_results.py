import os
import re
import json
import argparse
import pandas as pd

def query_times(file_path, print_output):
    data = []

    with_results = 0
    with_no_results = 0
    with_error = 0
    TimeoutError = 0
    other_errors = []

    cols = pd.read_csv(file_path, sep=';', nrows=0).columns.tolist()
    cols_to_use = [col for col in cols if col != 'timestampsAll']
    df = pd.read_csv(file_path, sep=';', usecols=cols_to_use)
    
    if print_output:
        print(f"{'name':10} | {'error':10} | {'results':10} | {'httpRequests':10} | {'time':10}")
        print("-" * 60)
    for _, row in df.iterrows():
        if str(row.get("error", "")).lower() in ("true", "false"):
            raw_name = str(row.get("name", "")).strip()

            # Extract number from name
            # TODO: differentiate between 19 and 19...
            if raw_name == "emi#examples018_ns":
                name = "018e"
            else:    
                match = re.search(r'\b(\d+[a-zA-Z]?)\b', raw_name)
                if match is None:
                    match = re.search(r'(\d+[a-zA-Z]?)', raw_name)
                name = match.group(1) if match else raw_name

            # Error column
            error = str(row.get("error", "")).lower()
            if error == "true":
                with_error += 1
                results = -1
                if 'unexpected' in str(row.get("errorDescription", "")).lower():
                    TimeoutError += 1
                else:
                    other_errors.append({
                        "name": name,
                        "errorDescription": row.get("errorDescription", "")
                    })


            # Results column
            if error == "false":
                try:
                    results = int(row.get("results"))
                except (ValueError, TypeError):
                    results = -1
                if results > -1:
                    if results == 0:
                        with_no_results += 1
                    else:
                        with_results += 1

            # httpRequests column
            try:
                http_requests = int(row.get("httpRequests") or -1)
            except (ValueError, TypeError):
                http_requests = -1

            # Time column
            try:
                time = float(row.get("time") or -1)
            except (ValueError, TypeError):
                time = -1

            # Store processed data
            data.append({
                "query": name,
                "results": results,
                "error": error,
                "httpRequests": http_requests,
                "time": time
            })

    data = sorted(data, key=lambda x: x['results'], reverse=True)
    if print_output:
        for item in data:
            # Print outputs
            print(f"{item.get('query', ''):10} | {item.get('error', ''):10} | {item.get('results', ''):10} | {item.get('httpRequests', ''):10} | {item.get('time', ''):10}")
        print("-" * 60)
        print(f"Total queries: {len(data)}")
        print(f"Queries with results: {with_results}")
        print(f"Queries with no results: {with_no_results}")
        print(f"Queries with error: {with_error}")
        print(f"  Queries with TimeoutError: {TimeoutError}")
        print(f"  Queries with other errors: {len(other_errors)}")
        for i in other_errors:
            print(f"    Query {i['name']}: {i['errorDescription']}")
    return data


def sparql_endpoint_comunica(file_path, print_output):
    split_query_pattern = "Received query query:"
    split_within_query_pattern = 'Worker'
    identify_crash = 'Virtuoso 42000 Error SR452: Error in accessing temp file'

    all_queries = []
    current_query = []
    current_http = []
    current_source = ""
    source_request_list = {}
    select_statement = ""
    
    crash_query = {}
    found_crash = False
    crash_reported = False
    crash_index = 0

    within_query = False
    within_http = False
    within_query_tracker = False
    location = 0

    all_queries_local = []
    queries_dir = f"{os.getcwd()}/no-service/input/queries/"
    num_queries = 0
    # read in all query files for matching
    for file in os.listdir(queries_dir):
        # no-service queries
        if 'no-service' in file_path and 'ns' in file:
            with open(queries_dir + file, 'r', encoding='utf-8') as q:
                all_queries_local.append({
                    "query": q.read(),
                    "id": file[:-3]
                })
                num_queries += 1
        # service queries
        elif 'default' in file_path and 'ns' not in file:
            with open(queries_dir + file, 'r', encoding='utf-8') as q:
                all_queries_local.append({
                    "query": q.read(),
                    "id": file[:-3]
                })
                num_queries += 1
    
    # read in the log file
    with open(file_path, 'r', encoding='utf-8') as nf:
        f = nf.readlines()
        for line in f:
            line = line.rstrip()
            # start of a new query
            if split_query_pattern in line:
                source_list = line.split("# Datasources: ")[1].split(' ')
                # instance of the split between queries (not at the beginning of file)
                if (len(current_query) > 0) & (len(current_http) > 0):
                    all_queries.append({
                        "query": current_query,
                        "select": select_statement,
                        "http_requests": current_http,
                        "source_requests": source_request_list,
                        "sources": source_list
                    })
                    # finding where Biosoda endpoint crashed within workflow
                    if found_crash and not crash_reported:
                        crash_reported = True
                        crash_index = len(all_queries)-1
                        crash_query = {
                            "query": current_query,
                            "select": select_statement,
                            "http_requests": current_http,
                            "source_requests": source_request_list,
                            "sources": source_list
                        }
                current_query = []
                current_http = []
                source_request_list = {}
                within_query = True
                within_http = False

            # end of a query / start of HTTP requests    
            elif split_within_query_pattern in line:
                within_query = False
                within_http = True
                within_query_tracker = False

            # adds the body of the query to current_query 
            elif within_query:
                if "PREFIX" in line and not within_query_tracker:
                    within_query_tracker = True
                    select_statement = line
                elif within_query_tracker:
                    select_statement = select_statement + '\n' + line
                current_query.append(line)

            # adds the HTTP requests to current_http
            elif within_http:
                if identify_crash in line:
                    found_crash = True
                if 'INFO: Requesting' in line:
                    # counting source-specific requests
                    current_source = line.split("INFO: Requesting ")[1].split(" ")[0]
                    if current_source not in source_request_list:
                        source_request_list[current_source] = 1
                    else:
                        source_request_list[current_source] += 1
                    current_http.append(line)
                
            else:
                location += 1
                continue
            
            # adds last query to all_queries
            if location == len(f)-1:
                all_queries.append({
                    "query": current_query,
                    "select": select_statement,
                    "http_requests": current_http,
                    "source_requests": source_request_list,
                    "sources": source_list
                })
            location += 1
    
    match = ""
    if print_output:
        print(f"Number of queries: {len(all_queries)}")
        print(f"{'~HTTP requests':15} | {'query file name':10}")
        print("-" * 60)
    # iter over queries identified to match them with the query ids
    all_queries_sorted = sorted(all_queries, key=lambda x: len(x['http_requests']), reverse=True)
    iter_location = 0
    for query in all_queries_sorted:
        search_term = normalize_query(query.get("select", "").strip())
        match = ""
        for item in all_queries_local:
            normalized_item_query = normalize_query(item.get("query", ""))
            if search_term in normalized_item_query:
                match = item.get("id", "")
                break  # Stop searching once a match is found

        # Add the match field to the query object
        query["match"] = match

        if print_output:
            print(f"{len(query['http_requests']):15} |", query['match'])
        iter_location += 1
    # print crash details
    if print_output:
        print("-" * 60)
        if crash_reported:
            print(f"Query that encounters crash: {all_queries[crash_index]['match']}")
            for i in range(crash_index-1, -1, -1):
                if all_queries[i]["sources"].count("https://biosoda.unil.ch/emi/sparql") > 0:
                    print(f"Query that caused crash: {all_queries[i]['match']}")
                    for key in all_queries[i].get('source_requests', ''):
                        print(f"  Source: {key} | Requests: {all_queries[i].get('source_requests', '')[key]}")
                    break
    return all_queries_sorted

def normalize_query(query):
    """
    Normalize a query string by removing extra whitespace, line breaks, and ensuring consistent formatting.
    """
    return re.sub(r'\s+', ' ', query.strip())

def write_summary_to_file(query_times, sparql_endpoint_log, outfile):
    """
    Write a summary of query times and SPARQL endpoint logs to a file with uniform column sizes and centered content.
    """
    with open(outfile, 'w') as f:
        # Define column widths
        col_widths = {
            "name": 15,
            "error": 10,
            "results": 10,
            "httpRequests": 15,
            "time": 10,
            "query_file_name": 20,
            "total_http_requests": 20,
            "source_requests": 55,
            "match_max_width": 15  # Maximum width for the 'match' value
        }

        # Write header for Query Times Summary
        f.write("Query Times Summary:\n")
        f.write(
            f"{'name'.center(col_widths['name'])} | {'error'.center(col_widths['error'])} | "
            f"{'results'.center(col_widths['results'])} | {'httpRequests'.center(col_widths['httpRequests'])} | "
            f"{'time'.center(col_widths['time'])}\n"
        )
        f.write("-" * (sum(col_widths.values()) - col_widths['match_max_width'] - col_widths['total_http_requests'] - col_widths['source_requests'] + 12) + "\n")
        for item in query_times:
            f.write(
                f"{item.get('query', '').center(col_widths['name'])} | {item.get('error', '').center(col_widths['error'])} | "
                f"{str(item.get('results', '')).center(col_widths['results'])} | {str(item.get('httpRequests', '')).center(col_widths['httpRequests'])} | "
                f"{str(item.get('time', '')).center(col_widths['time'])}\n"
            )
        f.write("-" * (sum(col_widths.values()) - col_widths['match_max_width'] - col_widths['total_http_requests'] - col_widths['source_requests'] + 12) + "\n")
        f.write(f"Total queries: {len(query_times)}\n")
        f.write(f"Queries with results: {sum(1 for i in query_times if i['results'] > 0)}\n")
        f.write(f"Queries with no results: {sum(1 for i in query_times if i['results'] == 0)}\n")
        f.write(f"Queries with error: {sum(1 for i in query_times if i['error'] == 'true')}\n")
        f.write("\n\n")

        # Write header for SPARQL Endpoint Logs Summary
        f.write("Comunica SPARQL Endpoint Log Summary:\n")
        f.write(
            f"{'query file name'.center(col_widths['query_file_name'])} | {'Total HTTP requests'.center(col_widths['total_http_requests'])} | "
            f"{'Source: HTTP requests'.center(col_widths['source_requests'])}\n"
        )
        f.write("-" * (sum(col_widths.values())) + "\n")
        for item in sparql_endpoint_log:
            # Truncate the 'match' value if it exceeds the max width
            match_value = item.get('match', '')
            if len(match_value) > col_widths['match_max_width']:
                if "emi#examples018" in match_value:
                    match_value = "018e"
                elif "emi#examples" in match_value:
                    match_value = match_value[len("emi#examples"):-3]
                elif 'Q' in match_value:
                    match_value = match_value[1:-3]
                else:
                    match_value = match_value.split('_')[0] # for uniprot queries
            else:
                match_value = match_value[:-3]

            # Format the line with consistent column widths
            line = f"{match_value.ljust(col_widths['query_file_name'])} | {str(len(item.get('http_requests', ''))).center(col_widths['total_http_requests'])}"
            for source, requests in item.get('source_requests', {}).items():
                line += f" | {f'{source}: {requests}'.center(col_widths['source_requests'])}"
            line += "\n"
            f.write(line)
        f.write("-" * (sum(col_widths.values())) + "\n")
        f.write(f"Total queries: {len(sparql_endpoint_log)}\n")
        f.write("\n")

        print(f"Summary written to {outfile}")

# usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse experiment query-times.csv results.")
    parser.add_argument("-q", "--query-times", required=False, help="Path to the 'query-times.csv' file (semicolon-delimited)")
    parser.add_argument("-s", "--sparql-endpoint", required=False, help="Path to the '/logs/sparql-endpoint-comunica.txt' file (tab delimited)")
    parser.add_argument("-o", "--output-file", required=False, help="Path to the output summary text file")
    args = parser.parse_args()

    if args.sparql_endpoint and args.query_times and args.output_file:
        total_queries = 0
        q = query_times(args.query_times, print_output=False)
        s = sparql_endpoint_comunica(args.sparql_endpoint, print_output=False)
        
        if args.output_file:
            write_summary_to_file(q, s, args.output_file)
        
        ## code to determine the number of queries identified in the query-times.csv and sparql-endpoint-comunica.txt log
        # print(len(q), len(s))
        # for qitem in q:
        #     qname = qitem['query']
        #     found = False
        #     location = 0
        #     for sitem in s:
        #         if qname in sitem['match'][:-3]:
        #             # print(f"{qname}: included")
        #             total_queries += 1
        #             found = True
        #             break
        #         elif qname == "18a" and sitem['match'] == "emi#examples018_ns":
        #             # print(f"{qname}: included")
        #             total_queries += 1
        #             found = True
        #             break
        #         if not found and location == len(s)-1:
        #             print(f"{qname}: not included")
        #             break
        #         location += 1
        # print(f"Total queries: {total_queries}")
    elif args.query_times:
        q = query_times(args.query_times, print_output=True)
    elif args.sparql_endpoint:
        s = sparql_endpoint_comunica(args.sparql_endpoint, print_output=True)
    else:
        print("Please provide either --query-times (-q) or --sparql-endpoint (-s).")