# GDRender

Inspired by this Geometry Dash level by Spu7nix: https://www.youtube.com/watch?v=UKqMBAxxun8

## Concept
I wanted to expand the concept of building animations in a level through an algorithm, so I decided that the next reasonable step would be to place an entire 3D animation into the game.
The level above mostly used the approach of switching between individual frames combined with clever 2D movement, which works for short animations, but cannot be scaled up far due to the game's limitations. Instead, this method reuses the same set of objects for the entire level, moving around to match the animation. This has never been done before, mostly because the only options for moving groups of objects in the game are to move in a straight line and to rotate around other, individual objects. There is also a hard limit of 999 individual groups, so any more than that cannot be moved at all without messing with other objects.

## How it works
Using blender and a modified rendering script, it creates an SVG file for every frame that contains the shapes in the animation transformed into 2D. The program then analyzes the shapes and computes how to best move the game objects to match the animation with smooth motion in between the frames. The objects and motions are converted into the format of the save file for the level editor, which can then be tested and uploaded to the Geometry Dash servers.
