import sys
import os
import logging
import subprocess
import json
from os import listdir
from os.path import isfile, join

try:
    import cliff
except ImportError as e:
    subprocess.check_call("pip install cliff", shell=True)
    import cliff

from cliff.app import App
from cliff.command import Command
from cliff.commandmanager import CommandManager
from distutils.spawn import find_executable


class Tiamat(App):

    def __init__(self):
        super(Tiamat, self).__init__(
            description='cliff-based interactive command line interface',
            version='0.1',
            command_manager=CommandManager("Tiamat"),
            deferred_help=True,
        )
        commands = {
            'deploy': Deploy,
            'destroy': Destroy,
            'ansible': Ansible,
            'get elk files': ElkFiles,
            'elk': Elk,
            'show active servers': ShowActive,
            'show deployment list': ShowServers,
            'add server': AddServers,
            'remove server': RemoveServers
        }
        for k, v in commands.iteritems():
            self.command_manager.add_command(k, v)

        self.command_manager.add_command('complete', cliff.complete.CompleteCommand)

        # os platform check
        global os_platform
        if sys.platform.startswith('linux'):
            os_platform = "Linux"
        elif sys.platform.startswith('darwin'):
            os_platform = "OS X"
        elif sys.platform.startswith('win32') or sys.platform.startswith('cygwin'):
            os_platform = "Windows"

        # start dependencies check
        if "AWS_ACCESS_KEY_ID" not in os.environ:
            print "Error: environment variable AWS_ACCESS_KEY_ID is missing."
            exit(1)

        if "AWS_SECRET_ACCESS_KEY" not in os.environ:
            print "Error: environment variable AWS_SECRET_ACCESS_KEY is missing."
            exit(1)

        if "AWS_DEFAULT_REGION" not in os.environ:
            print "Error: environment variable AWS_DEFAULT_REGION is missing."
            exit(1)

        if not find_executable('terraform'):
            ans = raw_input("Error: Terraform is not installed or missing in search path.\n \
            Do you want to install it via Tiamat? y/n ")

            if ans == 'y' or ans == 'yes':
                is_64bits = sys.maxsize > 2 ** 32
                local_path = raw_input("Please input full local file directory --> ")
                local_file_path = local_path + '/terraform.zip'

                if os_platform == "Linux":
                    if is_64bits:
                        url = "https://releases.hashicorp.com/terraform/0.9.8/terraform_0.9.8_" + \
                            "linux_amd64.zip?_ga=2.142026481.2126347023.1497377866-658368258.1496936210"
                    else:
                        url = "https://releases.hashicorp.com/terraform/0.9.8/terraform_0.9.8_" + \
                            "linux_386.zip?_ga=2.137897971.2126347023.1497377866-658368258.1496936210"
                    wget_call = "wget " + url + " -O " + local_file_path
                    subprocess.check_call(wget_call, shell=True)  # check this command
                    unzip_call = "unzip " + local_file_path + " -d " + local_path
                    subprocess.check_call(unzip_call, shell=True)

                elif os_platform == "OS X":
                    url = "https://releases.hashicorp.com/terraform/0.9.8/terraform_0.9.8" + \
                        "_darwin_amd64.zip?_ga=2.76410710.2126347023.1497377866-658368258.1496936210"
                    curl_call = "curl " + url + " -o " + local_file_path
                    subprocess.check_call(curl_call, shell=True)
                    unzip_call = "unzip " + local_file_path + "-d " + local_path
                    subprocess.check_call(unzip_call, shell=True)  # can use -d to assign exp dir

                elif os_platform == "Windows":
                    if is_64bits:
                        url = "https://releases.hashicorp.com/terraform/0.9.8/terraform_0.9.8_" + \
                            "windows_amd64.zip?_ga=2.176148193.2126347023.1497377866-658368258.1496936210"
                    else:
                        url = "https://releases.hashicorp.com/terraform/0.9.8/terraform_0.9.8_" + \
                            "windows_386.zip?_ga=2.176148193.2126347023.1497377866-658368258.1496936210"
                    wget_call = "wget " + url + " -O " + local_path
                    subprocess.check_call(wget_call, shell=True)  # check this command
                    subprocess.check_call("unzip " + local_path, shell=True)  # check this command

                else:
                    print "Error: cannot check OS.Please download Terraform manually."
                    url = ""
                    exit(1)

            else:
                exit(1)
        else:
            pass
            # print find_executable('terraform')

    def initialize_app(self, argv):
            self.LOG.debug('initialize_app')

    def prepare_to_run_command(self, cmd):
            self.LOG.debug('prepare_to_run_command %s', cmd.__class__.__name__)

    def clean_up(self, cmd, result, err):
            self.LOG.debug('clean_up %s', cmd.__class__.__name__)
            if err:
                self.LOG.debug('got an error: %s', err)


def main(argv=sys.argv[1:]):
    shell = Tiamat()
    return shell.run(argv)


