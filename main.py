##### EDIT THINGS BELOW THIS LINE TO YOUR CONTENT
# percent of resources to dedicate to preferred projects
preferred_projects_percent=80  # example: 80
# Your "preferred projects list". Work will be split among these projects according to given percent (10, 20, 80).
# For example, if you want 80% of your "preferred project crunching time" to go to a particular project, put in 80. These values must add up to 100.
# If you just want to crunch the most profitable projects all the time, uncomment the next line (and comment out the subsequent one) to have no preferred projects:
# preferred_projects={}
preferred_projects={
    'https://www.sidock.si/sidock/':80,
    'https://www.worldcommunitygrid.org/boinc/':20
}
# projects on the ignored_projects list will always have their weight set to zero.
ignored_projects=['https://example.com/project1','http://exampleproject.com/project2']
boinc_data_dir=None # Example: '/var/lib/boinc-client' or 'C:\\ProgramData\\BOINC\\'. Only needed if in a non-standard location, otherwise None.
gridcoin_data_dir='/home/user/sharedfolder/gridcointest/' # Example: '/home/user/.GridcoinResearch' or 'C:\\Users\\username\\AppData\Roaming\GridcoinResearch\\'. Only needed if in a non-standard location, otherwise None
##### DON'T EDIT THINGS BELOW THIS LINE

import json
import pprint
import re
import platform
from pathlib import Path
import datetime
import xmltodict
import requests
import os
from requests.auth import HTTPBasicAuth
from typing import List,Union,Dict,Tuple

class GridcoinClientConnection():
    def __init__(self, config_file:str=None, config_type:str=None, ip_address:str='127.0.0.1', rpc_port:str='9876', rpc_user:str=None, rpc_password:str=None,):
        self.configfile=config_file #absolute path to the client config file
        self.configtype=config_type #valid options are 'CONF' and 'JSON'
        self.ipaddress=ip_address
        self.rpc_port=rpc_port
        self.rpcuser=rpc_user
        self.rpcpassword=rpc_password
    def run_command(self,command:str,arguments:List[Union[str,bool]]=None)->dict:
        if not arguments:
            arguments=[]
        credentials=None
        url='http://' + self.ipaddress +':' + self.rpc_port + '/'
        headers = {'content-type': 'application/json'}
        payload = {
            "method": command,
            "params": arguments,
            "jsonrpc": "2.0",
            "id": 0,
        }
        jsonpayload=json.dumps(payload)
        if self.rpcuser or self.rpcpassword:
            credentials=HTTPBasicAuth(self.rpcuser, self.rpcpassword)
        response = requests.post(
            url, data=jsonpayload, headers=headers, auth=credentials)
        return response.json()
    def get_approved_project_urls(self)->List[str]:
        """

        :return: A list of UPPERCASED project URLs using gridcoin command listprojects
        """
        return_list=[]
        all_projects=self.run_command('listprojects')
        for projectname,project in all_projects['result'].items():
            return_list.append(project['base_url'].upper())
        return return_list
    def project_name_to_url(self,searchname:str)->Union[str,None]:
        all_projects = self.run_command('listprojects')
        for project_name, project in all_projects['result'].items():
            if project_name.upper()==searchname.upper():
                return project['base_url'].upper()
        return None

class BoincClientConnection():
    def __init__(self, config_dir:str=None, ip_address:str='127.0.0.1', port:str='9876', rpc_user:str=None, rpc_password:str=None):
        if config_dir==None:
            self.config_dir='/var/lib/boinc-client'
        else:
            self.config_dir=config_dir #absolute path to the client config dir
        self.ip_address=ip_address
        self.port=port
        self.rpc_user=rpc_user
        self.rpc_password=rpc_password
    def test_connection(self):
        pass
    def get_project_list(self)->List[str]:
        """

        :return: UPPERCASED list of project URLs
        """
        project_list_file=os.path.join(self.config_dir,'all_projects_list.xml')
        return_list=[]
        with open(project_list_file, mode='r', encoding='ASCII', errors='ignore') as f:
            parsed = xmltodict.parse(f.read())
            for project in parsed['projects']['project']:
                return_list.append(project['url'].upper())
        return return_list

