import os
import subprocess
import argparse
import datetime

def execute_queries(directory_path):
    """
    Iterate through all files in a directory, read each file as a query,
    and execute a CLI command with that query.

    Parameters:
    - directory_path: Path to the directory containing query files.
    - cli_command_template: Command with '{}' as placeholder for the query.
    """

    output_log_path = os.path.join(os.getcwd(), "output.log")
    with open(output_log_path, "a", encoding="utf-8") as log_file:
        for filename in os.listdir(directory_path):
            file_path = os.path.join(directory_path, filename)
            sources = getSources(open(file_path, 'r'))
            # Format the CLI command
            base_command = f"node ../comunica/engines/query-sparql/bin/query-dynamic.js "
            for source in sources:
                if source != "":
                    fixed_source = source.replace('\n', '')
                    base_command += f"{fixed_source} "
            base_command += f"-f {file_path} -t 'application/sparql-results+json' --httpRetryCount=2"
            start_time = datetime.datetime.now()
            log_file.write(f"Executing: {base_command}\n")
            log_file.write(f"Timestamp (start): {start_time.isoformat()}\n")
            try:
                result = subprocess.run(base_command, shell=True, check=True, text=True, capture_output=True)
                log_file.write("Output:\n" + result.stdout + "\n")
            except subprocess.CalledProcessError as e:
                log_file.write(f"Error executing command for {filename}: {e.stderr}\n")
            end_time = datetime.datetime.now()
            log_file.write(f"Timestamp (end): {end_time.isoformat()}\n\n")
        

def getSources(query_file):
    """
    Function to get the sources for the CLI command.
    This is a placeholder and should be replaced with actual logic to retrieve sources.
    """
    f = query_file.readlines()
    return f[0].split("# Datasources: ")[1].split(' ')

# Example usage
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run Comunica tests script.")
    parser.add_argument("-q", "--queries", type=str, required=True, help="Directory containing query files.")
    args = parser.parse_args()

    execute_queries(args.queries)