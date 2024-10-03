import sys
import argparse

from moviepy.video.io.VideoFileClip import VideoFileClip
import ffmpeg
from PySide6.QtCore import Qt
import moviepy.Clip

parser = argparse.ArgumentParser(
    prog="Python Video Editor",
    description="Simple Video Clip/Quality/Resolution Editor"
)

parser.add_argument("-i", "--input")
parser.add_argument('-o', "--output")
parser.add_argument("-cb", "--clipbegin")
parser.add_argument("-ce", "--clipend")
parser.add_argument("-rw", "--resolutionw")
parser.add_argument("-rh", "--resolutionh")
parser.add_argument("-b", "--bitrate")
parser.add_argument("-v", "--volume")

args = parser.parse_args()


def main():
    if args.input == None or args.output == None:
        print("No input/output file selected. Please input a filename to be edited.")
        return

    video = VideoFileClip(args.input).subclip(args.clipbegin, args.clipend)
    if args.volume == True:
        video.fx(vfx.volumex, args.volume)
    if args.resolutionw == None or args.resolution == None:
        args.resolutionw, args.resolutionh = video.size
    video.write_videofile(args.output, codec="libx264", audio_codec="aac", target_resolution=(args.resolutionw, args.resolutionh), bitrate=args.bitrate, )
    


if __name__ == "__main__":
    main()
