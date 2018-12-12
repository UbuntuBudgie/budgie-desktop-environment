# WindowShuffler

GUI and keyboard friendly window arranger for the budgie and mate desktop

Demo: https://www.youtube.com/watch?v=Ii4n8H4XEzc

## Description
WindowShuffler is a window placement add-on. Click a window and subsequently click a tile in the grid, the window moves to the corresponding position on the screen. Shift-click two tiles will make the window span the two. Shift-click does not need to be on two tiles next to each other; cross- selection and spanning multiple tiles is possible.
Options include: quick-grid all windows into the current grid, take a snapshot of current layout, reset to snapshot.
The "extension" comes with a list of shortcuts, which can be called by pressing [ i ].

WindowShuffler supports multi-monitor setup. Windows are positioned in the grid -per screen-.

## Set up
- Make sure all of the following dependencies are installed: wmctrl, xdotool, python3-gi-cairo, python3-cairo.
- Copy all icons (all .svg files) to /usr/share/pixmaps
- Store all code files in one and the same diretory
- Run the wrapper `matrix_wrapper` from either a shortcut or a hotcorner. Running the wrapper again toggles the grid.

## Limitations
- Some windows have a fixed size, they cannot be resized.
- Some windows have a minimum size, they cannot be resized below their minimum size.

## Use WindowShuffler without the matrix window
Shuffler can also be used by cli. To use, run `shuffler_nogui` with as arguments the size of the matrix (horizontally, vertically) + the targeted position of the active window in the matrix (where 0 is the first). An example:

`shuffler_nogui 2 2 0 1`

will place the active window in the bottom left cell in a grid of 2 x 2.

