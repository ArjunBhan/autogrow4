#!/usr/bin/env python

import os
import sys
import shutil
import json
import argparse
import glob

def make_docker():
    """
    This will create the docker to run AutoGrow4.
    This is also where all of the files are copied into the image.

    If docker image can not be created it will raise an exception.
    """
    print("Creating new docker image for AutoGrow4")
    script_dir = str(os.path.dirname(os.path.realpath(__file__))) + os.sep
    output_and_log_dir = os.path.abspath("output_and_log_dir") + os.sep
    log_file = "{}log.txt".format(output_and_log_dir)
    printout = "\nAttempting to create the docker container. If 1st time running " + \
        "this script it may take a few minutes. Output details are piped to: " + \
        "{}\n".format(log_file)

    build_bash_script = script_dir + "build.bash"
    try:
        os.system("cd {}".format(script_dir))
        os.system("sudo bash {} > {}".format(build_bash_script, log_file))
    except:
        printout = "\nCan not create a docker file. Please make sure to run the " + \
            "script with sudo priveledges 'sudo bash build.bash'\n" + \
            "Please also make sure docker is installed on the system."
        print(printout)
        raise Exception(printout)

#
############################################
def check_for_required_inputs(json_vars):
    """
    Confirm all the required inputs were provided.

    Required Variables go here.

    Inputs:
    :param dict json_vars: The parameters. A dictionary of {parameter name: value}.
    """
    keys_from_input = list(json_vars.keys())

    list_of_required_inputs = [
        "filename_of_receptor",
        "center_x",
        "center_y",
        "center_z",
        "size_x",
        "size_y",
        "size_z",
        "root_output_folder",
        "source_compound_file",
    ]

    missing_variables = []
    for variable in list_of_required_inputs:
        if variable in keys_from_input:
            continue
        missing_variables.append(variable)

    if len(missing_variables) != 0:
        printout = "\nRequired variables are missing from the input. A description \
            of each of these can be found by running python ./RunAutogrow -h"
        printout = printout + "\nThe following required variables are missing: "
        for variable in missing_variables:
            printout = printout + "\n\t" + variable
        print("")
        print(printout)
        print("")
        raise NotImplementedError("\n" + printout + "\n")

    # Make sure the dimmensions are in floats. If in int convert to float.
    for x in ["center_x", "center_y", "center_z", "size_x", "size_y", "size_z"]:
        if type(json_vars[x]) in [float, int]:
            continue
        else:
            printout = "\n{} must be a float value.\n".format(x)
            print(printout)
            raise Exception(printout)


    #######################################
    # Check that all required files exist #
    #######################################

    # convert paths to abspath, in case necessary
    json_vars["filename_of_receptor"] = os.path.abspath(
        json_vars["filename_of_receptor"]
    )
    json_vars["root_output_folder"] = os.path.abspath(
        json_vars["root_output_folder"]
    )
    json_vars["source_compound_file"] = os.path.abspath(
        json_vars["source_compound_file"]
    )
    # Check filename_of_receptor exists
    if os.path.isfile(json_vars["filename_of_receptor"]) is False:
        raise NotImplementedError(
            "Receptor file can not be found. File must be a .PDB file."
        )
    if ".pdb" not in json_vars["filename_of_receptor"]:
        raise NotImplementedError("filename_of_receptor must be a .PDB file.")

    # Check root_output_folder exists
    if os.path.exists(json_vars["root_output_folder"]) is False:
        # If the output directory doesn't exist, then make ithe output
        # directory doesn't exist, then make it
        try:
            os.makedirs(json_vars["root_output_folder"])
            os.system("chmod +x {}".format(json_vars["root_output_folder"]))
        except:
            raise NotImplementedError(
                "root_output_folder could not be found and could not be created. \
                Please manual create desired directory or check input parameters"
            )

        if os.path.exists(json_vars["root_output_folder"]) is False:
            raise NotImplementedError(
                "root_output_folder could not be found and could not be created. \
                Please manual create desired directory or check input parameters"
            )

    if os.path.isdir(json_vars["root_output_folder"]) is False:
        raise NotImplementedError(
            "root_output_folder is not a directory. \
            Check your input parameters."
        )

    # Check source_compound_file exists
    if os.path.isfile(json_vars["source_compound_file"]) is False:
        raise NotImplementedError(
            "source_compound_file must be a tab delineated .smi file. \
            source_compound_file can not be found: \
            {}.".format(json_vars["source_compound_file"])
        )
    if ".smi" not in json_vars["source_compound_file"]:
        raise NotImplementedError(
            "source_compound_file must be a \
            tab delineated .smi file."
        )
