import os
import subprocess

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
            base_command += f"{source} "
        
        base_command += f"-f {file_path} -t stats"
        print(f"{base_command}")
        # try:
        #     print(f"Executing: {base_command}")
        #     result = subprocess.run(base_command, shell=True, check=True, text=True, capture_output=True)
        #     print("Output:\n", result.stdout)
        # except subprocess.CalledProcessError as e:
        #     print(f"Error executing command for {filename}: {e.stderr}")

def getSources(query_file):
    """
    Function to get the sources for the CLI command.
    This is a placeholder and should be replaced with actual logic to retrieve sources.
    """
    f = query_file.readlines()
    return f[1].split("# Datasources: ")[1].split(' ')

# Example usage
if __name__ == "__main__":
    queries_dir = "/experiments/input/queries"

    execute_queries(queries_dir)