def get_config_parameters(gridcoin_dir:str)->Dict[str, str]:
    """

    :param gridcoin_dir: Absolute path to a gridcoin config directory
    :return: All config parameters found, preferring those in the json file to the conf. Note that sidestakes become a list as there may be multiple
    """
    return_dict=dict()
    if 'gridcoinsettings.json' in os.listdir(gridcoin_dir):
        with open(os.path.join(gridcoin_dir,'gridcoinsettings.json')) as json_file:
            config_dict=json.load(json_file)
            if 'rpcuser' in config_dict:
                return_dict['rpc_user']=config_dict['rpcuser']
            if 'rpcpass' in config_dict:
                return_dict['rpc_pass']=config_dict['rpcpass']
            if 'rpcport' in config_dict:
                return_dict['rpc_port']=config_dict['rpcport']
    if 'gridcoinresearch.conf' in os.listdir(gridcoin_dir):
        with open(os.path.join(gridcoin_dir,'gridcoinresearch.conf')) as f:
            for line in f:
                if line.startswith('#'):
                    continue
                try:
                    key=line.split('=')[0]
                    value=line.split('=')[1].replace('\n','')
                    if '#' in value:
                        value=value.split('#')[0]
                    value=value.strip()
                except Exception as e:
                    print('Warning: Error parsing line from config file, ignoring: '+line)
                    print('Pase error was: '+str(e))
                    continue
                if key=='addnode':
                    continue
                if key=='sidestake':
                    if 'sidestake' not in return_dict:
                        return_dict['sidestake']=[]
                    return_dict['sidestake'].append(value)
                    continue
                if key in return_dict:
                    print('Warning: multiple values found for '+key+' in gridcoin config file at '+os.path.join(gridcoin_dir,'gridcoinresearch.conf')+' using the first one we found')
                    continue
                return_dict[key]=value
    return return_dict

def check_sidestake(config_params:Dict[str,Union[str,List[str]]],address:str,minval:float)->bool:
    """
    Checks if a given address is being sidestaked to or not
    :param config_params: config_params from get_config_parameters
    :param address: address to check
    :param minval: minimum value to pass check
    :return: True or False
    """
    if 'enablesidestaking' not in config_params:
        return False
    if 'sidestake' not in config_params:
        return False
    if config_params['enablesidestaking']!='1':
        return False
    for sidestake in config_params['sidestake']:
        found_address=sidestake.split(',')[0]
        found_value=float(sidestake.split(',')[1])
        if found_address==address:
            if found_value>=minval:
                return True
    return False

def projecturlfromstatsfile(statsfilename: str,all_project_urls:List[str],approved_project_urls:List[str]) -> str:
    statsfilename = statsfilename.replace('job_log_', '')
    statsfilename = statsfilename.split('_')[0]
    statsfilename = statsfilename.replace('.txt', '')
    for knownurl in approved_project_urls:
        if statsfilename.upper() in knownurl:
            return knownurl
    for knownurl in all_project_urls:
        if statsfilename.upper() in knownurl:
            return knownurl
    print('WARNING: Found stats file ' + statsfilename+' but unable to find URL for it, perhaps it is not the BOINC client\'s list of projects?')
    return statsfilename
def project_url_from_credit_history_file(filename: str, approved_project_urls: List[str],
                                         all_project_urls: List[str]) -> str:
    filename = filename.replace('statistics_', '')
    filename = filename.replace('.xml', '')
    filename = filename.split('_')[0]
    # print('GUESSING SHORT URL IS '+filename)
    for knownurl in approved_project_urls:
        if filename.upper() in knownurl:
            return knownurl
    for knownurl in all_project_urls:
        if filename.upper() in knownurl:
            return knownurl
    print('WARNING: Found credit history file ' + filename+' but unable to find URL for it, perhaps it is not the BOINC client\'s list of projects?')
    return filename


def stat_file_to_list(stat_file_abs_path: str) -> List[Dict[str, str]]:
    """
        Turns a BOINC job log into list of dicts we can use, each dict is a task. Dicts have keys below:
        STARTTIME,ESTTIME,CPUTIME,ESTIMATEDFLOPS,TASKNAME,WALLTIME,EXITCODE
        Note that ESTIMATEDFLOPS comes from the project and EXITCODE will always be zero.
        All values and keys in dicts are strings.

        BOINC's job log format is:

[ue]	Estimated runtime	BOINC Client estimate (seconds)
[ct]	CPU time		Measured CPU runtime at completion (seconds)
[fe]	Estimated FLOPs count	From project (integer)
[nm]	Task name		From project
[et]	Elapsed time 		Wallclock runtime at completion (seconds)

    """
    stats_list = []
    try:
        with open(stat_file_abs_path, mode='r', errors='ignore') as f:
            for log_entry in f:
                # print('Found logentry '+str(logentry))
                match=None
                try:
                    match = re.search(r'(\d*)( ue )([\d\.]*)( ct )([\d\.]*)( fe )(\d*)( nm )(\S*)( et )([\d\.]*)( es )(\d)',log_entry)
                except Exception as e:
                    print(
                        'Error reading BOINC job log at ' + stat_file_abs_path + ' maybe it\'s corrupt? Line: ' + log_entry)
                    print('Error is: ' + str(e))
                if not match:
                    print('Encountered log entry in unknown format: ' + log_entry)
                    continue
                stats = dict()
                stats['STARTTIME'] = match.group(1)
                stats['ESTTIME'] = match.group(3)
                stats['CPUTIME'] = match.group(5)
                stats['ESTIMATEDFLOPS'] = match.group(7)
                stats['TASKNAME'] = match.group(9)
                stats['WALLTIME'] = match.group(11)
                stats['EXITCODE'] = match.group(13)
                stats_list.append(stats)
        return stats_list
    except Exception as e:
        print('Error reading BOINC job log at '+stat_file_abs_path+' maybe it\'s corrupt? '+str(e))
        return []


