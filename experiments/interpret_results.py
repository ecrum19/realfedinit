import csv
import re
import os
import argparse

def interpret_results(file_path):
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

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Parse experiment query-times.csv results.")
    parser.add_argument("-i", "--input", required=True, help="Path to the CSV input file (semicolon-delimited)")
    args = parser.parse_args()

    parsed_data = interpret_results(args.input)