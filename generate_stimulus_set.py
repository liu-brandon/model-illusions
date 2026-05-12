import numpy as np
import subprocess

depth_cues = [0, .7]
radii = [1.5]
omegas = np.arange(-1.0, 1.0, .2)
print(omegas)

processes = []
for depth_cue in depth_cues:
    for r in radii:
        for omega in omegas:
            file_name = f"depth_{depth_cue}_r_{r}_omega_{omega}.mp4"
            out_path = f"stimulus/{file_name}"
            processes.append(subprocess.Popen(["python", "run.py", "--depth_cue", str(depth_cue), "--T", str(10), "--radii", str(r), "--omegas", str(omega), "--out", str(out_path)]))

for p in processes:
    p.wait()