def credit_history_file_to_list(credithistoryfileabspath: str) -> List[Dict[str, str]]:
    """
        Turns a BOINC credit history file into list of dicts we can use. Dicts have keys below:
        TIME,USERTOTALCREDIT,USERRAC,HOSTTOTALCREDIT,HOSTRAC
        Note that ESTIMATEDFLOPS comes from the project and EXITCODE will always be zero.
        All keys and values in dicts are strings.
    """
    statslist = []
    with open(credithistoryfileabspath, mode='r', encoding='ASCII', errors='ignore') as f:
        parsed = xmltodict.parse(f.read())
        for logentry in parsed.get('project_statistics', {}).get('daily_statistics', []):
            stats = {}
            if not isinstance(logentry, dict):
                continue
            stats['TIME'] = logentry['day']
            stats['USERTOTALCREDIT'] = logentry['user_total_credit']
            stats['USERRAC'] = logentry['user_expavg_credit']
            stats['HOSTTOTALCREDIT'] = logentry['host_total_credit']
            stats['HOSTRAC'] = logentry['host_expavg_credit']
            statslist.append(stats)
    return statslist


def config_files_to_stats(config_dir_abs_path: str) -> Dict[str, Dict[str, Union[int, float, Dict[str, Union[float, str]]]]]:
    """

    :param config_dir_abs_path: Absolute path to BOINC data directory
    :return: Dict of stats in format COMBINEDSTATSEXAMPLE in main.py
    """
    stats_files = []
    credit_history_files = []
    return_stats = {}
    for file in os.listdir(config_dir_abs_path):
        if 'job_log' in file:
            stats_files.append(os.path.join(config_dir_abs_path, file))
        if file.startswith('statistics_') and file.endswith('.xml'):
            credit_history_files.append(os.path.join(config_dir_abs_path, file))
    # print('Found stats_files: ' + str(stats_files))
    # print('Found historical credit info files at: ' + str(credit_history_files))
    # Process job logs
    for statsfile in stats_files:
        project_url = projecturlfromstatsfile(os.path.basename(statsfile),ALL_PROJECT_URLS,approved_project_urls=APPROVED_PROJECT_URLS)
        stat_list = stat_file_to_list(statsfile)
        # print('In statsfile for '+project_url)
        # Compute the first and last date in the stats file. Currently not used but does work
        startdate = str(datetime.datetime.fromtimestamp(float(stat_list[0]['STARTTIME'])).strftime('%m-%d-%Y'))
        lastdate = str(
            datetime.datetime.fromtimestamp(float(stat_list[len(stat_list) - 1]['STARTTIME'])).strftime('%m-%d-%Y'))
        # print('Start date is '+startdate)
        if project_url not in return_stats:
            return_stats[project_url] = {'CREDIT_HISTORY': {}, 'WU_HISTORY': {}, 'COMPILED_STATS': {}}
        wu_history = return_stats[project_url]['WU_HISTORY']
        for wu in stat_list:
            date = str(datetime.datetime.fromtimestamp(float(wu['STARTTIME'])).strftime('%m-%d-%Y'))
            if date not in wu_history:
                wu_history[date] = {'TOTALWUS': 0, 'total_wall_time': 0, 'total_cpu_time': 0}
            wu_history[date]['TOTALWUS'] += 1
            wu_history[date]['total_wall_time'] += float(wu['WALLTIME'])
            wu_history[date]['total_cpu_time'] += float(wu['CPUTIME'])
    # process credit logs
    for credit_history_file in credit_history_files:
        project_url = project_url_from_credit_history_file(os.path.basename(credit_history_file), APPROVED_PROJECT_URLS,
                                                          ALL_PROJECT_URLS)
        credithistorylist = credit_history_file_to_list(credit_history_file)
        # print('PRINTING CREDITHISTORYLIST')
        if len(credithistorylist) > 0:
            # print('In credit_history_file for ' + project_url)
            startdate = str(datetime.datetime.fromtimestamp(float(credithistorylist[0]['TIME'])).strftime('%m-%d-%Y'))
            lastdate = str(
                datetime.datetime.fromtimestamp(float(credithistorylist[len(credithistorylist) - 1]['TIME'])).strftime(
                    '%m-%d-%Y'))
            # print('Start date is ' + startdate)
        for index, entry in enumerate(credithistorylist):
            if index == len(credithistorylist) - 1: # Skip the last entry as it's already calculated at the previous entry
                continue
            next_entry = credithistorylist[index + 1]
            current_time = float(entry['TIME'])
            delta_credits = float(next_entry['HOSTTOTALCREDIT']) - float(entry['HOSTTOTALCREDIT'])
            # Add found info to combined average stats
            date = str(datetime.datetime.fromtimestamp(float(current_time)).strftime('%m-%d-%Y'))
            if project_url not in return_stats:
                return_stats[project_url] = {'CREDIT_HISTORY': {}, 'WU_HISTORY': {}, 'COMPILED_STATS': {}}
            if 'CREDIT_HISTORY' not in return_stats[project_url]:
                return_stats[project_url]['CREDIT_HISTORY'] = {}
            credit_history = return_stats[project_url]['CREDIT_HISTORY']
            if 'COMPILED STATS' not in return_stats[project_url]:
                return_stats[project_url]['COMPILED_STATS'] = {}
            if date not in credit_history:
                credit_history[date] = {}
            if 'CREDITAWARDED' not in credit_history[date]:
                credit_history[date]["CREDITAWARDED"] = 0
            credit_history[date]['CREDITAWARDED'] += delta_credits
    # find averages
    for project_url, parent_dict in return_stats.items():
        total_wus = 0
        total_credit = 0
        total_cpu_time = 0
        total_wall_time = 0
        for date, credit_history in parent_dict['CREDIT_HISTORY'].items():
            total_credit += credit_history['CREDITAWARDED']
        for date, wu_history in parent_dict['WU_HISTORY'].items():
            total_wus += wu_history['TOTALWUS']
            total_wall_time += wu_history['total_wall_time']
            total_cpu_time += wu_history['total_cpu_time']
        if total_wus == 0:
            avg_wall_time = 0
            avg_cpu_time = 0
            avg_credit_per_task = 0
            credits_per_hour = 0
        else:
            total_cpu_time=total_cpu_time/60/60 # convert to hours
            total_wall_time=total_wall_time/60/60 #convert to hours
            avg_wall_time = total_wall_time / total_wus
            avg_cpu_time = total_cpu_time / total_wus
            avg_credit_per_task = total_credit / total_wus
            credits_per_hour = (total_credit / (total_wall_time))
        parent_dict['COMPILED_STATS']['TOTALCREDIT'] = total_credit
        parent_dict['COMPILED_STATS']['AVGWALLTIME'] = avg_wall_time
        parent_dict['COMPILED_STATS']['AVGCPUTIME'] = avg_cpu_time
        parent_dict['COMPILED_STATS']['AVGCREDITPERTASK'] = avg_credit_per_task
        parent_dict['COMPILED_STATS']['TOTALTASKS'] = total_wus
        parent_dict['COMPILED_STATS']['TOTALWALLTIME'] = total_wall_time
        parent_dict['COMPILED_STATS']['TOTALCPUTIME'] = total_cpu_time
        parent_dict['COMPILED_STATS']['AVGCREDITPERHOUR'] = credits_per_hour
        #print('For project {} this host has crunched {} WUs for {} total credit with an average of {} credits per WU. {} hours were spent on these WUs for {} credit/hr'.format(project_url.lower(), total_wus, round(total_credit,2), round(avg_credit_per_task,2), round((total_wall_time),2),round(credits_per_hour,2)))
    return return_stats


