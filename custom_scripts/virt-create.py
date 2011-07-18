#!/usr/bin/env python
import os, sys, urllib2, string, subprocess, imp


class VMInstance:
    def __init__(self, config_file, template_file):
        """
        VMInstance object constructor.
        Gets config_file and template_file as its input. Returns VMInstance object with all params necessary for provisioning.
        """
        config = imp.new_module('config')
        imp.load_source('config', config_file)
        import config
        self.name = config.vmname
        self.arch = config.arch
        self.ram = config.memory
        self.cpunum = config.vcpus
        self.hddsize = config.hda_disk_size/1024
        self.kickstart_file = "%s_ks" %self.name
        self.kickstart_image = "%s.img" % self.kickstart_file
        self.image_name = config.image_path
        self.network_configurator(config.networking)
        self.mirror = config.mirror+'/%s'%self.arch
        self.make_mirror_lines()
        self.make_repo_lines(config.repo_list)
        self.generate_encrypted_rootpw(config.rootpw)
        self.make_root_keys_lines(['ssh-dss AAAAB3NzaC1kc3MAAACBAOokUZ2brsQH76mdb7/MP1ar9lNc15TMA6Hfi9VCUoBxrfnfnac9DKAsNmLjBeeS1DqeTcVx8M2M9xEjKL3DO6nbhbkLUg1t3pnJmPNsw9Et7KpWR3DxGB7PWqGbHmkir71KFMnC2euDZGzlw2d/t6Mj53zxuxx7IHFgGLfAYqQ3AAAAFQD1oYeoFPWlDHuHp2MNt8mV2rgnUQAAAIAkIxaJk1vHZOZ9NaGdysePWxsAYQ1tqzkHzjDckg3M+905jDF6HAyD5RybEYxSx7JR3jE+dWHKSC9k1y6yYMPFC1CE/UN87vRLAeiGp0xDhSufj8+gCIpl13xl4R2TrjJsTlk0YQdmLwFvBTvYz6vPBnr5OlhmmI4LlGbZH/wl/QAAAIBnD9kH/YM0ShgrBaElWrWzb66RPTP/KAdjpnuaYIb6JQ9r638ofdziOlHN4csnlirQE5w+3V6peV4aNgUBOxbruZatSI9O0AwhOqjsQTFeZfLBKs/yLqCvVz8CzxzV+dmo/WijUPI12wMGo+HeDKZzWutg3Yx+9sTVZtJFuKcz7A== s_hanzhin NEW', 'ssh-dss AAAAB3NzaC1kc3MAAACBAN1DkueBAp+kj0U7eQfSBrDJ5njz1V2LjhOdUIP0K9lByPwdBgW9UbiRjeIIzTBH6NsN18I/XDCXBdPAQexlh8cZRIA+SJKh6pXLgzS7+/abBNQSfXLnfjzt44G4I8SKPd60RICScsiOt12UV6PdyGaT1TVpe/Ba2ZQPUKQWADMbAAAAFQD5FZcnLaarwBZOUm1T31AK/QEeEwAAAIEAwavEGeMcqRlkHGN/ziUg/7qIaLhSyHWJxsos4lQ510l9QikBOR3YtRH/imcSGU16sj5B1lJfMBZV/FShcInt40VrJU4h4/t9cH7KZfjjr359gSr1WyzHd0r6WkTxDP06U6RuNtGJethadfQjaNofgz85dGS2iVbR5pNdNpFk//MAAACATDmuVsqWJg2gurtGe3dJ2oeyJWmqS6wUv4s53h5NA4KedRWtJ5L/KBXt4M/SFktM7zijsexVRdt3Y0CdmXO5IlChGwvIaA3uSlV4FdHqiGJFzmU+nJuqyTv7sZhZJ7cnOkcHEtw4pRxknrDK0PfbGqVjBOyY+qMqEb5RnLqpETw= a.sergeev@creatstudio.com', 'ssh-dss AAAAB3NzaC1kc3MAAACBANOxkvltuYBNxCyrZ9xWfXu4rlw+N2a27/+PRxleC315RDuJ2S77qLOCzWsndyBD9BQIpv2f4kDp0PO7kFgh6xgDZmRpRm8hcaMvOE5uSYZcB/d9DwYzI0oWyUEnCtVqB3r/CG4euo0/De7L9VLeBcHQjK0ter6beiQZfbkfSKxJAAAAFQDdsuIMOnntvDAdutUWukMTT2EfvQAAAIB6Emv6FF0TqmQCOPQG0RYrJ8yiF4wR2lwkCoN8Z9I5+7Re7FKbAGJr76eYojB/6eO7EASPN2anhLUkAcxb9xHveBsojwDygQJxUYqg/x3UozfQwS+QouTfLJ8rVIi5EAP6C/utOXl8jAy/sO6QWJv8q59tdec3fjeB187dJ6DCAgAAAIB2pyZamQZ81bQuNkm1n7JIowpPUMEqBgHUeM4kMwcjLU3N2Xsn3AkAn7RjrqI460yNyNDmmg9cHXR6s+FYJWJ6RVJ9ihg5CRNuDnHgPxyfu1z9BodU1nCHQT2oLRqMmQsOg42BejIZsq66dJtJoqc2hKW8aETCLlWc3HQkPGR4wg== emilovanov@suselinux'])
        self.packages_lines = string.join(config.add_packages,"\n")
        self.postinstall_lines = string.join(config.postinstall_commands, "\n")
        template = open(template_file, 'r')
        kickstart_template = string.Template(template.read())
        print "Creating Contents"
        self.create_kickstart_contents(kickstart_template)
        kickstart = open(self.kickstart_file, 'wb')
        kickstart.writelines(self.kickstart_contents)
        kickstart.close()
        self.create_kickstart_image()
        self.create_virtinstall_command()



    def make_root_keys_lines(self, ssh_root_keys):
        self.root_keys_lines = ''
        for key in ssh_root_keys:
            self.root_keys_lines += 'echo "%s" >> /root/.ssh/authorized_keys\n' % key

    def network_configurator(self, networking):
        """
        If our list is just created, we add the hostname to the first network definition
        """
        self.network_lines=''
        self.network_lines_commandline = ''
        self.network_line_kickstart = ''
        count = 0
        for network in networking:
            done = False
            self.network_lines_commandline += "-b %s " % (network[0])
            network[0] = "eth%s"%count
            if not len(self.network_lines):
                network += self.name,
                self.network_line_kickstart = "ksdevice=%s ip=%s netmask=%s gateway=%s" % tuple(network[:4])
                if len(network) == 4:
                    self.network_lines += "network --device=%s --bootproto=static --ip=%s --netmask=%s --hostname=%s\n" % tuple(network)
                    done = True
                elif len(network) == 5:
                    self.network_lines += "network --device=%s --bootproto=static --ip=%s --netmask=%s --gateway=%s --hostname=%s\n" % tuple(network)
            if len(network) == 3:
                self.network_lines += "network --device=%s --bootproto=static --ip=%s --netmask=%s\n" % tuple(network)
            elif len(network) == 4 and not done:
                self.network_lines += "network --device=%s --bootproto=static --ip=%s --netmask=%s --gateway=%s\n" % tuple(network)

    def it_is_repo(self, repo):
        """
        it_is_repo() checks whether repository metadata is available for download. If not (urllib2 Exception is raised),
         returns False
        """
        try:
            urllib2.urlopen(repo+'/repodata/repomd.xml')
        except urllib2.HTTPError:
            result = False
            pass
        else:
            result = True
        return result

    def make_mirror_lines(self):
        """
        Checks if it_is_repo and makes mirror strings for kickstart and commandline usage.
        """
        if self.it_is_repo(repo = self.mirror):
            self.mirror_line_commandline = self.mirror
            self.mirror_line = "url --url %s" % self.mirror
        else:
            self.mirror_line_commandline = ''
            self.mirror_line = ''
            raise Exception("Mirror %s unreachable. Will not install." % self.mirror)

    def make_repo_lines(self, custom_repos):
        """
        Make lines to define custom repositories in kickstart files.
        """
        self.repo_lines = ''
        if type(custom_repos) == type(self.repo_lines):
            for repo in custom_repos:
                if self.it_is_repo(repo = repo[1]):
                    self.repo_lines += 'repo --name %s --baseurl=%s\n' % repo
        elif type(custom_repos) == type(()):
            if self.it_is_repo(repo = custom_repos[1]):
                self.repo_lines += 'repo --name %s --baseurl=%s\n' % custom_repos
        else:
            self.repo_lines = ''

    def generate_encrypted_rootpw(self, root_pw):
        p = subprocess.Popen(['openssl','passwd','-1', root_pw], stdout=subprocess.PIPE)
        self.root_pw_enc, error = p.communicate()
        self.root_pw_enc = "rootpw --iscrypted %s" % self.root_pw_enc.strip()
        
    def create_virtinstall_command(self):
        """
        Generate command line for creating virtual machine instance.
        """
        self.kickstart_file = os.path.basename(self.kickstart_file)
        cmd_template = string.Template(
            "virt-install -n $name -r $ram --arch=$arch --vcpus=$cpunum --os-type=linux --os-variant=rhel5.4 -v -l $mirror --disk path=$image_name,size=$hddsize,bus=virtio --disk path=$kickstart_image $network_lines_commandline -x \"ks=hd:vdb:/$kickstart_file serial text $network_line_kickstart\" --accelerate --vnc")
        self.commandline = cmd_template.substitute(self.__dict__)
        print self.commandline

    def create_kickstart_contents(self, template):
        self.kickstart_contents = template.safe_substitute(self.__dict__)
        print self.kickstart_contents

    def create_kickstart_image(self):
        """
        Kickstart image file generator.
        Takes VMInstance and makes 1440 bytes IMG for kickstarting installation procedure
        """
        scriptlet = '#!/bin/bash\nif [ $USER == root ]; then\nKSIMAGE=%s\nif [ -f $KSIMAGE ]; then rm -f $KSIMAGE; fi\nmkfs.msdos -C $KSIMAGE 1440\nmkdir -p ./temp\nmount -o loop $KSIMAGE ./temp\ncp %s ./temp\numount ./temp\nrm -rf ./temp\nelse\necho "Only root can generate Kickstart image. Please, provide a pre-generated image."\nexit 1\nfi' % (self.kickstart_image, self.kickstart_file)
        scriptlet_filename = "%s.scriptlet" % self.name
        scriptlet_file = open(scriptlet_filename, 'wb')
        scriptlet_file.writelines(scriptlet)
        scriptlet_file.close()
        retcode = os.system('/bin/bash %s' % scriptlet_filename)
        if retcode:
            print 'Something went wrong with kickstart'
            raise Exception('Kickstart image generation exception: scriptlet returned code %s' % retcode)

config_file = ''
template_file = ''
if len(sys.argv) == 1:
    print 'Usage: virt-create.py <config_file>'
    sys.exit(1)
elif os.path.exists(sys.argv[1]) and os.path.exists(sys.argv[2]):
    config_file = sys.argv[1]
    template_file = sys.argv[2]
else:
    print 'Config file %s or ks template %s not found'%(sys.argv[1], sys.argv[2])
    exit(1)

VM = VMInstance(config_file, template_file)
print 'Executing %s :' % VM.commandline
retcode = os.system(VM.commandline)
sys.exit(retcode)
