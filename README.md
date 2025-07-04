Create new PlayStation 2 PSS files with this documentation and python script. (Other tools required)

This release contains a tool to generate compatible MPEG-2 videos for PS2 games that use field-stacking
to achieve 50/60hz video.

How does it work?
Some PS2 games have pre-rendered videos (usually opening / intro cinematics) that run at 50/60hz.
However, in cases such as the Gran Turismo games the videos themselves are actually not interlaced 50/60hz.
Instead they are progressive at half fps, with each frame containing 2 fields stacked on top of each other.

<p align="center">
  <img width="640" height="360" src="https://github.com/Silentwarior112/GT4-pat-editor/blob/main/pink%20vitz.png">
</p>

In these cases the game is responsible for weaving the fields together by scanning the top and bottom half.

This becomes troublesome when trying to create a custom video for these intro cinematics, since
there isn't a commonly available solution to render a video in this manner.

The python script is a serviceable solution. It will take any interlaced video and re-encode it
into a progressive video with the fields unwoven and stacked the same way original ones were.
