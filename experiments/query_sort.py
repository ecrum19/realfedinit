import os
import json
import sys

def main():
    if len(sys.argv) < 3:
        print("Usage: python3 query-sort.py <input_json_file> <output_path> [service / noservice]")
        sys.exit(1)

    input_file = sys.argv[1]
    output_directory = sys.argv[2]
    service_type = sys.argv[3]
    # checks input file validity
    try:
        with open(input_file, 'r', encoding='utf-8') as f:
            json_data = json.load(f)
    except Exception as e:
        print(f"Error reading {input_file}: {e}")
        sys.exit(1)

    working_output_dir = os.path.join(output_directory)
    # checks if specified output path is valid
    if not os.path.isdir(working_output_dir):
        print(f"Error: {output_directory} does not exist.")
        sys.exit(1)

    # Make sure the JSON has a top-level "data" key.
    if "data" not in json_data:
        print("JSON file does not contain a top-level 'data' key.")
        sys.exit(1)

    if service_type not in ["service", "noservice"]:
        print("Sort option not supported, please use 'service or 'noservice' as third argument")
        sys.exit(1)

    if service_type == "service":
        withService(json_data, output_directory)
    
    if service_type == "noservice":
        withoutService(json_data, output_directory)
    

def withService(data, out_directory):
    output_dir_s = os.path.join(out_directory, "input", "queries")
    os.makedirs(output_dir_s, exist_ok=True)

    excluded = [
        "13", # server-side error
        "14", # server-side error
        "20", # server-side error
        "46", # server-side error
        "99_uniprot_identifiers_org_translation",   # server-side error
        "90_uniprot_affected_by_metabolic_diseases_using_MeSH", # server-side error
    ]
    total = 0
    past_names = []
    for item_key, item_value in data["data"].items():
        s_query_text = item_value.get("query").split('\n')
        fix_prefix_s_query_text = ''
        for i in s_query_text:
            if i.strip() != '':
                fix_prefix_s_query_text += f"\n{i}"
        
        s_query_source = "sparql@" + item_value.get("target")

        if s_query_text is None:
            print(f"Skipping item '{item_key}': no 'query' property found.")
            continue
        
        # Generate a safe filename.
        # Here we use os.path.basename to extract the last part of the URL.
        base_name = os.path.basename(item_key)

        # In case the key does not have a proper basename, replace unsafe characters.
        if not base_name:
            base_name = item_key.replace('https://', '00').replace('/', '_')
        
        # Case where file name is repeated
        if base_name in past_names:
            base_name += "a"
        past_names.append(base_name)

        # Append the .rq extension.
        s_output_filename = f"{base_name}.sparql"
        s_full_output_path = os.path.join(output_dir_s, s_output_filename)

        if base_name not in excluded:
            total += 1
            # for with SERVICE descriptions
            try:
                with open(s_full_output_path, 'w', encoding='utf-8') as out_file:
                    out_file.write("# Datasources: %s%s" % (s_query_source, fix_prefix_s_query_text))
                # print(f"Created file: {output_filename}")
            except Exception as e:
                print(f"Error writing {s_output_filename}: {e}")
    print("Total with service queries:", total)



def withoutService(data, out_directory):
    output_dir_ns = os.path.join(out_directory, "input", "queries")
    try:
        os.makedirs(output_dir_ns, exist_ok=False)
    except Exception as e:
        print(f"Directory {output_dir_ns} already exists")
    
    excluded = [
        "14", # server-side error
        "20", # server-side error
        "46", # server-side error
        "99_uniprot_identifiers_org_translation",   # server-side error
        "90_uniprot_affected_by_metabolic_diseases_using_MeSH", # server-side error
        "70_enzymes_interacting_with_molecules_similar_to_dopamine", # IDSM
        "71_enzymes_interacting_with_molecules_similar_to_dopamine_with_variants_related_to_disease", # IDSM
        "52",  # IDSM
        "54",  # IDSM
        "60",  # IDSM
        "002",    # IDSM
        "18a", # IDSM
    ]

    # Iterate over each item in the "data" dictionary.
    total = 0
    past_names = []
    for item_key, item_value in data["data"].items():
        s_query_text = item_value.get("query")
        ns_query_source = "sparql@" + item_value.get("target")

        if s_query_text is None:
            print(f"Skipping item '{item_key}': no 'query' property found.")
            continue

        
        # generate no SERVICE description query
        split_query = s_query_text.split("\n")
        ns_query_text = ""
        brace_count = 0
        curr_service = False
        for line in split_query:
            # remove SERVICE description line
            if "SERVICE" in line:
                tab_count = line.count("\t")
                tabs = ""
                for i in range(tab_count+1):
                    tabs += "\t"
                line_s = line.split("<")
                for s in line_s:
                    if ">" in s:
                        source = s.split(">")[0]
                        if "{" in source:
                            source = source[:-1].strip()
                        source = "sparql@" + source
                ns_query_source += " %s" % source
                brace_count += 1
                curr_service = True
                ns_query_text += (tabs + "{\n")
            
            # case where both brackets are in same line
            elif "{" in line and "}" in line and curr_service:
                ns_query_text += "%s\n" % line

            # count bracket offset
            elif "{" in line and curr_service:
                brace_count += 1
                ns_query_text += "%s\n" % line

            # find closing bracket for SERVICE clause
            # elif "}" in line and curr_service:
            #     brace_count -= 1
            #     if brace_count > 0:
            #         ns_query_text += "%s\n" % line
            #     else:
            #         curr_service = False
            #         brace_count = 0
            
            # fix double bracket syntax
            elif "}}" in line:
                tab_count = line.count("\t")
                tabs = ""
                for i in range(tab_count):
                    tabs += "\t"
                rm_one_bracket = line.replace("}}", "}")
                ns_query_text += tabs + "}\n" + tabs[:-1] + "%s\n" % rm_one_bracket

            # for normal query lines
            else:
                if line.strip() != '':
                    ns_query_text += "%s\n" % line


        # Generate a safe filename.
        # Here we use os.path.basename to extract the last part of the URL.
        base_name = os.path.basename(item_key)

        # In case the key does not have a proper basename, replace unsafe characters.
        if not base_name:
            base_name = item_key.replace('https://', '00').replace('/', '_')
        
        # Case where file name is repeated
        if base_name in past_names:
            base_name += "a"
        past_names.append(base_name)

        # Append the .rq extension.
        ns_output_filename = f"{base_name}_ns.sparql"
        ns_full_output_path = os.path.join(output_dir_ns, ns_output_filename)

        print(base_name not in excluded, base_name)
        if str(base_name) not in excluded:
            total += 1
            # for without SERVICE descriptions
            try:
                with open(ns_full_output_path, 'w', encoding='utf-8') as out_file:
                    out_file.write("# Datasources: %s\n%s" % (ns_query_source, ns_query_text.rstrip('\n')))
                # print(f"Created file: {output_filename}")
            except Exception as e:
                print(f"Error writing {ns_output_filename}: {e}")
    print("Total no-service queries:", total)


if __name__ == "__main__":
    main()