class Deploy(Command):
    """Apply the environment configuration"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(Deploy, self).get_parser(prog_name)
        parser.add_argument('--config_name', default='test')
        parser.add_argument('--caps', action='store_true')
        return parser

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        output = 'start deploying environment ' + parsed_args.config_name + '\n'
        if parsed_args.caps:
            output = output.upper()
        self.app.stdout.write(output)

        global is_deployed
        global deploy_server_list
        if not is_deployed:
            try:
                subprocess.check_call("terraform plan -detailed-exitcode", shell=True)
            except subprocess.CalledProcessError:
                print "\nError predicted by terraform plan. Please check the configuration before deployment."
                ans = raw_input("Do you want to deploy anyway? y/n ")
                if ans != 'y' and ans != 'yes':
                    return

            p = subprocess.Popen("terraform apply", shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
            result = ""
            while True:
                output = p.stdout.readline()
                result += output
                if output == '' and p.poll() is not None:
                    break
                if output:
                    print output.strip()

            if p.returncode != 0:
                print "\nError: terraform exited abnormally. Return code is %s.\n" % p.returncode
                print p.stderr.read()
                print "Immediate destroy is suggested.\n"
                subprocess.call("terraform destroy", shell=True)
                return

            # parse ansible ip
            ansible_ip_beg = result.find("ansible ip") + 13
            ansible_ip_end = result.find("\n", ansible_ip_beg)
            global state
            state.ip["ansible"] = result[ansible_ip_beg:ansible_ip_end]

            # parse elk ip
            if 'elk' in deploy_server_list:
                elk_ip_beg = result.find("elk ip") + 9
                elk_ip_end = result.find("\n", elk_ip_beg)
                state.ip["elk"] = result[elk_ip_beg:elk_ip_end]

            is_deployed = True

            state.active_server_list = deploy_server_list
            state.active_server_list.append('ansible')

            with open("global_state.json", "w") as global_state:
                json.dump(state, global_state)
            global_state.close()
        else:
            self.app.stdout.write("Error: environment already deployed.\n")


class Destroy(Command):
    """Destroy the applied environment"""
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        self.app.stdout.write('start destroying environment...\n')
        subprocess.call("terraform destroy", shell=True)
        global is_deployed
        global state
        is_deployed = False
        state.ip.clear()
        state.active_server_list = []
        if isfile('global_state.json'):
            os.remove('global_state.json')


class Ansible(Command):
    """Open a nested Ansible shell"""
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global state
        if "ansible" not in state.ip.keys():
            self.app.stdout.write("Error: Ansible IP unavailable.\n")
            return

        ssh_call = "ssh -i key ubuntu@" + state.ip["ansible"]
        subprocess.check_call(ssh_call, shell=True)


class ElkFiles(Command):
    """Copy log files from ELK server to local folder"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(ElkFiles, self).get_parser(prog_name)
        parser.add_argument('local_path')
        return parser

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global state
        global elk_logs_path
        if "elk" not in state.ip.keys():
            self.app.stdout.write("Error: ELK IP unavailable.\n")
            return

        scp_call = "scp -i key -r ubuntu@" + state.ip["elk"] + ':' + elk_logs_path + ' ' + parsed_args.local_path
        subprocess.check_call(scp_call, shell=True)


class Elk(Command):
    """open the Elk Dashboard in user's default browser"""
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global state
        if "elk" not in state.ip.keys():
            self.app.stdout.write("Error: ELK IP unavailable.\n")
            return

        global os_platform
        if os_platform == "Linux":
            browser_call = "xdg-open " + 'http://' + state.ip["elk"]
        elif os_platform == "OS X":
            browser_call = "open " + 'http://' + state.ip["elk"]
        elif os_platform == "Windows":
            browser_call = "explorer " + 'http://' + state.ip["elk"]

        subprocess.check_call(browser_call, shell=True)


class ShowActive(Command):
    """show the list of active servers"""
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global state
        for server in state.active_server_list:
            print server


class AddServers(Command):
    """add a server to deployment list"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(AddServers, self).get_parser(prog_name)
        parser.add_argument('server_name')
        return parser

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global deploy_server_list
        if parsed_args.server_name not in deploy_server_list:
            config_file_path = "overrides/" + parsed_args.server_name + "_override.tf"
            if not isfile(config_file_path):
                print "Error: no config file for this server."
                return

            cp_call = "cp " + config_file_path + " ."
            subprocess.check_call(cp_call, shell=True)
            deploy_server_list.append(parsed_args.server_name)


class RemoveServers(Command):
    """remove a server from deployment list"""
    log = logging.getLogger(__name__)

    def get_parser(self, prog_name):
        parser = super(RemoveServers, self).get_parser(prog_name)
        parser.add_argument('server_name')
        return parser

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global deploy_server_list
        if parsed_args.server_name in deploy_server_list:
            rm_call = "rm " + parsed_args.server_name + "_override.tf"
            subprocess.call(rm_call, shell=True)
            deploy_server_list.remove(parsed_args.server_name)


class ShowServers(Command):
    """show the list of servers to be deployed"""
    log = logging.getLogger(__name__)

    def take_action(self, parsed_args):
        self.log.debug('debugging')
        global deploy_server_list
        for server in deploy_server_list:
            print server


class GlobalState:
    def __init__(self):
        self.active_server_list = []
        self.ip = {}


if __name__ == '__main__':
    # global state variables
    full_server_list = ["blackhat", "contractor", "elk", "ftp",
                        "mail", "payments", "wazuh"]

    if isfile("global_state.json"):
        is_deployed = True
        with open("global_state.json", "r") as global_state:
            state = json.load(global_state)

    else:
        is_deployed = False
        state = GlobalState()

    deploy_server_list = [f.split('_')[0] for f in listdir('.') if isfile(f) and f[-2:] == 'tf']

    try:
        deploy_server_list.remove('configuration.tf')
    except ValueError:
        pass

    elk_logs_path = ""
    os_platform = ""

    sys.exit(main(sys.argv[1:]))
