#!/bin/bash

# parse the command line parameters
while getopts i:s:p:x:l:c: o
do case "$o" in
        x)      vm_config="$OPTARG";;
        p)      param_file="$OPTARG";;
        s)      store="$OPTARG";;
        i)      image_name="$OPTARG";;
        c)      image_conf="$OPTARG";;
        l)      log_file="$OPTARG";;
        esac
done

common_loc="$store"/common
image_root="$store"/"$image_name"
custom_loc="$store"/custom_scripts
image_custom_loc="$store"/"$image_name"/custom_scripts

# source common files
source "$common_loc"/defs
source "$common_loc"/functions

log_msg "$0 starting"
log_msg "vm_config" $vm_config
log_msg "param_file" $param_file
log_msg "store" $store
log_msg "image_name" $image_name
log_msg "image_conf" $image_conf
log_msg "log_file"  $log_file


# source the image store specific file 
# some variables would get overwritten by vm config or params by user
# down the line
if [ -f "$image_conf" ]; then
   source_python_config "$image_conf"
fi

log_msg "custom_list" $custom_list

# source the vm config variables 
source_python_config "$vm_config"

# source additional params passed by UI
source "$param_file"

# WARNING! WARNING! WARNING! RACE CONDITION HERE!!! DANGER!!!
TEMP_CONFIG_FILE=$( $MKTEMP )
KS_TEMPLATE="$image_custom_loc/ks.template"

log_msg "temporary configuration file is $TEMP_CONFIG_FILE"

echo ""
echo "image_path = '$VM_DISKS_DIR/${name}.disk.xm'" >> $TEMP_CONFIG_FILE
echo "vmname = '${name}'" >> $TEMP_CONFIG_FILE
echo "arch = '${arch}'" >> $TEMP_CONFIG_FILE
echo "vcpus = '${vcpus}'" >> $TEMP_CONFIG_FILE
echo "memory = ${memory}" >> $TEMP_CONFIG_FILE
echo "mirror = '${mirror}'" >> $TEMP_CONFIG_FILE
echo "repo_list = `echo -n ${custom_repos}| sed -e 's/, /\", \"/g' -e 's/)/\")/g' -e 's/(/(\"/g'`" >> $TEMP_CONFIG_FILE
echo "hda_disk_size = ${hda_disk_size}" >> $TEMP_CONFIG_FILE
echo "networking = `echo -n \[${netlist}\] | sed -e 's/(/[\"/g' -e 's/)/\"]/g' -e 's/\([0-9]\), /\1\", \"/g'`" >> $TEMP_CONFIG_FILE
echo "routes = '${routes}'" >> $TEMP_CONFIG_FILE
echo "add_packages = ${add_packages}" >> $TEMP_CONFIG_FILE
# echo "ssh_root_keys = ${ssh_root_keys}" >> $TEMP_CONFIG_FILE
echo "rootpw = '${rootpw}'" >> $TEMP_CONFIG_FILE
echo "postinstall_commands = '${postinstall_commands}'" >> $TEMP_CONFIG_FILE
echo ""

log_msg "executing virt-create.py script: python virt-create.py \"$TEMP_CONFIG_FILE\""
VCPY_OUTPUT=$( python $image_custom_loc/virt-create.py "$TEMP_CONFIG_FILE" "$KS_TEMPLATE" 2>&1 )
VCPY_RC=$?
log_msg "virt-create.py script returned output $VCPY_RC: $VCPY_OUTPUT"

if [ $VCPY_RC -ne 0 ]
then
  log_msg "virt-create.py failed, giving up"
  exit $VCPY_RC
fi

rm "$TEMP_CONFIG_FILE"

log_msg "$0 completed."