def add_mag_to_combined_stats(combined_stats: dict, mag_ratios: Dict[str, float], approved_projects: List[str],preferred_projects:List[str] ) -> Tuple[Dict[str, Dict[str, Union[int, float, Dict[str, Union[float, str]]]]],List[str]]:
    """

    :param combined_stats: combined_stats from main.py
    :param mag_ratios: mag ratios returned from get_project_mag_ratios. A dict with project URL as key and mag ratio as value
    :return: combined_stats w/ mag ratios added to us, list of projects which are being crunched but not on approved projects list
    """
    unapproved_list=[]
    for project_url, project_stats in combined_stats.items():
        if project_url not in mag_ratios:
            if project_url not in approved_projects:
                if project_url not in preferred_projects:
                    unapproved_list.append(project_url.lower())
            project_stats['COMPILED_STATS']['AVGMAGPERHOUR'] = 0
            project_stats['COMPILED_STATS']['MAGPERCREDIT'] = 0
            continue
        avg_credit_per_hour = 0
        if 'AVGCREDITPERHOUR' in project_stats['COMPILED_STATS']:
            avg_credit_per_hour = project_stats['COMPILED_STATS']['AVGCREDITPERHOUR']
        project_stats['COMPILED_STATS']['AVGMAGPERHOUR'] = avg_credit_per_hour * mag_ratios[project_url]
        project_stats['COMPILED_STATS']['MAGPERCREDIT']=mag_ratios[project_url]
    return combined_stats,unapproved_list


