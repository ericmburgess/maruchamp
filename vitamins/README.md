# The `vitamins` package

This package contains classes to represent what's going on in the game, such as 
`Car`, `Ball`, `Field`, as well as more abstract classes like `Location`, `Line`,
plus some routines for math, geometry, and drawing on the screen.

The classes for making a bot that actually plays the game are in the `ramen` package.

The intention is that nothing in `ramen` or `vitamins` should need to be modified,
instead your code can import and use these assets. Of course there's nothing to 
stop you from improving them (and submitting a pull request, thanks!).
