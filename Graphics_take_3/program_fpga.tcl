open_hw_manager

connect_hw_server -allow_non_jtag

open_hw_target

current_hw_device [get_hw_devices xc7z020_1]

set_property PROGRAM.FILE [lindex $argv 0] [get_hw_devices xc7z020_1]

program_hw_devices [get_hw_devices xc7z020_1]

refresh_hw_device -update_hw_probes false [lindex [get_hw_devices xc7z020_1] 0]
