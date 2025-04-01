import os
import sys

class Config:
    def __init__(self, optimize_config, join_config, rate_config):
        self.metadata_config = optimize_config
        self.join_config = join_config
        self.rate_config = rate_config

class Config_Direstories:
    def __init__(self, optimize_dir, void_dir, join_dir, rate_dir):
        self.optimize_files = optimize_dir
        self.void_files = void_dir
        self.join_files = join_dir
        self.rate_files = rate_dir

def listFilePaths(directory):
    """Return a sorted list of file paths in the given directory."""
    return sorted(
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if os.path.isfile(os.path.join(directory, f))
    )

def getConfigDirectories(top_directory):
    """Return a list of the different config directories."""
    return [d for d in os.listdir(top_directory) if os.path.isdir(os.path.join(top_directory, d)) and d[0] != '.']
    

def get_base_url(file_path):
    last_slash = file_path.rfind('/')
    return file_path[last_slash+1:]

def get_base_name(file_with_ext):
    dot = file_with_ext.rfind('.')
    return file_with_ext[:dot]

def listConfigFiles(filePaths):
    """Return a list of config files names (with file extension)."""
    files_list = []
    for f in filePaths:
        files_list.append(get_base_url(f))
    return files_list

def listConfigNames(files):
    """Return a list of config names (no file extension)"""
    names_list = []
    for f in files:
        names_list.append(get_base_name(f))
    return names_list

def new_config(current_config_path, new_option_line, new_algo_line, new_rate_line, output_file):
    """
    Replaces the line that contains 
    "ccqs:config/optimize-query-operation/actors.json",
    with the new_line provided.
    
    Parameters:
      default_config_path (str): Path to the default config JSON file.
      new_line (str): The new line to replace the target line.
      output_file (str): File path to write the modified content.
    """
    # Determine the search strings based on the new_option_line
    if 'VoID' in new_option_line:
        search_option_string = '"ccqs:config/rdf-metadata-extract/actors.json",'
    else:
        search_option_string = '"ccqs:config/optimize-query-operation/actors.json",'
    search_algo_string = '"ccqs:config/rdf-join/actors.json",'
    search_rate_string = '"ccqs:config/http/actors.json",'

    
    # Read the default config file line by line.
    with open(current_config_path, 'r') as f:
        lines = f.readlines()
    
    # Create a new list of lines with the target lines replaced.
    updated_lines = []
    for line in lines:
        # for option config
        if search_option_string in line:
            updated_lines.append(new_option_line if new_option_line.endswith('\n') else new_option_line + '\n')
        # for algo config
        elif search_algo_string in line:
            updated_lines.append(new_algo_line if new_algo_line.endswith('\n') else new_algo_line + '\n')
        # rate limit config
        elif search_rate_string in line:
            updated_lines.append(new_rate_line if new_rate_line.endswith('\n') else new_rate_line + '\n')
        # all other lines
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(output_file, 'w') as f:
        f.writelines(updated_lines)


def determinePermutations(algorithms, options, rates):
    """
    Returns all config file permutations as a list of Objects
    """
    combinations = []
    # default w/ rate-limit for initialization
    combinations.append(Config(
        optimize_config="def-count",
        join_config="default",
        rate_config="rate-on"
    ))

    # VoID + default w/ rate-limit for initialization
    combinations.append(Config(
        optimize_config="with-VoID",
        join_config="default",
        rate_config="rate-on"
    ))

    # aggfp+ask + default w/o rate-limit for initialization
    combinations.append(Config(
        optimize_config="aggfp-ask",
        join_config="default",
        rate_config="rate-off"
    ))

    # for r in rates:
    #     for a in algorithms:
    #         for o in options:
    #             combinations.append(Config(
    #                 optimize_config=o,
    #                 join_config=a,
    #                 rate_config=r
    #             ))
    return combinations


def writeClientConfigs(in_path, algorithm_names, option_names, rate_names, algoithm_files, option_files, rate_files, config_combos):
    """
    creates new client config files with the changes based on permutations
    """
    default_config = "../config/default.json"
    output_path = f"{in_path}client-config/"
    for combo in config_combos:
        # name of the current configs
        wanted_option = combo.metadata_config
        wanted_algo = combo.join_config
        wanted_rate = combo.rate_config

        # indexes of the current configs
        option_index = option_names.index(wanted_option)
        algo_index = algorithm_names.index(wanted_algo)
        rate_index = rate_names.index(wanted_rate)

        # the lines that will be replaced in the config file
        wanted_option_config = f'\t\t"{option_files[option_index]}",'
        wanted_algo_config = f'\t\t"{algoithm_files[algo_index]}",'
        wanted_rate_config = f'\t\t"{rate_files[rate_index]}",'

        # file name change
        outfile = f"{output_path}{wanted_option}_{wanted_algo}_{wanted_rate}.json"
        new_config(default_config, wanted_option_config, wanted_algo_config, wanted_rate_config, outfile)