def get_most_mag_efficient_projects(combinedstats: dict, ignored_projects: List[str], percentdiff: int = 10) -> List[
    str]:
    """
    Given combinedstats, return most mag efficient project(s). This is the #1 most efficient project and any other projects which are within percentdiff of that number.
    :param combinedstats: combinedstats dict
    :param percentdiff: Maximum percent diff
    :return: List of project URLs
    """

    def is_eligible(project_url: str, project_stats: dict):
        if project_url in ignored_projects:
            return False
        if int(project_stats['COMPILED_STATS']['TOTALTASKS']) > 10:
            return True
        return False

    return_list = []
    highest_project=None
    try:
        highest_project = next(iter(combinedstats))  # first project is the "highest project" until we test others against it
    except Exception as e:
        print('No projects found? Are you sure this computer has been crunching BOINC for more than a day? Quitting. '+str(e))
        quit()
    # find the highest project
    for project_url, project_stats in combinedstats.items():
        current_mag_per_hour=project_stats['COMPILED_STATS']['AVGMAGPERHOUR']
        highest_mag_per_hour=combinedstats[highest_project]['COMPILED_STATS']['AVGMAGPERHOUR']
        if  current_mag_per_hour > highest_mag_per_hour and is_eligible(project_url, project_stats):
            highest_project = project_url
    if combinedstats[highest_project]['COMPILED_STATS']['TOTALTASKS']>=10:
        print('\n\nHighest mag/hr project is {} w/ {}/hr of credit'.format(highest_project.lower(),
                                                                   combinedstats[highest_project]['COMPILED_STATS'][
                                                                       'AVGMAGPERHOUR']))
    return_list.append(highest_project)
    # then compare other projects to it to see if any are close
    highest_avg_mag = combinedstats[highest_project]['COMPILED_STATS']['AVGMAGPERHOUR']
    minimum_for_inclusion=highest_avg_mag - (highest_avg_mag * .10)
    for project_url, project_stats in combinedstats.items():
        current_avg_mag=project_stats['COMPILED_STATS']['AVGMAGPERHOUR']
        if project_url == highest_project:
            continue
        if minimum_for_inclusion <= current_avg_mag and is_eligible(project_url, project_stats):
            print('Also including this project because it\'s within 10% variance of highest mag/hr project: {}, mag/hr {}'.format(project_url.lower(), current_avg_mag))
            return_list.append(project_url)
        else:
            pass
            #print('{} + {} mag/hr'.format(project_url.lower(),project_stats['COMPILED_STATS']['AVGMAGPERHOUR']))
    #If there is no highest project, return empty list
    if len(return_list)==1:
        if combinedstats[highest_project]['COMPILED_STATS']['TOTALTASKS']<10:
            return_list.clear()
    return return_list

def sidestake_check(check_sidestake_results:bool,check_type:str,address:str)->None:
    if check_type=='FOUNDATION':
        message1='It appears that you have not enabled sidestaking to the Gridcoin foundation in your wallet. We believe it is only fair that people benefiting from the Gridcoin network contribute back to it\nSidestaking enables you to contribute a small % of your staking profits\nThis tool will not run unless you are donating at least 1% of your staking earnings to the Gridcoin foundation.\nWould you like to enable sidestaking?. \nPlease answer "Y" or "N" (without quotes)'
        message2='What percent would you like to donate to the foundation? Donations go towards software development, promotion, and growth of the coin. Enter a number like 5 for 5%. Please enter whole numbers only'
    elif check_type=='DEVELOPER':
        message1='Are you interested in sidestaking to the developers of this tool? This is optional. We ask you to consider what gain in efficiency this tool can bring you and to donate a small portion of that gain.\nPlease. I am trying to buy a pony.\nPlease answer "Y" or "N" (without quotes)'
        message2='What percent would you like to donate to the developers of this tool? Enter a number like 5 for 5%. Please enter whole numbers only'
    else:
        message1=''
        message2=''
    if not check_sidestake_results:
        print(message1)
        answer = input("")
        while answer not in ['Y', 'N']:
            print('Error: Y or N not entered. Try again please :)')
            answer = input("")
        if answer == 'N':
            if check_type=='FOUNDATION':
                print('Ok no problem, it is your choice after all! Program exiting now')
                quit()
            if check_type=='DEVELOPER':
                return
        print(message2)
        answer = input("")
        converted_value = None
        while not converted_value:
            try:
                converted_value = int(answer)
            except Exception as e:
                print("Hmm... that didn't seem to work, let's try again. Please enter a whole number")
                answer = input("")
        with open(os.path.join(gridcoin_data_dir, 'gridcoinresearch.conf'), "a") as myfile:
            if 'enablesidestaking=1' not in str(myfile):
                myfile.write("enablesidestaking=1\n")
            myfile.write('sidestake='+address+',' + str(converted_value) + '\n')
            #print('Modifying config file...')
def get_project_mag_ratios(grc_client: GridcoinClientConnection, lookback_period: int = 30) -> Dict[
    str, float]:
    """

    :param grc_client:
    :param lookback_period: number of superblocks to look back to determine average
    :return: Dictionary w/ key as project URL and value as project mag ratio (mag per unit of RAC)
    """
    projects = {}
    return_dict = {}
    mag_per_project = 0
    for i in range(1, lookback_period):
        superblock = grc_client.run_command('superblocks', [i, True])
        if i == 1:
            total_magnitude = superblock['result'][0]['total_magnitude']
            total_projects = superblock['result'][0]['total_projects']
            mag_per_project = total_magnitude / total_projects
        for project_name, project_stats in superblock['result'][0]['Contract Contents']['projects'].items():
            if project_name not in projects:
                projects[project_name] = []
            projects[project_name].append(project_stats['rac'])
    for project_name, project_racs in projects.items():
        average_rac = sum(project_racs) / len(project_racs)
        project_url = grc_client.project_name_to_url(project_name)
        return_dict[project_url] = mag_per_project / average_rac
    return return_dict
