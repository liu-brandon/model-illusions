import numpy as np
import subprocess
import argparse

parser = argparse.ArgumentParser()
parser.add_argument("--output_folder",          type=str, default="stimulus",               help="Output folder")
parser.add_argument("--fps",                    type=int, default=30,                       help="frames per second")
parser.add_argument("--time",                   type=float, default=10.0,                   help="video length in seconds")
parser.add_argument("--resolution",             type=str, default="512x512",                help="video resolution in pixels")

args = parser.parse_args()

depth_cues = [0, .7]
radii = [1.5]
omegas = np.arange(-.6, .6, .3)
print(omegas)

processes = []
for depth_cue in depth_cues:
    for r in radii:
        for omega in omegas:
            file_name = f"depth_{depth_cue}_r_{r}_omega_{omega}.mp4"
            out_path = f"{args.output_folder}/{file_name}"
            processes.append(subprocess.Popen(["python", "generate_bistable_cylinder.py", "--fps", str(args.fps), "--depth_cue", str(depth_cue), "--T", str(args.time), "--radii", str(r), "--omegas", str(omega), "--out", str(out_path), "--resolution", args.resolution]))

for p in processes:
    p.wait()