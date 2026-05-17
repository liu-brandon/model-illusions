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
radii = [.7]
omegas = np.arange(-.6, .6, .1)
seeds = range(5)
print(omegas)

processes = []
for depth_cue in depth_cues:
    for r in radii:
        for omega in omegas:
            for seed in seeds:
                file_name = f"depth_{depth_cue}_r_{r}_omega_{omega}_seed_{seed}.mp4"
                out_path = f"{args.output_folder}/{file_name}"
                processes.append(subprocess.Popen(["python", "generate_bistable_cylinder.py", "--rows", str(20), "--K0", str(35), "--height", str(2.0), "--fps", str(args.fps), "--depth_cue", str(depth_cue), "--T", str(args.time), "--radii", str(r), "--omegas", str(omega), "--out", str(out_path), "--resolution", args.resolution, "--seed", str(seed)]))

for p in processes:
    p.wait()