#
def find_previous_runs(folder_name_path):
    """
    This will check if there are any previous runs in the output directory.
        - If there are it will return the interger of the number label of the last Run folder path.
            - ie if there are folders Run_0, Run_1, Run_2 the function will return int(2)
        - If there are no previous Run folders it returns None.

    Inputs:
    :param str folder_name_path: is the path of the root output folder. We will
        make a directory within this folder to store our output files

    Returns:
    :returns: int last_run_number: the int of the last run number or None if no previous runs.
    """

    path_exists = True
    i = 0
    while path_exists is True:
        folder_path = "{}{}{}".format(folder_name_path, i, os.sep)
        if os.path.exists(folder_path):
            i = i + 1
        else:
            path_exists = False

    if i == 0:
        # There are no previous runs in this directory
        last_run_number = None
        return None

    # A previous run exists. The number of the last run.
    last_run_number = i - 1
    return last_run_number
# 
def set_run_directory(root_folder_path, start_a_new_run):
    """
    Determine and make the folder for the run directory.
        If start_a_new_run is True    Start a frest new run.
            -If no previous runs exist in the root_folder_path then make a new
                folder named root_folder_path + "Run_0"
            -If there are previous runs in the root_folder_path then make a
                new folder incremental increasing the name by 1 from the last
                run in the same output directory.
        If start_a_new_run is False    Find the last run folder and return that path
            -If no previous runs exist in the root_folder_path then make a new
            folder named root_folder_path + "Run_0"

    Inputs:
    :param str root_folder_path: is the path of the root output folder. We will
        make a directory within this folder to store our output files
    :param bol start_a_new_run: True or False to determine if we continue from
        the last run or start a new run
        - This is set as a vars["start_a_new_run"]
        - The default is vars["start_a_new_run"] = True
    Returns:
    :returns: str folder_path: the string of the newly created directory for
        puting output folders
    """

    folder_name_path = root_folder_path + "Run_"
    print(folder_name_path)

    last_run_number = find_previous_runs(folder_name_path)

    if last_run_number is None:
        # There are no previous simulation runs in this directory
        print("There are no previous runs in this directory.")
        print("Starting a new run named Run_0.")

        # make a folder for the new generation
        run_number = 0
        folder_path = "{}{}{}".format(folder_name_path, run_number, os.sep)
        os.makedirs(folder_path)

    else:
        if start_a_new_run is False:
            # Continue from the last simulation run
            run_number = last_run_number
            folder_path = "{}{}{}".format(folder_name_path, last_run_number, os.sep)
        else:  # start_a_new_run is True
            # Start a new fresh simulation
            # Make a directory for the new run by increasing run number by +1
            # from last_run_number
            run_number = last_run_number + 1
            folder_path = "{}{}{}".format(folder_name_path, run_number, os.sep)
            os.mkdir(folder_path)
            os.system("chmod +x {}".format(folder_path))

    print("The Run number is: ", run_number)
    print("The Run folder path is: ", folder_path)
    print("")
    return folder_path
# 
def get_output_folder(json_vars):
    """
    Find the folder for where to place output runs on host system.

    Inputs:
    :param dict json_vars: The parameters. A dictionary of {parameter name: value}.
    Returns:
    :returns: str folder_path: the string of the newly created directory for
        puting output folders
    """
    if "start_a_new_run" in json_vars.keys():
        start_a_new_run = json_vars["start_a_new_run"]
    else:
        start_a_new_run = False

    root_output_folder = os.path.abspath(json_vars["root_output_folder"]) + os.sep
    folder_path = set_run_directory(root_output_folder, start_a_new_run) 

    # os.system("sudo docker cp {}:Outputfolder.zip {}".format(container_id, folder_path))
    return folder_path
    

def move_files_to_temp_dir(json_vars):
    """
    This will move all files needed to a temp_user_files directory and will created a modified
    json_vars dict called docker_json_vars which will be used for pathing within
    the docker.

    Inputs:
    :param dict json_vars: The parameters. A dictionary of {parameter name: value}.

    Returns:
    :returns: dict docker_json_vars: A modified version of the json dictionary
        that is to be used within the docker container.
    """
    docker_json_vars = {}
    # make or remove and make the temp_user_files dir
    temp_dir_path = os.path.abspath("temp_user_files") + os.sep
    if os.path.exists(temp_dir_path):
        shutil.rmtree(temp_dir_path)
    os.mkdir(temp_dir_path)
    os.system("chmod +x {}".format(temp_dir_path))

    # make or remove and make an output_and_log_dir
    output_and_log_dir = os.path.abspath("output_and_log_dir") + os.sep
    if os.path.exists(output_and_log_dir):
        shutil.rmtree(output_and_log_dir)
    os.mkdir(output_and_log_dir)
    os.system("chmod +x {}".format(output_and_log_dir))

    print("copying files into temp directory: temp_user_files")
    # get files from json_vars
    for var_name in json_vars.keys():
        var_item = json_vars[var_name]
        if type(var_item) not in [str, unicode]:
            continue
        if type(var_item) == unicode:
            var_item = str(var_item)
        # This could be a different variable that is not a path
        # ie) dock_choice: QuickVina2 would be a string that is not a path
        if os.path.exists(var_item) is False:
            continue
        if "mgl" in var_name.lower():
            print("MGLTools from within the docker will be used")
            continue
        if "babel" in var_name.lower():
            print("obabel from within the docker will be used")
            continue
        if var_name == "root_output_folder":
            continue
        basename = os.path.basename(var_item)
        temp_path = temp_dir_path + basename
        if os.path.isdir(var_item):
            shutil.copytree(var_item, temp_path)
            docker_json_vars[var_name] = "/UserFiles/" + basename + os.sep
            continue

        if os.path.isfile(var_item):
            shutil.copyfile(var_item, temp_path)
            docker_json_vars[var_name] = "/UserFiles/" + basename

    for var_name in json_vars.keys():
        if var_name not in docker_json_vars.keys():
            docker_json_vars[var_name] = json_vars[var_name]

    # Add docker babel and MGL paths
    docker_json_vars["mgltools_directory"] = "/mgltools_x86_64Linux2_1.5.6"
    docker_json_vars["obabel_path"] = "/usr/bin/obabel"

    # Set output folder
    docker_json_vars["root_output_folder"] = "/Outputfolder/"

    with open(temp_dir_path + "docker_json_vars.json", "w") as file_item:
        json.dump(docker_json_vars, file_item, indent=4)

    return docker_json_vars
