import os
import json
import sys
import itertools

def listFilePaths(directory):
    """Return a sorted list of file paths in the given directory."""
    return sorted(
        os.path.join(directory, f) 
        for f in os.listdir(directory) 
        if os.path.isfile(os.path.join(directory, f))
    )

def get_base_url(file_path):
    last_slash = file_path.rfind('/')
    return file_path[last_slash+1:]

def get_base_name(file_with_ext):
    dot = file_with_ext.rfind('.')
    return file_with_ext[:dot]

class Config:
    def __init__(self, optimize_config, join_config):
        self.optimize_config = optimize_config
        self.join_config = join_config

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

def new_config(current_config_path, new_option_line, new_algo_line, output_file):
    """
    Replaces the line that contains 
    "ccqs:config/optimize-query-operation/actors.json",
    with the new_line provided.
    
    Parameters:
      default_config_path (str): Path to the default config JSON file.
      new_line (str): The new line to replace the target line.
      output_file (str): File path to write the modified content.
    """
    search_option_string = '"ccqs:config/optimize-query-operation/actors.json",'
    search_algo_string = '"ccqs:config/rdf-join/actors.json",'
    
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
        # all other lines
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(output_file, 'w') as f:
        f.writelines(updated_lines)


def determinePermutations(algorithms, options):
    """
    Returns all config file permutations as a list of Objects
    """
    combinations = []
    for a in algorithms:
        for o in options:
            combinations.append(Config(
                optimize_config=o,
                join_config=a
            ))
    return combinations


def writeClientConfigs(algorithm_names, option_names, algoithm_files, option_files, config_combos):
    """
    creates new client config files with the changes based on permutations
    """
    default_config = "../config/default.json"
    output_path = "no_service_combos/input/client-config/"
    for combo in config_combos:
        # name of the current configs
        wanted_option = combo.optimize_config
        wanted_algo = combo.join_config

        # indexes of the current configs
        option_index = option_names.index(wanted_option)
        algo_index = algorithm_names.index(wanted_algo)

        # the lines that will be replaced in the config file
        wanted_option_config = f'\t\t"{option_files[option_index]}",'
        wanted_algo_config = f'\t\t"{algoithm_files[algo_index]}",'

        # file name change
        outfile = f"{output_path}{wanted_option}_{wanted_algo}.json"
        new_config(default_config, wanted_option_config, wanted_algo_config, outfile)


def changeExptTemplate(current_template_file, combos_added):
    """
    creates new client config files with the new config files in the "additionalBinds" input for permutations
    """
    current_path = "no_service_combos/input/config/"
    with open(current_template_file, 'r') as f:
        lines = f.readlines()

    target_line = '"additionalBinds": [],'
    # Create a new list of lines with the target lines replaced.
    updated_lines = []
    for line in lines:
        
        # find targeted line config
        if target_line in line:
            updated_lines.append('\t\t"additionalBinds": [\n')
            # add combos to the list
            for comb in combos_added:
                file_name = f"{comb.optimize_config}_{comb.join_config}.json"
                if combos_added.index(comb) < len(combos_added)-1:
                    updated_lines.append(f'\t\t\t"{current_path}{file_name}:/tmp/{file_name}",\n')
                else:
                    updated_lines.append(f'\t\t\t"{current_path}{file_name}:/tmp/{file_name}"\n')

            updated_lines.append("\t\t],\n")
        # all other lines
        else:
            updated_lines.append(line)
    
    # Write the updated lines to the output file.
    with open(current_template_file, 'w') as f:
        f.writelines(updated_lines)

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 config_permutations.py <aglorithm_dir> <options_dir>")
        sys.exit(1)

    # directories to algorithm and options directories
    algos_dir = sys.argv[1]
    options_dir = sys.argv[2]

    # all config paths
    allAlgoPaths = listFilePaths(algos_dir)
    allOptionPaths = listFilePaths(options_dir)

    # all config files
    algoFiles = listConfigFiles(allAlgoPaths)
    optionFiles = listConfigFiles(allOptionPaths)

    # all config names
    algoNames = listConfigNames(algoFiles)
    optionNames = listConfigNames(optionFiles)

    all_combos = determinePermutations(algoNames, optionNames)

    writeClientConfigs(algoNames, optionNames, algoFiles, optionFiles, all_combos)
    changeExptTemplate("no_service_combos/jbr-experiment.json.template", all_combos)



if __name__ == '__main__':
    main()