def changeExptTemplate(algo_path, option_path, void_path, rate_path, algo_configs, option_configs, rate_configs, current_template_file):
    """
    creates new client config files with the new config files in the "additionalBinds" parameter for permutations
    """
    with open(current_template_file, 'r') as f:
        lines = f.readlines()

    algo_split = algo_path.split('/')
    option_split = option_path.split('/')
    void_split = void_path.split('/')
    rate_split = rate_path.split('/')
    algo_input_path = '/'.join(algo_split[1:])
    option_input_path = '/'.join(option_split[1:])
    void_input_path = '/'.join(void_split[1:])
    rate_input_path = '/'.join(rate_split[1:])

    target_line = '"additionalBinds": [],'
    # Create a new list of lines with the target lines replaced.
    updated_lines = []
    for line in lines:
        
        # find targeted line config
        if target_line in line:
            updated_lines.append('\t"additionalBinds": [\n')
            # add algorithm configs
            for afile in algo_configs:
                updated_lines.append(f'\t\t"/{algo_input_path}/{afile}:/tmp/{afile}",\n')
            # add option configs
            for ofile in option_configs:
                #special case for VoID config
                if "VoID" in ofile:
                    updated_lines.append(f'\t\t"/{void_input_path}/{ofile}:/tmp/{ofile}",\n')
                else:
                    updated_lines.append(f'\t\t"/{option_input_path}/{ofile}:/tmp/{ofile}",\n')
            for rfile in rate_configs:
                # include comma for all but last file
                if rate_configs.index(rfile) < len(rate_configs)-1:
                    updated_lines.append(f'\t\t"/{rate_input_path}/{rfile}:/tmp/{rfile}",\n')
                else:
                    updated_lines.append(f'\t\t"/{rate_input_path}/{rfile}:/tmp/{rfile}"\n')
            updated_lines.append("\t],\n")
        
        # change replication number
        elif '"queryRunnerReplication":' in line:
            updated_lines.append('\t"queryRunnerReplication": 1,\n')

        # change queryRunnerRecordTimestamps and queryRunnerRecordHttpRequests
        elif 'queryRunnerEndpointAvailabilityCheckTimeout' in line:
            updated_lines.append(line)
            updated_lines.append('\t"queryRunnerRecordTimestamps": true,\n')
            updated_lines.append('\t"queryRunnerRecordHttpRequests": true,\n')

        # specify configs to use for experiment
        elif '"configClient":' in line:
            updated_lines.append('\t"configClient": "input/client-config/%FACTOR-type%.json",\n')
            
        # all other lines
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(current_template_file, 'w') as f:
        f.writelines(updated_lines)


def changeCombJson(current_comb_file, combos_added):
    """
    creates new jbr-combinations.json file with the new configs specified in the "type" parameter
    """
    with open(current_comb_file, 'r') as f:
        lines = f.readlines()

    target_line = '"factors":'
    # Create a new list of lines with the target lines replaced.
    updated_lines = []
    trailing_parenthesis = False
    for line in lines:
        
        # find targeted line config
        if target_line in line:
            updated_lines.append('\t"factors": {\n')
            updated_lines.append('\t\t"type": [ ')
            # add combos to the list
            for comb in combos_added:
                file_name = f"{comb.metadata_config}_{comb.join_config}_{comb.rate_config}"
                if combos_added.index(comb) < len(combos_added)-1:
                    updated_lines.append(f'"{file_name}", ')
                else:
                    updated_lines.append(f'"{file_name}" ]\n')

            updated_lines.append("\t}\n")
        # all other lines
        elif '"type":' in line:
            trailing_parenthesis = True
        elif trailing_parenthesis:
            trailing_parenthesis = False
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(current_comb_file, 'w') as f:
        f.writelines(updated_lines)

def changeExptJsonService(current_template_file):
    """
    makes changes to jbr-experiment.json file
    """
    with open(current_template_file, 'r') as f:
        lines = f.readlines()

    updated_lines = []
    for line in lines:
        if '"queryRunnerReplication":' in line:
            updated_lines.append('\t"queryRunnerReplication": 1,\n')

        # change queryRunnerRecordTimestamps and queryRunnerRecordHttpRequests
        elif 'queryRunnerEndpointAvailabilityCheckTimeout' in line:
            updated_lines.append(line)
            updated_lines.append('\t"queryRunnerRecordTimestamps": true,\n')
            updated_lines.append('\t"queryRunnerRecordHttpRequests": true,\n')
            
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(current_template_file, 'w') as f:
        f.writelines(updated_lines)