#
def handle_json_info(vars):
    """
    This will open the json file.
        1) check that JSON file has basic info
            -receptor, size/center...
        2) copy files to a temp directory
            -receptor, .smi files ...
        3) make a JSON file with modified information for within docker
    Inputs:
    :param dict argv: Dictionary of User specified variables

    Returns:
    :param dict argv: Dictionary of User specified variables
    :param dict json_vars: Dictionary of User specified variables
    :returns: dict docker_json_vars: A modified version of the json dictionary
        that is to be used within the docker container.
    """
    print("Handling files")

    json_file = vars["json_file"]
    if os.path.exists(json_file) is False:
        printout = "\njson_file is required. Can not find json_file: {}.\n".format(json_file)
        print(printout)
        raise Exception(printout)
    json_vars = json.load(open(json_file))
    check_for_required_inputs(json_vars)
    docker_json_vars = move_files_to_temp_dir(json_vars)

    return json_vars, docker_json_vars
# 
def run_autogrow_docker_main(vars):
    """
    This function runs the processing to:
        1) check that JSON file has basic info
            -receptor, size/center...
        2) copy files to a temp directory
            -receptor, .smi files ...
        3) make a JSON file with modified information for within docker
        4) run build.bash
            which transfers the necessary files to docker container
        5) execute RunAutogrow.py from within the docker containiner
        6) export the files back to the final end dir

    Inputs:
    :param dict argv: Dictionary of User specified variables
    """
    printout = "\n\nThis script builds a docker for AutoGrow4 and runs AutoGrow4 " + \
        "within the docker. The setup may take a few minutes the first time being run " + \
        "and AutoGrow may take a long time depending on the settings.\n\n"
    print(printout)
    # Run parts 1-3
    # 1) check that JSON file has basic info
    #     -receptor, size/center...
    # 2) copy files to a temp directory
    #     -receptor, .smi files ...
    # 3) make a JSON file with modified information for within docker
    json_vars, docker_json_vars = handle_json_info(vars)

    # HANDLE RESTARTING A RUN!!!!!!!???? @@@@JAKE

    # Run part 4) run build.bash
    make_docker()

    # get output folder
    outfolder_path = get_output_folder(json_vars)

    # Run part 5) run AutoGrow in the container
    # docker cp foo.txt mycontainer:/foo.txt
    print("\nRunning AutoGrow4 in Docker")
    tmp_path = os.path.abspath("temp_user_files")
    script_dir = str(os.path.dirname(os.path.realpath(__file__))) + os.sep
    execute_outside_docker = script_dir + "execute_autogrow_from_outside_docker.sh"
    command = "sudo bash {} {} {}".format(execute_outside_docker, tmp_path, outfolder_path)
    os.system(command)
    print("AutoGrow Results placed in: {}".format(outfolder_path))
# 

PARSER = argparse.ArgumentParser()

# Allows the run commands to be submitted via a .json file.
PARSER.add_argument(
    "--json_file",
    "-j",
    metavar="param.json_file",
    required=True,
    help="Name of a json file containing all parameters. \
    Overrides other arguments. This takes all the parameters described in \
    RunAutogrow.py. MGLTools and openbabel paths can be ignored as they are \
    already installed in the docker image.",
)

ARGS_DICT = vars(PARSER.parse_args())
run_autogrow_docker_main(ARGS_DICT)

# sudo docker run autogrow -it \
#     -v /home/jacob/Documents/autogrow4/Docker/.temp_user_files:/autogrow_work_dir/ \
#     -filename_of_receptor ../tutorial/PARP/4r6e_removed_smallmol_aligned_Hs.pdb \
#     -output_dir /autogrow_work_dir/autogrow_output/