def print_table(table_dict:Dict[str,Dict[str,str]],sortby:str):
    headings=[]
    values={}
    replace_names={
        'TOTALWALLTIME':'TOTALWALLTIME(HRS)',
        'TOTALCPUTIME':'TOTALCPUTIME(HRS)'
    }
    for url,stats in table_dict.items():
        for key,value in stats.items():
            if key not in headings:
                headings.append(key)
            if key in replace_names:
                key=replace_names[key]
            if key not in values:
                values[key]=[]
            if value not in values[key]:
                values[key].append(value)
    longest_url= len(max(table_dict.keys(), key=len))
    table_width=longest_url+len(str(values.keys()))
    # print header
    ## print first line
    print('*'*table_width)
    ## print rest of header
    padding_len = longest_url
    padding_str = ' ' * padding_len
    print('*  '+padding_str+'| ',end='')
    for heading in headings:
        print(heading+' | ',end="")
    print('')
    # print contents
    sortedprojects= sorted(table_dict.keys(),key=lambda a: float(table_dict[a].get('AVGMAGPERHOUR')),reverse=True)
    for url in sortedprojects:
        stats=table_dict[url]
        url_padding=longest_url-len(url)
        url_padding_str=' '*url_padding
        print('* '+url.lower()+url_padding_str,end=' ')
        for heading in headings:
            value=stats.get(heading,'')
            padding=len(heading)-len(value)
            padding_str=' ' * padding
            print('| '+value+padding_str,end=' ')
        print('')
    print('*' * table_width)
    


if __name__ == '__main__':
    combined_stats = {}
    APPROVED_PROJECT_URLS = []
    weak_stats = [] # projects which we don't have enough stats from to make accurate averages
    # COMBINEDSTATS has format:
