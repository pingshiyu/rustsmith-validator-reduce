# loop over files in `m0` directory to see what's changed in `m197`

from pathlib import Path
import filecmp

m0_folder = Path("mir_dump_m0")
m197_folder = Path("mir_dump_m197")

mir_files = [mir_file.name for mir_file in m0_folder.glob("*.mir")]
matches, mismatches, erors = filecmp.cmpfiles(m0_folder, m197_folder, common=mir_files)
print("mismatches:", mismatches)