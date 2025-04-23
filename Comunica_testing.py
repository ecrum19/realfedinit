import os
import subprocess
import argparse

def execute_queries(directory_path):
    """
    Iterate through all files in a directory, read each file as a query,
    and execute a CLI command with that query.

    Parameters:
    - directory_path: Path to the directory containing query files.
    - cli_command_template: Command with '{}' as placeholder for the query.
    """
    for filename in os.listdir(directory_path)[:1]:
        file_path = os.path.join(directory_path, filename)
        sources = getSources(open(file_path, 'r'))
        
        # Format the CLI command
        base_command = f"node ../comunica/engines/query-sparql/bin/query.js "
        for source in sources:
            fixed_source = source.strip('\n')
            base_command += f"{source} "
        
        base_command += f"-f {file_path} -t stats"
        try:
            print(f"Executing: {base_command}")
            result = subprocess.run(base_command, shell=True, check=True, text=True, capture_output=True)
            print("Output:\n", result.stdout)
        except subprocess.CalledProcessError as e:
            print(f"Error executing command for {filename}: {e.stderr}")

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