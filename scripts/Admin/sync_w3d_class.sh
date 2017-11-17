#!/bin/bash
RCLONE="/home/cavedemo/W3DClassSync/rclone_bin/rclone --delete-after"

LOCAL_PRE="/share/cavewriting/classes/w3d2017fall"

if [$1]
    drive_names="$1"
else
    drive_names=("Blake" "Charles" "Dani" "Griffin" "Jack" "Liesl" "Lucas" "Meredith" "Michael" "Olivia" "Sally" "Scott" "Theadora" "Tim" "Zhean")
fi

#local_names=("hequet" "perez" "solayappan" "shin" "douglas" "han" "francois" "tachihara" "giannazzo" "bayer" "burke" "swanson" "vann" "dingsun" "ziebell")

for i in "${!drive_names[@]}"; do
    $RCLONE sync "W3D:w3d2017Fall_Shared/${drive_names[$i]}/kioskButton" "$LOCAL_PRE/${drive_names[$i]}"
    python3 /home/cavedemo/remove_double.py -rv "/share/cavewriting/classes/w3d2017fall/${drive_names[$i]}"
done

$RCLONE copy W3D:w3d2017Fall_Shared/Fonts /share/cavewriting/CW2/fonts