#    COMBINED_STATS_EXAMPLE = {
#        'HTTP://PROJECT.COM/PROJECT': {
#            'COMPILED_STATS': {
#                'AVGWALLTIME': 30.01, 'AVGCPUTIME': 10.02, 'TOTALTASKS': 51, 'TOTALWALLTIME': 223311.34,
#                'AVGCREDITPERHOUR': 31.2, 'AVGCREDITPERTASK': 32.12, 'AVGMAGPERHOUR': 32.1, 'TOTALCPUTIME':300010.10},
#            'CREDIT_HISTORY': {
#                '11-29-21': {'CREDITAWARDED':100.54},
#                '11-28-21': {'CREDITAWARDED':100.21},
#            },
#            'WU_HISTORY': {
#                '07-31-2021':{'STARTTIME': '1627765997', 'ESTTIME': '6128.136145', 'CPUTIME': '3621.724000',
#                 'ESTIMATEDFLOPS': '30000000000000', 'TASKNAME': 'wu_sf3_DS-16x271-9_Grp218448of1000000_0',
#                 'WALLTIME': '3643.133927', 'EXITCODE': '0'},
#                '07-29-2021': {'STARTTIME': '1627765996', 'ESTTIME': '6128.136145', 'CPUTIME': '3621.724000',
#                               'ESTIMATEDFLOPS': '30000000000000',
#                               'TASKNAME': 'wu_sf3_DS-16x271-9_Grp218448of1000000_0',
#                               'WALLTIME': '3643.133927', 'EXITCODE': '0'},
#            }
#        },
#    }
    # Define starting parameters
    found_platform=platform.system()
    if not boinc_data_dir:
        if found_platform=='Linux':
            if os.path.isdir('/var/lib/boinc-client'):
                boinc_data_dir='/var/lib/boinc-client'
            else:
                boinc_data_dir=os.path.join(Path.home(), 'BOINC/')
        elif found_platform=='Darwin':
            boinc_data_dir=os.path.join('/Library/Application Support/BOINC Data/')
        else:
            boinc_data_dir = 'C:\ProgramData\BOINC\\'
    if not gridcoin_data_dir:
        if found_platform=='Linux':
            gridcoin_data_dir=os.path.join(Path.home(),'.GridcoinResearch/')
        elif found_platform=='Darwin':
            gridcoin_data_dir = os.path.join(Path.home(), 'Library/Application Support/GridcoinResearch/')
        else:
            gridcoin_data_dir=os.path.join(Path.home(),'AppData\Roaming\GridcoinResearch\\')

    # check that directories exist
    print('Guessing BOINC data dir is ' + str(boinc_data_dir))
    if not os.path.isdir(boinc_data_dir):
        print('BOINC data dir does not appear to exist. If you have it in a non-standard location, please edit the first few lines of this script so we know where to look')
        quit()
    print('Guessing Gridcoin data dir is ' + str(gridcoin_data_dir))
    if not os.path.isdir(gridcoin_data_dir):
        print('Gridcoin data dir does not appear to exist. If you have it in a non-standard location, please edit the first few lines of this script so we know where to look')
        quit()
    total_found_values = 0
    for url, found_value in preferred_projects.items():
        total_found_values+=found_value
    if total_found_values!=100 and len(preferred_projects)>0:
        print('Warning: The weights of your preferred projects do not add up to 100! Quitting.')
        quit()

    # Establish connections to BOINC and Gridcoin clients, get basic info
    boinc_client = None
    grc_client = None
    try:
        boinc_client = BoincClientConnection(config_dir=boinc_data_dir)
    except Exception as e:
        print('Unable to connect to a BOINC client. Are you sure BOINC is running? Error ' + str(e))
        quit()
    gridcoin_conf=None
    try:
        gridcoin_conf = get_config_parameters(gridcoin_data_dir)
    except Exception as e:
        print('Error parsing gridcoin config file in directory: '+gridcoin_data_dir+' Error: '+str(e))
        quit()
    rpc_user = gridcoin_conf.get('rpcuser')
    rpc_password = gridcoin_conf.get('rpcpassword')
    rpc_port = gridcoin_conf.get('rpcport')
    if not rpc_user or not rpc_password or not rpc_port:
        print('Error: Gridcoin wallet is not configured to accept RPC commands based on config file from ' + str(
            gridcoin_data_dir))
        print(
            'RPC commands enable us to talk to the Gridcoin client and get information about project magnitude ratios')
        print('Would you like us to automatically configure your Gridcoin client to accept RPC commands?')
        print('It will be configured to only accept commands from your machine.')
        print('Please answer "Y" or "N" without quotes. Then press the enter key')
        answer = input("")
        while answer not in ['Y', 'N']:
            print('Error: Y or N not entered. Try again please :)')
            answer = input("")
        if answer == "N":
            print('Ok, we won\'t, quitting now')
            quit()
        else:
            with open(os.path.join(gridcoin_data_dir, 'gridcoinresearch.conf'), "a") as myfile:
                from random import choice
                from string import ascii_uppercase
                from string import ascii_lowercase
                from string import digits
                rpc_user = ''.join(choice(ascii_uppercase) for i in range(8))
                rpc_password = ''.join(choice(ascii_uppercase+ascii_lowercase+digits) for i in range(12))
                rpc_port = 9876
                print('Your RPC username is: ' + rpc_user)
                print('Your RPC password is: ' + rpc_password)
                print('You don\'t need to remember these.')
                print('Modifying config file...')
                myfile.write("rpcport=9876\n")
                myfile.write("rpcallowip=127.0.0.1\n")
                myfile.write("server=1\n")
                myfile.write("rpcuser=" + rpc_user + '\n')
                myfile.write("rpcpassword=" + rpc_password + '\n')
            print('Alright, we\'ve modified the config file. Please restart the gridcoin wallet.')
            print('Once it\'s loaded and fully synced, press enter to continue')
            discard_me = input('')

    #check sidestakes
    foundation_address='bc3NA8e8E3EoTL1qhRmeprbjWcmuoZ26A2'
    developer_address='RzUgcntbFm8PeSJpauk6a44qbtu92dpw3K'
    check_sidestake_results = check_sidestake(gridcoin_conf, foundation_address, 1)
    sidestake_check(check_sidestake_results,'FOUNDATION',foundation_address)
    check_sidestake_results = check_sidestake(gridcoin_conf, developer_address, 1)
    sidestake_check(check_sidestake_results, 'DEVELOPER', developer_address)
    print('Welcome to FindTheMag and thank you for trying out this tool. Your feedback and suggestions are welcome on the github page : )')
    print('Looks like you are sidestaking to the foundation, thank you for giving back!')
    check_sidestake_results = check_sidestake(gridcoin_conf, developer_address, 1)
    try:
        grc_client = GridcoinClientConnection(rpc_user=rpc_user,rpc_port=rpc_port,rpc_password=rpc_password)
    except Exception as e:
        print('Unable to connect to Gridcoin wallet. Are you sure it\'s open? Error: ' + str(e))
        quit()
    try:
        APPROVED_PROJECT_URLS = grc_client.get_approved_project_urls()
    except Exception as e:
        print('Error getting project URL list from Gridcoin wallet. Are you sure it\'s open? Error: '+str(e))
        quit()
    try:
        ALL_PROJECT_URLS = (boinc_client.get_project_list())
    except Exception as e:
        print('Error getting project URL list from BOINC '+str(e))

    # make base for COMBINEDSTATS dict
    for url in list(APPROVED_PROJECT_URLS):
        combined_stats[url] = {'COMPILED_STATS': {}, 'CREDIT_HISTORY': {}, 'WU_HISTORY': []}
    print('Gathering project stats...')
    combined_stats = config_files_to_stats(boinc_data_dir)
    print('Calculating project weights...')
    print('Curing some cancer along the way...')
    # Calculate project weights w/ credit/hr
    final_project_weights = {}
    # Uppercase preferred_projects list
    for url in list(preferred_projects.keys()):
        weight=preferred_projects[url]
        del preferred_projects[url]
        preferred_projects[url.upper()] = weight
    ignored_projects = [x.upper() for x in ignored_projects]  # uppercase ignored project url list
    mag_ratios = get_project_mag_ratios(grc_client)
    combined_stats,unapproved_projects = add_mag_to_combined_stats(combined_stats, mag_ratios, APPROVED_PROJECT_URLS,preferred_projects.keys())
    if len(unapproved_projects)>0:
        print('Warning: Projects below were found in your BOINC config but are not on the gridcoin approval list or your preferred projects list. If you want them to be given weight, be sure to add them to your preferred projects')
        pprint.pprint(unapproved_projects)
    most_efficient_projects = get_most_mag_efficient_projects(combined_stats, ignored_projects)
    if len(most_efficient_projects)==0:
        total_preferred_weight=1000-(len(APPROVED_PROJECT_URLS))+len(preferred_projects)
    else:
        total_preferred_weight = (preferred_projects_percent / 100) * 1000
    if len(most_efficient_projects)==0:
        print('No projects have enough completed tasks to determine which is the most efficient. Assigning all projects 1')
        total_mining_weight=0
    else:
        total_mining_weight = 1000 - total_preferred_weight
    total_mining_weight_remaining = total_mining_weight
    # assign weight of 1 to all projects which didn't make the cut
    for project_url in APPROVED_PROJECT_URLS:
        if project_url in preferred_projects:
            continue  # exclude preferred projects
        if project_url in ignored_projects:
            final_project_weights[project_url] = 0
            continue
        if project_url not in APPROVED_PROJECT_URLS:
            continue
        if project_url not in combined_stats:
            #print('Warning: project has no stats, setting project weight to one: ' + project_url.lower())
            final_project_weights[project_url] = 1
            total_mining_weight_remaining -= 1
            weak_stats.append(project_url.lower())
            continue
        total_tasks = int(combined_stats[project_url]['COMPILED_STATS']['TOTALTASKS'])
        if total_tasks < 10:
            #print('Warning: project does not have enough tasks to compute accurate average, setting project weight to one: ' + project_url.lower())
            weak_stats.append(project_url.lower())
        if project_url not in most_efficient_projects or total_tasks < 10:
            final_project_weights[project_url] = 1
            total_mining_weight_remaining -= 1
    if len(most_efficient_projects)>0:
        print('The following projects do not have enough stats to be calculated accurately, assigning them a weight of one: ')
        pprint.pprint(weak_stats)
    # Figure out weight to assign to most efficient projects, assign it
    if len(most_efficient_projects)==0:
        per_efficient_project=0
    else:
        per_efficient_project = total_mining_weight_remaining / len(most_efficient_projects)
    if total_mining_weight_remaining>0:
        print('Assigning ' + str(total_mining_weight_remaining) + ' weight to ' + str(
        len(most_efficient_projects)) + ' mining projects which means ' + str(per_efficient_project) + ' per project ')
    for project_url in most_efficient_projects:
        if project_url not in final_project_weights:
            final_project_weights[project_url]=0
        final_project_weights[project_url] += per_efficient_project
    # Assign weight to preferred projects
    per_preferred_project = total_preferred_weight / len(preferred_projects)
    for project_url,weight in preferred_projects.items():
        if project_url not in final_project_weights:
            final_project_weights[project_url]=0
        intended_weight=(preferred_projects[project_url] / 100) * total_preferred_weight
        final_project_weights[project_url] += intended_weight
    print('')
    print('SOME PRETTY STATS JUST FOR YOU, SORTED BY AVGMAGPERHOUR')
    #generate table to print pretty
    table_dict={}
    for project_url,stats_dict in combined_stats.items():
        table_dict[project_url]={}
        for stat_name,stat_value in stats_dict['COMPILED_STATS'].items():
            rounding=2
            if stat_name=='MAGPERCREDIT':
                rounding=5
            table_dict[project_url][stat_name]=str(round(float(stat_value),rounding))
    print_table(table_dict,sortby='AVGMAGPERHOUR')
    print('Total project weight will be 1000. We will reserve a minimum .01% of processing power for monitoring each project')
    print('Total weight for preferred projects is ' + str(round(float(total_preferred_weight),2)))
    print('Total weight for mining projects is ' + str(round(float(total_mining_weight),2)))
    print('FINAL SUGGESTED PROJECT WEIGHTS')
    for project,weight in final_project_weights.items():
        print(project.lower()+': '+str(weight))
    if check_sidestake_results==True:
        print('~~---***Wow THANK YOU for sidestaking to our development. You rock!***---~~~')
        print('Yeeeehaw! We\'re going to the pony store!')
        print("""
---             ,--,
----      _ ___/ /\|
-----    ;( )__, )
-----   ; //   '--;
----      \     |
---        v    v""")
    else:
        print('If you\'d like to say thank you to the developers of this tool, please help us buy our next round of energy drinks by sending GRC to:')
        print(developer_address)
    print('Press enter key to exit')
    answer = input("")