def changeClientConfigService(config_client_path):
    """
    changes cofig-client.json file to use Comuniva v4
    """
    with open(config_client_path, 'r') as f:
        lines = f.readlines()
    
    updated_lines = []
    for line in lines:
        if '"https://linkedsoftwaredependencies.org/bundles/npm/@comunica/config-query-sparql/^2.0.0/components/context.jsonld"' in line:
            updated_lines.append('\t\t"https://linkedsoftwaredependencies.org/bundles/npm/@comunica/config-query-sparql/^4.0.0/components/context.jsonld"\n') # fix this line...
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(config_client_path, 'w') as f:
        f.writelines(updated_lines)


def changeDockerFile(current_docker_file):
    """
    changes Dockerfile-client for expt
    """
    with open(current_docker_file, 'r') as f:
        lines = f.readlines()

    # Create a new list of lines with the target lines replaced.
    updated_lines = []
    for line in lines:
        # changes Comunica version used
        if "FROM" in line:
            updated_lines.append("FROM comunica/query-sparql@sha256:ee52195387cc7879be8aa4844ed4658dc5b701ea8adaf2487954f918fb1de338\n")
        # changes docker command to include "--contextOverride"
        elif "CMD" in line:
            updated_lines.append(
                'CMD [ "/bin/sh", "-c", "node --max-old-space-size=$MAX_MEMORY ./bin/http.js -c /tmp/context.json -p 3000 -t $QUERY_TIMEOUT -l $LOG_LEVEL --contextOverride -i" ]\n')
        # all other lines
        else:
            updated_lines.append(line)

    # Write the updated lines to the output file.
    with open(current_docker_file, 'w') as f:
        f.writelines(updated_lines)

def main():
    if len(sys.argv) < 2:
        print("Usage: python3 config_permutations.py <configs_dir> (please use tailing slash)")
        sys.exit(1)

    # TODO: use argparse for this because it will be much prettier
    config_dir = sys.argv[1]
    dir_list = config_dir.split('/')
    expt_dir = dir_list[0]+'/'

    # for default-service experiments
    if "default" in config_dir:
        changeDockerFile(f"{expt_dir}input/dockerfiles/Dockerfile-client")
        changeExptJsonService(f"{expt_dir}jbr-experiment.json")
        changeClientConfigService(f"{expt_dir}input/config-client.json")
    
    # for no-service experiments
    else:
        input_dir = '/'.join(dir_list[:2]) + '/'
        docker_dir = f'{input_dir}dockerfiles/'

        # directories for the different config files
        optimize_dir = f"{config_dir}optimize-query-operation/"
        void_dir = f"{config_dir}rdf-metadata-extract/"
        join_dir = f"{config_dir}rdf-join/"
        rate_dir = f"{config_dir}http/"


        # all config paths
        allPaths = Config_Direstories(
            optimize_dir=listFilePaths(optimize_dir),
            void_dir=listFilePaths(void_dir),
            join_dir=listFilePaths(join_dir),
            rate_dir=listFilePaths(rate_dir)
        )
        
        # all config files
        algoFiles = listConfigFiles(allPaths.join_files)
        optionFiles = listConfigFiles(allPaths.optimize_files)
        optionFiles.extend(listConfigFiles(allPaths.void_files))
        rateFiles = listConfigFiles(allPaths.rate_files)

    
        # all config names
        count = 0
        algoNames = listConfigNames(algoFiles)
        optionNames = listConfigNames(optionFiles)
        rateNames = listConfigNames(rateFiles)
        all_combos = determinePermutations(algoNames, optionNames, rateNames)
        # for c in all_combos:
        #     print(c.metadata_config, c.join_config, c.rate_config)
        #     count += 1
        # print(count)

        changeDockerFile(docker_dir+"Dockerfile-client")
        writeClientConfigs(input_dir, algoNames, optionNames, rateNames, algoFiles, optionFiles, rateFiles, all_combos)
        changeExptTemplate(join_dir, optimize_dir, void_dir,  rate_dir, algoFiles, optionFiles, rateFiles, f"{expt_dir}jbr-experiment.json.template")
        changeCombJson(f"{expt_dir}jbr-combinations.json", all_combos)



if __name__ == '__main__':
    main()